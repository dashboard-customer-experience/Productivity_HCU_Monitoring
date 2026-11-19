# Auto-update data dashboard Prod HCU

Robot (GitHub Action) menarik data dari Google Sheets (publish-to-web),
menjalankan agregasi, lalu commit hasilnya ke folder `data/`.
Dashboard `index.html` membaca 5 file CSV di `data/` saat dibuka.

## Alur

```
Sheets (SourceData H1, SourceData H2, Raw Data ticketing)
  -> Action: curl 3 CSV
  -> python build/aggregate.py
  -> data/hcu_agg.csv, hcu_perf.csv, hcu_lookup.csv, hcu_ticket.csv
  -> commit & push
  -> index.html fetch 5 CSV -> dashboard update
```

Tidak perlu upload index.html manual lagi. Cukup update Sheets.
Jadwal default: tiap Senin 12:00 WIB (05:00 UTC). Bisa juga dijalankan manual
dari tab **Actions -> Update dashboard data -> Run workflow**.

## File

- `build/aggregate.py` — orchestrator
- `build/build_productivity.py` — hasil: hcu_agg.csv, hcu_perf.csv, hcu_lookup.csv
- `build/build_ticket_v4.py` — hasil: hcu_ticket.csv
- `build/requirements.txt` — dependency Python (pandas)
- `build/workflow-update-data.yml` — SALIN ke `.github/workflows/update-data.yml`
- `data/hcu_roster.csv` — roster manual (31 agent, shiftlead, segment). Edit di sini.

## Langkah pasang (sekali saja)

1. Lengkapi `data/hcu_roster.csv` menjadi 31 agent (nama persis seperti di data,
   shiftlead, segment Senior/Junior).
2. Buat file `.github/workflows/update-data.yml` dengan isi dari
   `build/workflow-update-data.yml`.
3. Aktifkan **Settings -> Actions -> General -> Workflow permissions ->
   Read and write permissions**.
4. Jalankan workflow manual sekali untuk mengetes (tab Actions -> Run workflow).
5. Setelah `data/*.csv` terbentuk, update `index.html` agar membaca dari `data/`.

## Mengganti URL sumber

Semua URL publish-to-web ada di bagian `env:` pada workflow. Ganti di situ saja.
