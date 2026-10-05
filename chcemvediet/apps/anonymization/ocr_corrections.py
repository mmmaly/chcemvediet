# vim: expandtab
# -*- coding: utf-8 -*-
u"""
Corrections of Slovak words with the rare letters "ĺ" and "ŕ" in OCR output.

Our Tesseract model reads these two letters unreliably ("predlžiť" for "predĺžiť", "zahĺňať" for
"zahŕňať"), and training it harder made it see them in place of "ť", "ľ", "ž" and "Í". The
misreadings of the common word families are regular and are not Slovak words themselves, so they
are fixed here with a few explicit rules. A rule is listed only if its wrong form cannot be a
real word: e.g. there is no rule for "krb"/"kĺb" or "strp-"/"stŕp-".
"""
import re

# (pattern with the misread letter in group 2, correct letter)
_RULES = [
    # spĺňať, dopĺňať, vypĺňať, napĺňať, zapĺňať ("výplň", "náplňou" are not touched: no "a" follows)
    (r'\b((?:ne)?(?:s|do|vy|na|za)p)([lrŕ])(?=ňa)', u'ĺ'),
    # zahŕňať, zhŕňať, ohŕňať, vyhŕňať ("zahrň", "zahrňte" are not touched)
    (r'\b((?:ne)?(?:za|z|o|vy)h)([rlĺf])(?=ňa)', u'ŕ'),
    # dĺžka ("dlžník", "dlžoba" are not touched)
    (r'\b(d)([lrŕ])(?=žk)', u'ĺ'),
    # bŕzd (genitive plural of "brzda"); "ĺ" can not be right here
    (r'\b(b)(ĺ)(?=zd\b)', u'ŕ'),
]
# Rules whose wrong form has no diacritics: not applied inside file names, addresses and other
# compound tokens, which are often written without diacritics on purpose.
_PLAIN_RULES = [
    # stĺp, stĺpec ("strpieť" and "stŕpnuť" are not touched)
    (r'\b(st)(l)(?=p)', u'ĺ'),
    # hĺbka ("hlboký" is not touched)
    (r'\b(h)(l)(?=bk)', u'ĺ'),
    # zdĺhavý
    (r'\b(zd)(l)(?=hav)', u'ĺ'),
    # mŕtvy
    (r'\b(m)(r)(?=tv)', u'ŕ'),
]
_FLAGS = re.IGNORECASE | re.UNICODE
_RULES = [(re.compile(p, _FLAGS), c) for p, c in _RULES]
_PLAIN_RULES = [(re.compile(p, _FLAGS), c) for p, c in _PLAIN_RULES]
_POZDLZ = (re.compile(r'\b(pozd)(l)(?=ž)', _FLAGS), u'ĺ')
_COMPOUND = re.compile(r'[_/@\\-]|\.\w')

# "predĺžiť/predĺženie" (to extend) versus "predlžiť/predlženie" (to over-indebt): both are real
# words, so this is corrected only if the line speaks about a time limit or a contract. The
# imperfective "predlžovať/predlžuje" is spelled without "ĺ" and is never touched.
_PREDLZ = re.compile(u'\\b(pred)([lí])(?=ž(?!ov|uj))', _FLAGS)
_PREDLZ_CONTEXT = re.compile(u'lehot|termín|platnos|zmluv|nájm|dob[auy]\\b|\\bdní\\b|\\bdni\\b', _FLAGS)


def _replace(match, letter):
    wrong = match.group(2)
    upper = wrong.isupper() or (match.group(1)[-1:].isupper() and len(match.group(1)) > 1)
    return match.group(1) + (letter.upper() if upper else letter)

def _apply(rules, text):
    for pattern, letter in rules:
        text = pattern.sub(lambda m: _replace(m, letter), text)
    return text

def correct_line(text):
    u"""Returns ``text`` (one line of OCR output) with the known misreadings of "ĺ"/"ŕ" fixed."""
    predlz = bool(_PREDLZ_CONTEXT.search(text))
    tokens = re.split(r'(\s+)', text)
    for i, token in enumerate(tokens):
        if not token or token.isspace():
            continue
        token = _apply(_RULES + [_POZDLZ], token)
        if not _COMPOUND.search(token):
            token = _apply(_PLAIN_RULES, token)
        if predlz:
            token = _PREDLZ.sub(lambda m: _replace(m, u'ĺ'), token)
        tokens[i] = token
    return u''.join(tokens)
