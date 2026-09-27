-- 005 — Calinski–Harabasz dapat sangat besar pada run dengan kelompok organisasi identik (artefak titik kembar,
-- S05 §4) sehingga melampaui NUMERIC(14,2). Ubah ke DOUBLE PRECISION. Nilai tak hingga disimpan sebagai NULL.
ALTER TABLE woos.experiment ALTER COLUMN calinski_harabasz TYPE DOUBLE PRECISION;
