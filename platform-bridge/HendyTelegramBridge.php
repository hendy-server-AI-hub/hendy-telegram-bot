<?php

declare(strict_types=1);

/**
 * Narrow, read-only API adapter for the existing Hendy PHP application.
 * Bind providers to existing domain services; never expose raw database rows.
 */
final class HendyTelegramBridge
{
    private const RESOURCES = ['status', 'jobs', 'orders', 'metrics'];
    private const RATE_WINDOW_SECONDS = 60;
    private const RATE_MAX_REQUESTS = 30;

    /**
     * @param array<string, callable(): array<string, mixed>> $providers
     */
    public static function dispatch(
        string $resource,
        string $expectedToken,
        array $providers
    ): never {
        self::jsonHeaders();

        if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
            self::respond(405, ['ok' => false, 'error' => 'method_not_allowed']);
        }
        if (!in_array($resource, self::RESOURCES, true)) {
            self::respond(404, ['ok' => false, 'error' => 'not_found']);
        }
        if ($expectedToken === '') {
            self::respond(503, ['ok' => false, 'error' => 'bridge_not_configured']);
        }

        $authorization = self::authorizationHeader();
        $providedToken = str_starts_with($authorization, 'Bearer ')
            ? substr($authorization, 7)
            : '';
        if ($providedToken === '' || !hash_equals($expectedToken, $providedToken)) {
            self::respond(401, ['ok' => false, 'error' => 'unauthorized']);
        }
        if (!self::allowRate()) {
            self::respond(429, ['ok' => false, 'error' => 'rate_limited']);
        }

        try {
            if ($resource === 'status' && !isset($providers['status'])) {
                self::respond(200, [
                    'ok' => true,
                    'app' => 'hendy-platform',
                    'bridge' => 'ready',
                    'php' => PHP_VERSION,
                ]);
            }

            $provider = $providers[$resource] ?? null;
            if (!is_callable($provider)) {
                self::respond(503, [
                    'ok' => false,
                    'error' => 'resource_provider_not_configured',
                    'resource' => $resource,
                ]);
            }

            $payload = $provider();
            if (!is_array($payload)) {
                self::respond(500, ['ok' => false, 'error' => 'invalid_provider_response']);
            }
            self::respond(200, ['ok' => true] + $payload);
        } catch (Throwable $error) {
            error_log(sprintf(
                'Hendy Telegram bridge failure request_id=%s resource=%s type=%s',
                $_SERVER['HTTP_X_REQUEST_ID'] ?? 'not-set',
                $resource,
                get_class($error)
            ));
            self::respond(500, ['ok' => false, 'error' => 'internal_error']);
        }
    }

    private static function allowRate(): bool
    {
        $ip = (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown');
        $key = hash('sha256', $ip . '|' . (string)($_SERVER['HTTP_AUTHORIZATION'] ?? ''));
        $path = sys_get_temp_dir() . '/hendy-tg-bridge-' . $key . '.json';
        $handle = @fopen($path, 'c+');
        if ($handle === false || !flock($handle, LOCK_EX)) {
            if (is_resource($handle)) {
                fclose($handle);
            }
            return false;
        }

        try {
            rewind($handle);
            $raw = stream_get_contents($handle);
            $state = is_string($raw) ? json_decode($raw, true) : null;
            $now = time();
            if (!is_array($state) || ($state['window'] ?? 0) + self::RATE_WINDOW_SECONDS <= $now) {
                $state = ['window' => $now, 'count' => 0];
            }
            if (($state['count'] ?? 0) >= self::RATE_MAX_REQUESTS) {
                return false;
            }
            $state['count']++;
            rewind($handle);
            ftruncate($handle, 0);
            fwrite($handle, json_encode($state, JSON_THROW_ON_ERROR));
            fflush($handle);
            return true;
        } catch (Throwable) {
            return false;
        } finally {
            flock($handle, LOCK_UN);
            fclose($handle);
        }
    }

    private static function authorizationHeader(): string
    {
        $header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        if ($header === '' && function_exists('getallheaders')) {
            $headers = getallheaders();
            $header = is_array($headers) ? (string)($headers['Authorization'] ?? '') : '';
        }
        return trim($header);
    }

    private static function jsonHeaders(): void
    {
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store, private');
        header('X-Content-Type-Options: nosniff');
        header('Vary: Authorization');
    }

    /** @param array<string, mixed> $payload */
    private static function respond(int $status, array $payload): never
    {
        http_response_code($status);
        try {
            echo json_encode(
                $payload,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
            );
        } catch (JsonException) {
            http_response_code(500);
            echo '{"ok":false,"error":"serialization_error"}';
        }
        exit;
    }
}
