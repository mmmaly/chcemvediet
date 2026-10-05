#!/bin/bash
# Round 3: fine-tune the script/Latin model (has @ § & ...) on the page-level data; add missing chars.
cd /root/ocr-test
export TESSDATA_PREFIX=/root/ocr-test/tessdata_latin
rm -rf ft3 && mkdir -p ft3/out
combine_tessdata -u tessdata_latin/Latin.traineddata ft3/Latin. >/dev/null 2>&1
cat train2/*.gt.txt > ft3/all_gt.txt
unicharset_extractor --output_unicharset ft3/new.unicharset --norm_mode 2 ft3/all_gt.txt >/dev/null 2>&1
merge_unicharsets ft3/Latin.lstm-unicharset ft3/new.unicharset ft3/merged.unicharset >/dev/null 2>&1
dawg2wordlist ft3/Latin.lstm-unicharset ft3/Latin.lstm-word-dawg ft3/Latin.wordlist >/dev/null 2>&1
dawg2wordlist ft3/Latin.lstm-unicharset ft3/Latin.lstm-punc-dawg ft3/Latin.punc >/dev/null 2>&1
dawg2wordlist ft3/Latin.lstm-unicharset ft3/Latin.lstm-number-dawg ft3/Latin.numbers >/dev/null 2>&1
# Slovak words in addition to the script model's own list
cat ft3/Latin.wordlist ft2/slk.wordlist 2>/dev/null | sort -u > ft3/words.txt
combine_lang_model --input_unicharset ft3/merged.unicharset --script_dir langdata --words ft3/words.txt \
  --numbers ft3/Latin.numbers --puncs ft3/Latin.punc --output_dir ft3/out --lang Latin >/dev/null 2>&1
echo "$(date +%T) charset: $(head -1 ft3/Latin.lstm-unicharset) -> $(head -1 ft3/merged.unicharset); added: $(comm -13 <(tail -n +2 ft3/Latin.lstm-unicharset | cut -d' ' -f1 | sort) <(tail -n +2 ft3/merged.unicharset | cut -d' ' -f1 | sort) | tr '\n' ' ')" > chain3.log
ls train2/*.lstmf | sort > ft3/all.txt
awk 'NR%10==0' ft3/all.txt > ft3/eval.txt; awk 'NR%10!=0' ft3/all.txt > ft3/train.txt
echo "stock Latin on eval pages: $(lstmeval --model tessdata_latin/Latin.traineddata --eval_listfile ft3/eval.txt 2>&1 | grep -o 'BCER eval=[0-9.]*, BWER eval=[0-9.]*' | tail -1)" >> chain3.log
nice -n 10 lstmtraining --model_output ft3/latin_chv --continue_from ft3/Latin.lstm --old_traineddata tessdata_latin/Latin.traineddata \
  --traineddata ft3/out/Latin/Latin.traineddata --train_listfile ft3/train.txt --eval_listfile ft3/eval.txt \
  --max_iterations ${1:-10000} --learning_rate 0.0002 2>&1 | grep -E "^At iteration|Finished" | awk 'NR%10==0 || /Finished/' >> chain3.log
for c in ft3/latin_chv_checkpoint; do
  echo "$c on eval pages: $(lstmeval --model $c --traineddata ft3/out/Latin/Latin.traineddata --eval_listfile ft3/eval.txt 2>&1 | grep -o 'BCER eval=[0-9.]*, BWER eval=[0-9.]*' | tail -1)" >> chain3.log
done
lstmtraining --stop_training --continue_from ft3/latin_chv_checkpoint --traineddata ft3/out/Latin/Latin.traineddata --model_output ft3/latin_chv.traineddata >/dev/null 2>&1
rm -rf tessdata_ft3 /opt/tessdata_ft3 && mkdir -p tessdata_ft3 && cp ft3/latin_chv.traineddata tessdata_ft3/chv.traineddata && cp -r tessdata_best/configs tessdata_best/tessconfigs tessdata_ft3/
cp -r tessdata_ft3 /opt/tessdata_ft3 && chmod -R a+rX /opt/tessdata_ft3
echo "$(date +%T) training done" >> chain3.log
while IFS=$(printf "\t") read id pages chars name; do
  pdf=/var/www/chcemvediet/chcemvediet/media/$(awk -F"\t" -v r=$id '$1==r {print $3}' candidates.tsv)
  nice -n 10 python3 tesseract_odt.py --tessdata /opt/tessdata_ft3 --lang chv --txt work/$id/tess.ft3.txt "$pdf" work/$id/ft3.odt >/dev/null 2>&1 || echo "$id FAILED" >> chain3.log
done < sample.tsv
echo "$(date +%T) CHAIN3_DONE" >> chain3.log
