#!/root/ocr-test/venv/bin/python
# Round 2 training data: page-level. For every page of a native PDF: run Tesseract (hOCR) to get the
# line boxes exactly as recognition sees them, fill each line with the text-layer words that lie in
# it (ground truth), write a WordStr box file for the whole page and let Tesseract make the .lstmf
# with its own line extraction. Lines whose ground truth is far from Tesseract's reading are left
# out (bad text layers, misplaced boxes).
import csv, os, random, re, subprocess, sys, unicodedata
from xml.etree import ElementTree
from rapidfuzz.distance import Levenshtein

BASE = u'/root/ocr-test'
MEDIA = u'/var/www/chcemvediet/chcemvediet/media/'
OUT = BASE + u'/' + os.environ.get(u'OUT', u'train2')
NAME = os.environ.get(u'OUT', u'train2')
DOCLIST = os.environ.get(u'DOCLIST')
TESSDATA = BASE + u'/tessdata_best'
DPI = 300
MAX_DOCS = int(sys.argv[1]) if len(sys.argv) > 1 else 250
MAX_PAGES = int(os.environ.get(u'MAX_PAGES', u'4'))
ALLOWED = re.compile(u'^[0-9A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýžĚŘŮěřůÜüÖö'
                     u' .,;:!?()\\[\\]%&@§€*+/=<>"\'„“”‚‘’–\\-_#°]+$')
X = u'{http://www.w3.org/1999/xhtml}'

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

def norm(t):
    t = unicodedata.normalize(u'NFC', t).replace(u' ', u' ').replace(u'­', u'')
    t = t.replace(u'—', u'–').replace(u'’', u"'").replace(u'‘', u"'").replace(u'”', u'“')
    return re.sub(r'\s+', u' ', t).strip()

def title(e):
    res = {}
    for part in (e.get(u'title') or u'').split(u';'):
        f = part.split()
        if f:
            res[f[0]] = f[1:]
    return res

def main():
    random.seed(7)
    os.makedirs(OUT, exist_ok=True)
    sample_ids = {r[0] for r in csv.reader(open(BASE + u'/sample.tsv'), delimiter=u'\t')}
    corpus = {r[0]: r for r in csv.reader(open(BASE + u'/corpus.tsv'), delimiter=u'\t')}
    native = [r for r in csv.reader(open(BASE + u'/corpus_class.tsv'), delimiter=u'\t')
              if r[0] not in sample_ids and int(r[2]) >= 50 and 1 <= int(r[1]) <= MAX_PAGES]
    random.shuffle(native)
    docs = native[:MAX_DOCS]
    if DOCLIST:
        wanted = {l.split(u'\t')[0] for l in open(DOCLIST).read().splitlines() if l.strip()}
        docs = [r for r in csv.reader(open(BASE + u'/corpus_class.tsv'), delimiter=u'\t')
                if r[0] in wanted and r[0] not in sample_ids and 1 <= int(r[1]) <= MAX_PAGES]
    seen_path = BASE + u'/%s_seen.txt' % NAME
    seen = set(open(seen_path).read().split()) if os.path.exists(seen_path) else set()
    log = open(BASE + u'/%s.log' % NAME, u'a')
    kept = dropped = 0
    for n, (rid, pages, chars, name) in enumerate(docs):
        if rid in seen:
            continue
        open(seen_path, u'a').write(rid + u'\n')
        pdf = MEDIA + corpus[rid][2]
        try:
            run([u'pdftoppm', u'-r', str(DPI), u'-gray', u'-png', pdf, os.path.join(OUT, rid + u'-p')])
            root = ElementTree.fromstring(run([u'pdftotext', u'-bbox-layout', pdf, u'-']).decode(u'utf-8'))
        except (subprocess.CalledProcessError, ElementTree.ParseError):
            continue
        images = sorted(f for f in os.listdir(OUT) if f.startswith(rid + u'-p') and f.endswith(u'.png'))
        for pno, page in enumerate(root.iter(X + u'page')):
            if pno >= len(images):
                break
            base = os.path.join(OUT, images[pno][:-4])
            try:
                run([u'tesseract', base + u'.png', base, u'--tessdata-dir', TESSDATA, u'-l', u'slk', u'--psm', u'3', u'hocr'])
                hocr = ElementTree.parse(base + u'.hocr').getroot()
            except (subprocess.CalledProcessError, ElementTree.ParseError):
                continue
            opage = hocr.find(u'.//%sdiv[@class="ocr_page"]' % X)
            W, H = [int(v) for v in title(opage)[u'bbox']][2:]
            sx, sy = W / float(page.get(u'width')), H / float(page.get(u'height'))
            gtwords = []
            for w in page.iter(X + u'word'):
                t = norm(w.text or u'')
                if t:
                    gtwords.append(((float(w.get(u'xMin')) + float(w.get(u'xMax'))) / 2 * sx,
                                    (float(w.get(u'yMin')) + float(w.get(u'yMax'))) / 2 * sy, t))
            boxes = []
            for line in opage.iter(X + u'span'):
                if line.get(u'class') != u'ocr_line':
                    continue
                x0, y0, x1, y1 = [int(v) for v in title(line)[u'bbox']]
                hyp = norm(u' '.join(u''.join(w.itertext()).strip() for w in line.iter(X + u'span') if w.get(u'class') == u'ocrx_word'))
                inside = sorted((g for g in gtwords if x0 - 3 <= g[0] <= x1 + 3 and y0 <= g[1] <= y1), key=lambda g: g[0])
                gt = u' '.join(g[2] for g in inside)
                if len(gt) < 3 or not ALLOWED.match(gt) or y1 - y0 < 15 or y1 - y0 > 250:
                    dropped += 1
                    continue
                if 1 - Levenshtein.normalized_distance(gt, hyp) < 0.75:
                    dropped += 1
                    continue
                boxes.append((x0, H - y1, x1, H - y0, gt))
                kept += 1
            if os.environ.get(u'ONLY_RARE') and not any(re.search(u'[ĺŕĹŔ]', b[4]) for b in boxes):
                boxes = []
            if len(boxes) < 3:
                os.remove(base + u'.hocr')
                continue
            with open(base + u'.box', u'w') as f:
                for x0, b, x1, t, gt in boxes:
                    f.write(u'WordStr %d %d %d %d 0 #%s\n' % (x0, b, x1, t, gt))
                    f.write(u'\t %d %d %d %d 0\n' % (x1 + 1, b, x1 + 5, t))
            with open(base + u'.gt.txt', u'w') as f:
                f.write(u'\n'.join(b[4] for b in boxes) + u'\n')
            try:
                run([u'tesseract', base + u'.png', base, u'--tessdata-dir', TESSDATA, u'-l', u'slk', u'--psm', u'6', u'lstm.train'])
            except subprocess.CalledProcessError:
                pass
            os.remove(base + u'.hocr')
        for f in images:
            os.remove(os.path.join(OUT, f))
        log.write(u'%d/%d %s kept=%d dropped=%d\n' % (n + 1, len(docs), rid, kept, dropped)); log.flush()
    log.write(u'BUILD2_DONE kept=%d dropped=%d\n' % (kept, dropped)); log.flush()

if __name__ == u'__main__':
    main()
