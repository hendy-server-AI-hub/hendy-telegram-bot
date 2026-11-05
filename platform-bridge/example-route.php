<?php

declare(strict_types=1);

/*
 * Mount this dispatcher from the PHP application's API router.
 * The existing application container should supply each data provider.
 *
 * Route pattern:
 * GET /api/integrations/telegram/v1/{status|jobs|orders|metrics}
 *
 * Example:
 * $providers = [
 *   'jobs' => fn (): array => [
 *       'items' => $videoJobs->recentForAdmin(25),
 *       'total' => $videoJobs->count(),
 *   ],
 *   'orders' => fn (): array => [
 *       'items' => $orders->recentForAdmin(25),
 *       'total' => $orders->count(),
 *   ],
 *   'metrics' => fn (): array => $dashboardMetrics->telegramSafeSummary(),
 * ];
 *
 * Use only the application's existing services, bounded pagination, and
 * explicitly allowlisted fields. Do not return payment details, password
 * hashes, sessions, tokens, or full personal records.
 */

require_once __DIR__ . '/HendyTelegramBridge.php';

// Your router must pass the final path segment as $resource.
$resource = (string)($routeParameters['resource'] ?? '');
$token = (string)(getenv('TELEGRAM_BRIDGE_TOKEN') ?: '');
$providers = $telegramBridgeProviders ?? [];

HendyTelegramBridge::dispatch($resource, $token, $providers);
