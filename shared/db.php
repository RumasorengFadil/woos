<?php
// Koneksi PDO PostgreSQL (satu per request). Dashboard hanya MEMBACA hasil pipeline.

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $c = config('db');
        $dsn = sprintf('pgsql:host=%s;port=%d;dbname=%s', $c['host'], $c['port'], $c['dbname']);
        $pdo = new PDO($dsn, $c['user'], $c['password'] ?: null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        $pdo->exec('SET search_path TO ' . preg_replace('/[^a-z_]/', '', $c['schema']));
    }
    return $pdo;
}

function db_all(string $sql, array $params = []): array
{
    $st = db()->prepare($sql);
    $st->execute($params);
    return $st->fetchAll();
}

function db_one(string $sql, array $params = []): ?array
{
    $st = db()->prepare($sql);
    $st->execute($params);
    $row = $st->fetch();
    return $row === false ? null : $row;
}

function db_value(string $sql, array $params = []): mixed
{
    $st = db()->prepare($sql);
    $st->execute($params);
    return $st->fetchColumn();
}
