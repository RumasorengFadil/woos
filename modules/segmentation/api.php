<?php
// Backend API read-only (PRD §46, §65). Mengembalikan hasil model tervalidasi yang sudah dipublish — tanpa komputasi model.
// GET ?resource=summary|clusters|organizations|organization|comparison  (+ parameter filter yang sama dengan dashboard)
require dirname(__DIR__, 2) . '/shared/bootstrap.php';
require_permission('dashboard.view');
require __DIR__ . '/repository.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
$filters = read_filters($_GET);
$model = validated_model();
$filters['dataset'] ??= $model['dataset_version'] ?? null;
$resource = (string) ($_GET['resource'] ?? '');

try {
    $data = match ($resource) {
        'summary' => ['model' => $model ? array_intersect_key($model, array_flip(['experiment_id', 'model_name', 'model_version',
                          'dataset_version', 'validation_status', 'trained_at', 'approved_on'])) : null,
                      'summary' => summary($filters), 'distribution' => cluster_distribution($filters)],
        'clusters' => cluster_profiles(),
        'organizations' => organizations($filters, (string) ($_GET['sort'] ?? 'name'), (string) ($_GET['dir'] ?? 'asc'),
                                         max(1, (int) ($_GET['page'] ?? 1)), min(200, max(1, (int) ($_GET['size'] ?? 50)))),
        'organization' => organization_detail((string) ($_GET['id'] ?? '')) ?? throw new DomainException('not_found'),
        'comparison' => model_comparison(),
        default => throw new InvalidArgumentException('unknown_resource'),
    };
    echo json_encode(['data' => $data], JSON_UNESCAPED_UNICODE | JSON_PRESERVE_ZERO_FRACTION);
} catch (DomainException $ex) {
    http_response_code(404);
    echo json_encode(['error' => $ex->getMessage()]);
} catch (InvalidArgumentException $ex) {
    http_response_code(400);
    echo json_encode(['error' => $ex->getMessage(), 'resources' => ['summary', 'clusters', 'organizations', 'organization', 'comparison']]);
}
