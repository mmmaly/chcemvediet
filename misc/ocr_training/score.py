#!/usr/bin/env python3
"""Score OCR outputs against the references in docs/.

Usage: python3 score.py ENGINE            (reads docs/<id>/<ENGINE>.txt for every document)
Reference: docs/<id>/gt.txt (PDF text layer, native documents) else docs/<id>/abbyy.txt.
Needs: pip install rapidfuzz
"""
import collections, csv, os, re, statistics as st, sys, unicodedata
from rapidfuzz.distance import Levenshtein

DIA = set(u'áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽěřůüöÉĚŘŮÜÖ')

def norm(t):
    t = unicodedata.normalize(u'NFC', t)
    t = re.sub(r'[­​]', u'', t)
    t = re.sub(r'-\n(?=[a-záäčďéíĺľňóôŕšťúýž])', u'', t)
    return re.sub(r'\s+', u' ', t).strip()

def strip_dia(t):
    return u''.join(c for c in unicodedata.normalize(u'NFD', t) if unicodedata.category(c) != u'Mn')

def words(t):
    return collections.Counter(re.findall(r'\w+', t.lower()))

def score(ref, hyp):
    r, h = words(ref), words(hyp)
    tp = sum(min(c, h[w]) for w, c in r.items())
    rd = collections.Counter(w for w in re.findall(r'\w+', ref) if set(w) & DIA)
    hw = words(hyp)
    dia = sum(min(c, hw[w.lower()] if False else collections.Counter(re.findall(r'\w+', hyp))[w]) for w, c in rd.items()) / sum(rd.values()) if rd else None
    return dict(
        cer=Levenshtein.normalized_distance(ref, hyp),
        wer=Levenshtein.normalized_distance(ref.split(), hyp.split()),
        cer_nodia=Levenshtein.normalized_distance(strip_dia(ref), strip_dia(hyp)),
        word_recall=tp / max(1, sum(r.values())),
        word_precision=tp / max(1, sum(h.values())),
        dia_recall=dia,
    )

def main():
    engines = sys.argv[1:] or [u'abbyy']
    here = os.path.dirname(os.path.abspath(__file__))
    index = list(csv.reader(open(os.path.join(here, u'docs/index.tsv')), delimiter=u'\t'))
    for eng in engines:
        by_kind = collections.defaultdict(list)
        for rid, kind, pages, name in index:
            d = os.path.join(here, u'docs', rid)
            hyp_path = os.path.join(d, eng + u'.txt')
            if not os.path.exists(hyp_path):
                continue
            ref_path = os.path.join(d, u'gt.txt') if kind == u'native' else os.path.join(d, u'abbyy.txt')
            if eng == u'abbyy' and kind == u'scan':
                continue
            s = score(norm(open(ref_path).read()), norm(open(hyp_path).read()))
            by_kind[kind].append(s)
        for kind, rows in sorted(by_kind.items()):
            med = lambda k: st.median(r[k] for r in rows if r[k] is not None)
            print(u'%-14s %-6s docs %2d  CER %.3f  WER %.3f  CER-no-accents %.3f  word recall %.3f  precision %.3f  accented-word recall %.3f'
                  % (eng, kind, len(rows), med(u'cer'), med(u'wer'), med(u'cer_nodia'), med(u'word_recall'), med(u'word_precision'), med(u'dia_recall')))

if __name__ == u'__main__':
    main()
