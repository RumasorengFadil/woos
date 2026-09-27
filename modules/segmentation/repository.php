<?php
// Query baca untuk domain segmentasi. SELURUH nilai cluster/label/metrik berasal dari hasil pipeline ML
// yang dipublish (PRD §47, §95). Tidak ada clustering, rule klasifikasi, atau perhitungan metrik model di sini.

const GRADE_GROUPS = ['MAK', 'MA', 'MM', 'MD', 'SPESIALIS', 'GENERALIS', 'UNKNOWN'];
const SORTABLE = [
    'name' => 'organization_name', 'ftk' => 'ftk', 'realization' => 'realization', 'gap' => 'gap',
    'fulfillment' => 'fulfillment_ratio', 'vacant' => 'vacant_share', 'cluster' => 'cluster_id', 'level' => 'organization_level',
];

function validated_model(): ?array
{
    return db_one('SELECT m.model_id, m.experiment_id, m.model_name, m.model_version, m.dataset_version, m.feature_version,
                          m.features_used, m.scaler, m.hyperparameters, m.metrics, m.validation_status, m.approved_by,
                          m.approved_on, m.trained_at, m.published_at, d.period, d.scope
                   FROM v_validated_model m JOIN dataset_version d USING (dataset_version)
                   ORDER BY d.period DESC LIMIT 1');
}

function periods(): array
{
    return db_all("SELECT dataset_version, period, scope, status FROM dataset_version WHERE status = 'ACTIVE' ORDER BY period DESC");
}

/** Normalisasi input filter dari query string (whitelist). */
function read_filters(array $q): array
{
    $f = [
        'dataset'     => isset($q['dataset']) && is_string($q['dataset']) ? $q['dataset'] : null,
        'directorate' => isset($q['directorate']) && preg_match('/^ORG-\d{4}$/', (string) $q['directorate']) ? $q['directorate'] : null,
        'level'       => isset($q['level']) && ctype_digit((string) $q['level']) ? (int) $q['level'] : null,
        'cluster'     => isset($q['cluster']) && preg_match('/^[A-Z_]{2,30}$/', (string) $q['cluster']) ? $q['cluster'] : null,
        'grade'       => isset($q['grade']) && in_array($q['grade'], GRADE_GROUPS, true) ? $q['grade'] : null,
        'atypical'    => !empty($q['atypical']) ? true : null,
        'search'      => isset($q['q']) && is_string($q['q']) && trim($q['q']) !== '' ? mb_substr(trim($q['q']), 0, 80) : null,
    ];
    return $f;
}

/** Klausa WHERE + parameter untuk v_validated_organization. */
function filter_sql(array $f, string $alias = 'v'): array
{
    $w = [];
    $p = [];
    if ($f['dataset']) { $w[] = "$alias.dataset_version = :dataset"; $p['dataset'] = $f['dataset']; }
    if ($f['directorate']) { $w[] = "$alias.directorate_id = :directorate"; $p['directorate'] = $f['directorate']; }
    if ($f['level'] !== null) { $w[] = "$alias.organization_level = :level"; $p['level'] = $f['level']; }
    if ($f['cluster']) { $w[] = "$alias.cluster_code = :cluster"; $p['cluster'] = $f['cluster']; }
    if ($f['grade']) { $w[] = "($alias.grade_distribution->'pct'->>:grade)::numeric > 0"; $p['grade'] = $f['grade']; }
    if ($f['atypical']) { $w[] = "$alias.is_atypical_member"; }
    if ($f['search']) { $w[] = "$alias.organization_name ILIKE :search"; $p['search'] = '%' . $f['search'] . '%'; }
    return [$w ? 'WHERE ' . implode(' AND ', $w) : '', $p];
}

function filter_options(): array
{
    return [
        'directorates' => db_all("SELECT DISTINCT directorate_id, directorate_name FROM v_validated_organization
                                  WHERE directorate_id IS NOT NULL ORDER BY directorate_name"),
        'levels'   => array_column(db_all('SELECT DISTINCT organization_level FROM v_validated_organization ORDER BY 1'), 'organization_level'),
        'clusters' => cluster_profiles(),
        'grades'   => GRADE_GROUPS,
    ];
}

function summary(array $f): array
{
    [$where, $p] = filter_sql($f);
    return db_one("SELECT count(*) AS organizations,
                          count(*) FILTER (WHERE segmentation_status = 'SEGMENTED') AS segmented,
                          count(*) FILTER (WHERE segmentation_status = 'NOT_SEGMENTED') AS not_segmented,
                          sum(ftk) AS ftk, sum(realization) AS realization, sum(gap) AS gap,
                          sum(position_count) AS positions, sum(vacant_position_count) AS vacant_positions,
                          count(*) FILTER (WHERE is_atypical_member) AS atypical,
                          count(DISTINCT cluster_id) AS clusters
                   FROM v_validated_organization v $where", $p) ?? [];
}

/** Profil cluster model tervalidasi (label bisnis, PRD §43, §56). */
function cluster_profiles(?int $modelId = null): array
{
    $sql = 'SELECT p.* FROM cluster_profile p WHERE p.model_id = ' . ($modelId === null
        ? '(SELECT model_id FROM v_validated_model LIMIT 1)' : ':m') . ' ORDER BY p.cluster_id';
    $rows = db_all($sql, $modelId === null ? [] : ['m' => $modelId]);
    foreach ($rows as &$r) {
        $r['characteristics'] = json_decode($r['characteristics'] ?? '[]', true);
        $r['centroid'] = json_decode($r['centroid'] ?? 'null', true);
    }
    return $rows;
}

function cluster_distribution(array $f): array
{
    [$where, $p] = filter_sql($f);
    return db_all("SELECT cluster_id, cluster_code, cluster_label, count(*) AS n, sum(ftk) AS ftk, sum(realization) AS realization,
                          sum(gap) AS gap
                   FROM v_validated_organization v $where GROUP BY 1, 2, 3 ORDER BY cluster_id NULLS LAST", $p);
}

function cluster_feature_stats(array $f): array
{
    [$where, $p] = filter_sql($f);
    $cond = $where ? $where . " AND segmentation_status = 'SEGMENTED'" : "WHERE segmentation_status = 'SEGMENTED'";
    return db_all("SELECT cluster_id, count(*) AS n,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY fulfillment_ratio) AS ful_q1,
        percentile_cont(0.5)  WITHIN GROUP (ORDER BY fulfillment_ratio) AS ful_med,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY fulfillment_ratio) AS ful_q3,
        percentile_cont(0.5)  WITHIN GROUP (ORDER BY vacant_share) AS vac_med,
        avg(vacant_share) AS vac_mean, avg(avg_realization_per_position) AS arp_mean,
        percentile_cont(0.5)  WITHIN GROUP (ORDER BY avg_realization_per_position) AS arp_med,
        avg(gap) AS gap_mean, avg(ftk) AS ftk_mean, avg(realization) AS real_mean
        FROM v_validated_organization v $cond GROUP BY cluster_id ORDER BY cluster_id", $p);
}

function cluster_by_directorate(array $f): array
{
    [$where, $p] = filter_sql($f);
    return db_all("SELECT directorate_id, directorate_name, cluster_code, count(*) AS n
                   FROM v_validated_organization v $where GROUP BY 1, 2, 3 ORDER BY 2", $p);
}

function viz_points(array $f, ?int $modelId = null): array
{
    if ($modelId === null) {
        [$where, $p] = filter_sql($f);
        $cond = $where ? "$where AND viz_x IS NOT NULL" : 'WHERE viz_x IS NOT NULL';
        return db_all("SELECT organization_id AS id, organization_name AS name, cluster_id AS c, cluster_label AS label,
                              viz_x AS x, viz_y AS y FROM v_validated_organization v $cond", $p);
    }
    return db_all('SELECT r.organization_id AS id, o.organization_name AS name, r.cluster_id AS c, r.cluster_label AS label,
                          r.viz_x AS x, r.viz_y AS y
                   FROM cluster_result r JOIN organization o USING (dataset_version, organization_id)
                   WHERE r.model_id = :m AND r.viz_x IS NOT NULL', ['m' => $modelId]);
}

function organizations(array $f, string $sort, string $dir, int $page, int $size): array
{
    [$where, $p] = filter_sql($f);
    $col = SORTABLE[$sort] ?? 'organization_name';
    $dir = strtolower($dir) === 'desc' ? 'DESC' : 'ASC';
    $total = (int) db_value("SELECT count(*) FROM v_validated_organization v $where", $p);
    $offset = max(0, ($page - 1) * $size);
    $rows = db_all("SELECT organization_id, organization_name, directorate_name, organization_level, ftk, realization, gap,
                           fulfillment_ratio, vacant_share, cluster_id, cluster_code, cluster_label, is_atypical_member, segmentation_status
                    FROM v_validated_organization v $where
                    ORDER BY $col $dir NULLS LAST, organization_id LIMIT $size OFFSET $offset", $p);
    return ['total' => $total, 'rows' => $rows];
}

function organization_detail(string $id): ?array
{
    $org = db_one('SELECT * FROM v_validated_organization WHERE organization_id = :id', ['id' => $id]);
    if (!$org) {
        return null;
    }
    $org['grade_distribution'] = json_decode($org['grade_distribution'], true);
    $org['profile'] = $org['cluster_id'] === null ? null : db_one(
        'SELECT * FROM cluster_profile WHERE model_id = :m AND cluster_id = :c', ['m' => $org['model_id'], 'c' => $org['cluster_id']]);
    if ($org['profile']) {
        $org['profile']['characteristics'] = json_decode($org['profile']['characteristics'], true);
    }
    $org['children'] = db_all('SELECT organization_id, organization_name, cluster_label, ftk, realization
                               FROM v_validated_organization WHERE parent_organization_id = :id ORDER BY organization_name', ['id' => $id]);
    $org['other_models'] = db_all("SELECT m.experiment_id, m.model_name, m.validation_status, r.cluster_label
                                   FROM cluster_result r JOIN model m USING (model_id)
                                   WHERE r.organization_id = :id AND NOT m.is_validated_model ORDER BY m.model_name", ['id' => $id]);
    return $org;
}

function model_comparison(): array
{
    $rows = db_all('SELECT * FROM v_model_comparison ORDER BY is_validated_model DESC, model_name');
    foreach ($rows as &$r) {
        $r['hyperparameters'] = json_decode($r['hyperparameters'], true);
        $r['clusters'] = cluster_profiles((int) $r['model_id']);
    }
    return $rows;
}

/** Kurva metrik vs K dari registri eksperimen untuk konfigurasi model tervalidasi (PRD §29, §69). */
function metric_curves(string $featureSet, string $scaler): array
{
    return db_all("SELECT model_name, hyperparameters->>'linkage' AS linkage, (hyperparameters->>'n_clusters')::int AS k,
                          silhouette, davies_bouldin, inertia
                   FROM experiment WHERE variant = 'all' AND feature_set = :fs AND scaler = :sc
                     AND model_name IN ('KMEANS', 'HIERARCHICAL') ORDER BY model_name, linkage, k",
                  ['fs' => $featureSet, 'sc' => $scaler]);
}

function dbscan_runs(string $featureSet, string $scaler): array
{
    return db_all("SELECT experiment_id, (hyperparameters->>'eps')::numeric AS eps, (hyperparameters->>'min_samples')::int AS min_samples,
                          n_clusters, noise_share, silhouette, eligible
                   FROM experiment WHERE model_name = 'DBSCAN' AND variant = 'all' AND feature_set = :fs AND scaler = :sc
                   ORDER BY min_samples, eps", ['fs' => $featureSet, 'sc' => $scaler]);
}

function query_keep(array $f, array $extra = []): array
{
    $map = ['dataset' => 'dataset', 'directorate' => 'directorate', 'level' => 'level', 'cluster' => 'cluster',
            'grade' => 'grade', 'atypical' => 'atypical', 'search' => 'q'];
    $q = [];
    foreach ($map as $k => $param) {
        if ($f[$k] !== null && $f[$k] !== false) {
            $q[$param] = $f[$k] === true ? 1 : $f[$k];
        }
    }
    return array_merge($q, $extra);
}
