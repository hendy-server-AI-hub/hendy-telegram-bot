<?php

declare(strict_types=1);

/*
 * Example integration from the existing PHP application's API router.
 * Replace each provider with calls to the application's existing domain
 * services. Never return raw rows or payment/personal data.
 *
 * Route: GET /api/integrations/telegram/v1/{status|jobs|orders|metrics}
 */

require_once __DIR__ . '/HendyTelegramBridge.php';

// These service objects must be created by the existing application container.
// Example providers should return bounded, allowlisted operational data only.
$providers = [
    // 'status' => fn (): array => $healthService->safeStatus(),
    // 'jobs' => fn (): array => ['items' => $videoJobs->recentForAdmin(25), 'total' => $videoJobs->count()],
    // 'orders' => fn (): array => ['items' => $orders->recentForAdmin(25), 'total' => $orders->count()],
    // 'metrics' => fn (): array => $dashboardMetrics->telegramSafeSummary(),
];

$resource = (string)($_GET['resource'] ?? '');
$token = (string)(getenv('TELEGRAM_BRIDGE_TOKEN') ?: '');

HendyTelegramBridge::dispatch(
    $resource,
    $token,
    $providers,
    // Connect the application's existing shared rate limiter here.
    static fn (): bool => true
);
