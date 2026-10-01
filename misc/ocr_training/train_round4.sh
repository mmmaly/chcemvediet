#!/bin/bash
# Round 4: teach the round-3 model ĺ and ŕ. Real pages containing them + synthetic lines, charset
# extended, training continued from the round-3 checkpoint, evaluation on the sample.
cd /root/ocr-test
export TESSDATA_PREFIX=/root/ocr-test/tessdata_latin
until [ -f rare.log ]; do sleep 30; done
echo "$(date +%T) $(cat rare.log)" > chain4.log
# 1. real pages that contain the rare letters (documents not used in round 2 keep their own pages)
rm -rf train4 train4.log train4_seen.txt
OUT=train4 DOCLIST=rare_docs.tsv MAX_PAGES=12 ONLY_RARE=1 nice -n 10 ./build_train2.py 0 >> chain4.out 2>&1
echo "$(date +%T) real pages: $(ls train4/*.lstmf 2>/dev/null | wc -l), lines $(cat train4/*.gt.txt | wc -l), with rare letters $(cat train4/*.gt.txt | grep -c '[ĺŕĹŔ]')" >> chain4.log
# 2. synthetic lines: real text lines with the rare letters + word drills, several fonts
rm -rf synth && mkdir -p synth
venv/bin/python - <<'PY'
import random, re
random.seed(11)
allowed = re.compile(u'^[0-9A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž .,;:!?()%&@§/"„“–\\-]+$')
lines = []
for l in open('rare_lines.txt', encoding='utf-8'):
    l = re.sub(r'\s+', ' ', l).strip()
    if 15 <= len(l) <= 95 and allowed.match(l):
        lines.append(l)
words = sorted({w.strip('.,;:()"„“') for l in open('rare_lines.txt', encoding='utf-8') for w in l.split() if re.search(u'[ĺŕĹŔ]', w) and allowed.match(w)})
words += u'stĺp stĺpec stĺpci kĺb hĺbka hĺbke dĺžka dĺžke dĺžeň jabĺk vĺn tĺcť žĺtok žltý mĺkvy spĺňa dopĺňa vypĺňa naplň vŕba tŕň vŕšok zmŕtvie zahŕňa odŕžať hŕba hŕstka kŕdeľ kŕmiť mŕtvy sŕdc tŕpky vŕtať zŕn Ĺubomír Ĺudovít Ŕ'.split()
filler = u'podľa zákona č. o sprístupnenie informácií v lehote žiadosť povinná osoba rozhodnutie odvolanie § ods. písm. zo dňa číslo strana príloha úrad mesto obec'.split()
for i in range(420):
    k = random.randint(5, 9); ws = [random.choice(words) if random.random() < 0.45 else random.choice(filler) for _ in range(k)]
    if not any(re.search(u'[ĺŕĹŔ]', w) for w in ws): ws[random.randrange(k)] = random.choice(words)
    l = ' '.join(ws); l = l[0].upper() + l[1:] if random.random() < 0.3 else l
    lines.append(l + random.choice(['', '.', ',', ';', ':']))
random.shuffle(lines)
open('synth/text.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print(len(lines), 'synthetic lines;', len(words), 'rare words')
PY
n=0
for font in "Liberation Sans" "Liberation Serif" "DejaVu Sans" "DejaVu Serif" "Nimbus Sans" "Nimbus Roman" "Liberation Sans Bold" "Liberation Sans Narrow"; do
  for pt in 10 12; do
    n=$((n+1)); base=synth/s$n
    text2image --text synth/text.txt --outputbase $base --font "$font" --fonts_dir /usr/share/fonts --ptsize $pt --resolution 300 --xsize 2480 --ysize 3508 --margin 150 --exposure $(( (n % 3) - 1 )) --max_pages 40 >/dev/null 2>&1 || continue
    tesseract $base.tif $base --tessdata-dir /root/ocr-test/tessdata_latin -l Latin --psm 6 lstm.train >/dev/null 2>&1
  done
done
echo "$(date +%T) synthetic lstmf files: $(ls synth/*.lstmf 2>/dev/null | wc -l) from $(wc -l < synth/text.txt) lines" >> chain4.log
# 3. character set and starting model (Slovak word list + our rare words: fast to build)
rm -rf ft4 && mkdir -p ft4/out
cat train2/*.gt.txt train4/*.gt.txt synth/text.txt > ft4/all_gt.txt
unicharset_extractor --output_unicharset ft4/new.unicharset --norm_mode 2 ft4/all_gt.txt >/dev/null 2>&1
combine_tessdata -u ft3/out/Latin/Latin.traineddata ft4/old. >/dev/null 2>&1
merge_unicharsets ft4/old.lstm-unicharset ft4/new.unicharset ft4/merged.unicharset >/dev/null 2>&1
( cat ft2/slk.wordlist; grep -ho "[A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž]\{2,\}" ft4/all_gt.txt ) | sort -u > ft4/words.txt
combine_lang_model --input_unicharset ft4/merged.unicharset --script_dir langdata --words ft4/words.txt \
  --numbers ft3/Latin.numbers --puncs ft3/Latin.punc --output_dir ft4/out --lang Latin >/dev/null 2>&1
echo "$(date +%T) charset $(head -1 ft4/old.lstm-unicharset) -> $(head -1 ft4/merged.unicharset); added: $(comm -13 <(tail -n +2 ft4/old.lstm-unicharset | cut -d' ' -f1 | sort) <(tail -n +2 ft4/merged.unicharset | cut -d' ' -f1 | sort) | tr '\n' ' '); words $(wc -l < ft4/words.txt)" >> chain4.log
# 4. lists: rare material is listed 3x so the new letters are seen often
ls train4/*.lstmf | sort > ft4/rare.txt; ls synth/*.lstmf | sort > ft4/synth.txt
awk 'NR%8==0' ft4/rare.txt > ft4/rare_eval.txt; awk 'NR%8!=0' ft4/rare.txt > ft4/rare_train.txt
cat ft3/train.txt ft4/rare_train.txt ft4/rare_train.txt ft4/rare_train.txt ft4/synth.txt ft4/synth.txt | shuf --random-source=<(yes) > ft4/train.txt
cat ft3/eval.txt ft4/rare_eval.txt > ft4/eval.txt
echo "round-3 model on eval (old + rare pages): $(lstmeval --model ft3/latin_chv_checkpoint --traineddata ft3/out/Latin/Latin.traineddata --eval_listfile ft4/eval.txt 2>&1 | grep -o 'BCER eval=[0-9.]*, BWER eval=[0-9.]*' | tail -1)" >> chain4.log
nice -n 10 lstmtraining --model_output ft4/latin_chv4 --continue_from ft3/latin_chv_checkpoint --old_traineddata ft3/out/Latin/Latin.traineddata \
  --traineddata ft4/out/Latin/Latin.traineddata --train_listfile ft4/train.txt --eval_listfile ft4/eval.txt \
  --max_iterations ${1:-9000} --learning_rate 0.0002 2>&1 | grep -E "^At iteration|Finished" | awk 'NR%10==0 || /Finished/' >> chain4.log
echo "round-4 model on eval: $(lstmeval --model ft4/latin_chv4_checkpoint --traineddata ft4/out/Latin/Latin.traineddata --eval_listfile ft4/eval.txt 2>&1 | grep -o 'BCER eval=[0-9.]*, BWER eval=[0-9.]*' | tail -1)" >> chain4.log
lstmtraining --stop_training --continue_from ft4/latin_chv4_checkpoint --traineddata ft4/out/Latin/Latin.traineddata --model_output ft4/latin_chv4.traineddata >/dev/null 2>&1
rm -rf tessdata_ft4 /opt/tessdata_ft4 && mkdir -p tessdata_ft4 && cp ft4/latin_chv4.traineddata tessdata_ft4/chv.traineddata && cp -r tessdata_best/configs tessdata_best/tessconfigs tessdata_ft4/
cp -r tessdata_ft4 /opt/tessdata_ft4 && chmod -R a+rX /opt/tessdata_ft4
echo "$(date +%T) training done" >> chain4.log
while IFS=$(printf "\t") read id pages chars name; do
  pdf=/var/www/chcemvediet/chcemvediet/media/$(awk -F"\t" -v r=$id '$1==r {print $3}' candidates.tsv)
  nice -n 10 python3 tesseract_odt.py --tessdata /opt/tessdata_ft4 --lang chv --txt work/$id/tess.ft4.txt "$pdf" work/$id/ft4.odt >/dev/null 2>&1 || echo "$id FAILED" >> chain4.log
done < sample.tsv
echo "$(date +%T) CHAIN4_DONE" >> chain4.log
