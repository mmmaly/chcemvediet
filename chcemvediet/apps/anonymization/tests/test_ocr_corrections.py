from django.test import TestCase

from chcemvediet.apps.anonymization.ocr_corrections import correct_line


class OcrCorrectionsTest(TestCase):
    u"""
    Tests ``correct_line()``: fixes of misread "ĺ"/"ŕ" in OCR output.
    """

    def test_misread_words_are_fixed(self):
        tests = [
            (u'zahĺňať aj zahrňa a zahfňa', u'zahŕňať aj zahŕňa a zahŕňa'),
            (u'doplňanie, naplňame, splňa, nesplňajú', u'dopĺňanie, napĺňame, spĺňa, nespĺňajú'),
            (u'dlžka stlpca v hlbke', u'dĺžka stĺpca v hĺbke'),
            (u'zdlhavý proces pozdlž cesty, mrtvy bod, bĺzd', u'zdĺhavý proces pozdĺž cesty, mŕtvy bod, bŕzd'),
            (u'SPLŇA DLŽKA Stlp ZAHRŇA', u'SPĹŇA DĹŽKA Stĺp ZAHŔŇA'),
        ]
        for text, expected in tests:
            self.assertEqual(correct_line(text), expected)

    def test_real_words_are_kept(self):
        for text in [
                u'zahrňte a zahrnúť, výplň a náplňou, splniť a splnenie',
                u'dlžník a dlžoba, strpieť, stŕpnuť, hlboký, krb, vrba, brzda',
                u'spĺňa zahŕňa dĺžka stĺp predĺženie lehoty',
                u'MINISTERSTVO INVESTÍCIÍ, miestnosť, Požiadavky, Katerina',
                u'lehota sa predlžuje, lehotu predlžujeme, predlžovanie lehoty',
                u'subor poskodene-stlpiky.pdf, stlpiky_2.jpg, www.mrtvy.sk/hlbka',
                ]:
            self.assertEqual(correct_line(text), text)

    def test_predlzenie_is_fixed_only_in_context_of_a_time_limit(self):
        self.assertEqual(correct_line(u'Oznámenie o predlžení lehoty'), u'Oznámenie o predĺžení lehoty')
        self.assertEqual(correct_line(u'predížiť zmluvu o 8 dní'), u'predĺžiť zmluvu o 8 dní')
        self.assertEqual(correct_line(u'hrozí predlženie spoločnosti'), u'hrozí predlženie spoločnosti')
