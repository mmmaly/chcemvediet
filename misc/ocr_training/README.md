# Tesseract OCR for chcemvediet: model and training notes

The anonymization pipeline can use Tesseract instead of ABBYY FineReader
(`OCR_ENGINE = 'tesseract'`, see `chcemvediet/apps/anonymization/tesseract_odt.py`).
The stock Tesseract models are not good enough for our documents, so we use a model
fine-tuned on our own data. This directory keeps the scripts that produced it.

## Using the model

    apt install tesseract-ocr poppler-utils
    # model file chv.traineddata (16 MB) in a directory that also has Tesseract's `configs/`
    OCR_ENGINE = u'tesseract'
    TESSERACT_LANG = u'chv'
    TESSERACT_TESSDATA = u'/opt/tessdata_ft4c'

The model is not in git. Download `chv.traineddata` from the GitHub release
[ocr-model-r4](https://github.com/mmmaly/chcemvediet/releases/tag/ocr-model-r4)
(sha256 `d3f9e0f59830ab7da2475fea0c74a11c95e185d3c3ed0d39f5f442e6b423836a`); on the production
server it is in `/opt/tessdata_ft4c`. Its dictionary is the stock Slovak word list plus a few
generic words with `ĺ`/`ŕ`; it contains no words taken from our documents (an earlier build
did, and must not be published).

## Why a custom model

Measured on 60 of our documents from 2025-2026 (30 PDFs with a text layer = ground truth,
30 scans compared with ABBYY's output), 116 pages:

| engine | native: words correct (median / mean / worst) | `@` | `§` | `ĺ` |
|---|---|---|---|---|
| ABBYY FineReader 11 | 98.6 % / 93.6 % / 30.9 % | 54/55 | 82/82 | 19/19 |
| Tesseract `slk` (tessdata_best) | 97.7 % / 96.5 % | 0/55 | 0/82 | 0/19 |
| Tesseract `script/Latin` | 98.2 % / 97.1 % | 55/55 | 80/82 | 0/19 |
| Latin fine-tuned, round 3 | 98.8 % / 97.3 % / 76.9 % | 55/55 | 82/82 | 0/19 |
| **Latin fine-tuned, round 4** | **99.3 % / 97.9 % / 82.3 %** | 55/55 | 82/82 | 14/19 |

* The stock Slovak model has a 120 character set without `@ § & – ; ' = Q q ĺ ö ü`.
* `ŕ` is still not recognized by round 4 (0/7 in the sample); it needs more training.
* Round 5 taught `ŕ` with synthetic lines full of `ŕ`/`ĺ` words and overdid it: the model then
  wrote `ŕ`/`ĺ` for `ť`, `ľ`, `ž` and capital `Í` ("INVESTÍCIĺ"). Synthetic material for rare
  letters has to contain their look-alikes too.

## How the model was trained

1. `build_train.py`: for PDFs that have a real text layer, render pages at 300 dpi, run
   Tesseract to get the line boxes exactly as recognition sees them, fill each line with the
   words of the text layer, write a page-level `WordStr` box file and let Tesseract create
   the `.lstmf`. Lines whose text is far from Tesseract's own reading are dropped.
   (Cutting line images ourselves from PDF coordinates made the model *worse* on pages.)
2. `train_round3.sh`: fine-tune `script/Latin` (tessdata_best) on 11.5k such lines, 10k iterations.
3. `train_round4.sh`: pages from 273 documents containing `ĺ`/`ŕ`, synthetic lines
   (`text2image`, 8 fonts), character set extended with `Ĺ Ŕ ŕ`, Slovak word list, 9k more
   iterations from the round 3 checkpoint.
4. `score.py`: the evaluation used for the table above.

The scripts have paths of the working directory (`/root/ocr-test` on the server) hard-coded;
they are kept as a record and a starting point, not as a polished tool.
