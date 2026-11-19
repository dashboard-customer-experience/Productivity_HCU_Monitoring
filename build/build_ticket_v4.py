#!/usr/bin/env python3
"""Bangun hcu_ticket.csv dari export ticketing + roster.

Pemakaian:
  python3 build_ticket_v4.py <ticket.csv|ticket.csv.gz> <roster.csv> <out.csv>

Catatan: versi ini mendeteksi gzip otomatis (pandas membaca .gz dari ekstensi),
jadi bisa dipakai dengan CSV biasa hasil fetch publish-to-web Google Sheets
maupun file .gz lokal.
"""
import sys
import re
import pandas as pd

src, roster_p, out = sys.argv[1], sys.argv[2], sys.argv[3]


def norm(s):
    s = str(s).replace('\u2019', "'").replace('\u2018', "'")
    return re.sub(r'\s+', ' ', s).strip().casefold()


def secs(s):
    p = str(s).strip().split(':')
    if len(p) != 3:
        return float('nan')
    try:
        return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
    except ValueError:
        return float('nan')


ro = pd.read_csv(roster_p, dtype=str, keep_default_na=False)
rn = {norm(a): a for a in ro['agent']}

# pandas mendeteksi kompresi dari ekstensi (.gz -> gzip, selain itu infer/plain).
d = pd.read_csv(src, dtype=str, keep_default_na=False)
d = d.drop_duplicates(subset=['Ticket ID'])
d['agent'] = [rn.get(norm(x)) for x in d['Nama Agent']]
d = d[d.agent.notna()].copy()
d['dt'] = pd.to_datetime(d['Date Key'], format='%d %b %Y')
d['fr'] = d['First Response Time (HH:MM:SS)'].map(secs)
d['rs'] = d['Resolution Time (HH:MM:SS)'].map(secs)
d['fr_m'] = d.fr / 60
d['rs_m'] = d.rs / 60
d['fcr_ok20'] = (d.fr <= 20).astype(int)
d['fcr_ok30'] = (d.fr <= 30).astype(int)
d['rs_ok60'] = (d.rs <= 60).astype(int)
d['rs_ok120'] = (d.rs <= 120).astype(int)
g = d.groupby([d.dt.dt.strftime('%Y-%m-%d'), 'agent']).agg(
    tickets=('Ticket ID', 'size'),
    fcr_sum=('fr_m', 'sum'), res_sum=('rs_m', 'sum'), res_n=('rs', 'count'),
    fcr_n=('fr', 'count'), fcr_ok20=('fcr_ok20', 'sum'), fcr_ok30=('fcr_ok30', 'sum'),
    rs_ok60=('rs_ok60', 'sum'), rs_ok120=('rs_ok120', 'sum')).reset_index()
g.columns = ['date', 'agent', 'tickets', 'fcr_sum', 'res_sum', 'res_n', 'fcr_n',
             'fcr_ok20', 'fcr_ok30', 'rs_ok60', 'rs_ok120']
g = g.sort_values(['date', 'agent'])
g.to_csv(out, index=False, float_format='%.4f')
print('rows', len(g), 'tickets', int(g.tickets.sum()), 'min', g.date.min(), 'max', g.date.max())
