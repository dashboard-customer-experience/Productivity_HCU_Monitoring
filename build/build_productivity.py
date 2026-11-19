#!/usr/bin/env python3
"""Bangun data harian dan performance dashboard Prod HCU dari export raw (H1 + H2).

Pemakaian:
  python3 build_productivity.py --h1 H1.csv --h2 H2.csv --roster data/hcu_roster.csv --out data/

Output: hcu_agg.csv (harian), hcu_perf.csv (per agent per hari/source/jam), hcu_lookup.csv (kamus id).
Baris yang identik di semua kolom dihapus sebelum dihitung.

Catatan: versi ini menerima CSV biasa maupun .gz (dideteksi dari ekstensi file),
supaya bisa dipakai langsung dengan hasil fetch publish-to-web Google Sheets.
"""
import argparse
import os

import pandas as pd


def norm(s):
    s = str(s).replace('\u2019', "'").replace('\u2018', "'")
    return ' '.join(s.split()).casefold()


def make_ids(values):
    return {v: i for i, v in enumerate(sorted(set(values)))}


def read_any(path):
    # pandas otomatis mendeteksi gzip dari ekstensi .gz; selain itu dibaca biasa.
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--h1', required=True)
    ap.add_argument('--h2', required=True)
    ap.add_argument('--roster', required=True)
    ap.add_argument('--out', default='data')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    raw = pd.concat(
        [read_any(p) for p in (a.h1, a.h2)],
        ignore_index=True,
    )
    raw = raw.drop_duplicates(subset=list(raw.columns)).copy()
    print('baris setelah hapus duplikat:', len(raw))

    raw['Channel'] = raw['Channel'].replace('', '(Tanpa Channel)')
    raw['Topic Name'] = raw['Topic Name'].replace('', '(Tanpa Topic)')
    raw['Source'] = raw['Source'].replace('', '(Tanpa Source)')
    raw['Nama Agent'] = raw['Nama Agent'].replace('', '(Tanpa Agent)')
    raw['dt'] = pd.to_datetime(raw['Date'], format='%d/%m/%Y')
    raw['hour'] = pd.to_numeric(raw['Time'], errors='coerce').fillna(0).astype(int)

    ro = pd.read_csv(a.roster, dtype=str)
    roster_names = set(ro['agent'])
    roster_by_norm = {norm(x): x for x in ro['agent']}
    raw['ag'] = [roster_by_norm.get(norm(x), x) for x in raw['Nama Agent']]

    ids = {
        'ch': make_ids(raw['Channel']),
        'tp': make_ids(raw['Topic Name']),
        'ag': make_ids(raw['ag']),
        'sr': make_ids(raw['Source']),
    }
    lookup = pd.DataFrame(
        [(k, i, n) for k, d in ids.items() for n, i in d.items()],
        columns=['kind', 'id', 'name'],
    )
    lookup.to_csv(os.path.join(a.out, 'hcu_lookup.csv'), index=False)

    daily = pd.DataFrame({
        'dt': raw['dt'],
        'ch': raw['Channel'].map(ids['ch']),
        'tp': raw['Topic Name'].map(ids['tp']),
        'ag': raw['ag'].map(ids['ag']),
        'sr': raw['Source'].map(ids['sr']),
    })
    daily = daily.groupby(['dt', 'ch', 'tp', 'ag', 'sr']).size().reset_index(name='count')
    daily['date'] = daily['dt'].dt.strftime('%Y-%m-%d')
    daily[['date', 'ch', 'tp', 'ag', 'sr', 'count']].to_csv(
        os.path.join(a.out, 'hcu_agg.csv'), index=False)

    hcu = raw[raw['ag'].isin(roster_names)]
    perf = hcu.assign(date=hcu['dt'].dt.strftime('%Y-%m-%d'))
    perf = perf.groupby(['date', 'ag', 'Source', 'hour']).size().reset_index(name='count')
    perf.columns = ['date', 'agent', 'source', 'hour', 'count']
    perf.to_csv(os.path.join(a.out, 'hcu_perf.csv'), index=False)

    print('harian:', len(daily), 'baris | perf HCU:', len(perf), 'baris')


if __name__ == '__main__':
    main()
