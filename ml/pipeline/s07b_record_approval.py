"""Tahap 7b — Catat validasi bisnis (PRD §45: Business Validation -> Approved Model).

Menulis `approval.json` di samping artefak model dan memperbarui `metrics.json`
menjadi validation_status = APPROVED. Hanya dijalankan setelah pakar domain menyetujui
label & pertanyaan validasi (D-030). Publish (Tahap 8) menolak model tanpa file ini.

Jalankan:  ml/.venv/bin/python ml/pipeline/s07b_record_approval.py [--dataset=v2]
"""
import json
from datetime import datetime, timezone

from config import OUTPUTS, dataset

APPROVAL = {
    "experiment_id": "EXP-KM-067",
    "decision": "D-030",
    "approved_by": "kustan@fahove.com (pemilik riset / pakar domain)",
    "approved_on": "2026-09-27",
    "validation_answers": {
        "V1_labels": "Setuju — kelima label usulan dipakai",
        "V2_stable_label": "Setuju — label 'Relatif Stabil' dipertahankan (catatan: berbasis 1 snapshot, D-008)",
        "V3_directorate_pool_units": "Setuju — cukup ditandai sebagai anggota atipikal (is_atypical_member)",
        "V4_representative_orgs": "Setuju — contoh representatif sesuai",
        "V5_unbudgeted_keuangan": "Setuju — pola Terisi Tanpa Formasi di unit verifikasi/pembayaran Keuangan diterima",
    },
}


def main():
    ds = dataset()
    art = OUTPUTS / "07_interpretation" / ds["version"] / "model_artifacts"
    metrics = json.loads((art / "metrics.json").read_text())
    if metrics["experiment_id"] != APPROVAL["experiment_id"]:
        raise SystemExit("Artefak bukan model yang disetujui")
    APPROVAL["recorded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    APPROVAL["dataset_version"] = ds["version"]
    (art / "approval.json").write_text(json.dumps(APPROVAL, indent=2, ensure_ascii=False))
    metrics["validation_status"] = "APPROVED"
    metrics["approval"] = {k: APPROVAL[k] for k in ["decision", "approved_by", "approved_on"]}
    (art / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("APPROVED:", metrics["experiment_id"])


if __name__ == "__main__":
    main()
