#!/usr/bin/env python3
"""Satu perintah untuk semua data dashboard Prod HCU.

Membangun dari export raw:
  - hcu_agg.csv, hcu_perf.csv, hcu_lookup.csv  (productivity, dari H1 + H2)
  - hcu_ticket.csv                              (ticketing, dari export ticket)

Pemakaian:
  python3 build/aggregate.py \
      --h1 H1.csv --h2 H2.csv \
      --ticket ticket_export.csv \
      --roster data/hcu_roster.csv \
      --out data/

Opsional: --skip-prod atau --skip-ticket kalau cuma mau bangun salah satunya.

Setelah build, script mencetak ringkasan (jumlah baris, rentang tanggal, total)
supaya bisa dicek sebelum dipakai.
"""
import argparse
import os
import subprocess
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print('>>', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def summarize(path, date_col='date', count_col=None):
    df = pd.read_csv(path)
    dates = df[date_col].astype(str)
    line = f"{os.path.basename(path)}: {len(df):,} baris, {dates.min()} s/d {dates.max()}"
    if count_col:
        line += f", total {int(df[count_col].sum()):,}"
    print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--h1')
    ap.add_argument('--h2')
    ap.add_argument('--ticket')
    ap.add_argument('--roster', required=True)
    ap.add_argument('--out', default='data')
    ap.add_argument('--skip-prod', action='store_true')
    ap.add_argument('--skip-ticket', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    py = sys.executable

    if not a.skip_prod:
        if not (a.h1 and a.h2):
            ap.error('--h1 dan --h2 wajib kalau tidak pakai --skip-prod')
        run([py, os.path.join(HERE, 'build_productivity.py'),
             '--h1', a.h1, '--h2', a.h2, '--roster', a.roster, '--out', a.out])

    if not a.skip_ticket:
        if not a.ticket:
            ap.error('--ticket wajib kalau tidak pakai --skip-ticket')
        run([py, os.path.join(HERE, 'build_ticket_v4.py'),
             a.ticket, a.roster, os.path.join(a.out, 'hcu_ticket.csv')])

    print('\n--- ringkasan ---')
    if not a.skip_prod:
        summarize(os.path.join(a.out, 'hcu_agg.csv'), count_col='count')
        summarize(os.path.join(a.out, 'hcu_perf.csv'), count_col='count')
    if not a.skip_ticket:
        summarize(os.path.join(a.out, 'hcu_ticket.csv'), count_col='tickets')


if __name__ == '__main__':
    main()
