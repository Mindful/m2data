from unittest import TestCase
from m2data import Example, Correction
import re


class TestExample(TestCase):
    # test only with publically available data (W&I+LOCNESS / FCE) and/or homemade data

    raw_line_cleaner = re.compile(r'(?<=\n)\s+')

    raw_example_1 = '''
    S The rich people will buy a car but the poor people always need to use a bus or taxi .
    A 0 2|||U:DET|||Rich|||REQUIRED|||-NONE-|||0
    A 7 7|||M:PUNCT|||,|||REQUIRED|||-NONE-|||0
    A 8 9|||U:DET||||||REQUIRED|||-NONE-|||0
    '''

    raw_example_2 = '''
    S Depending on the distance and duration to the desired place , mode of transport is chosen accordingly .
    A 5 6|||R:NOUN|||time|||REQUIRED|||-NONE-|||0
    A 9 10|||R:NOUN|||destination|||REQUIRED|||-NONE-|||0
    A 9 10|||R:NOUN|||location|||REQUIRED|||-NONE-|||0
    A 11 11|||M:DET|||the|||REQUIRED|||-NONE-|||0
    A 11 11|||M:DET|||a|||REQUIRED|||-NONE-|||1
    '''

    raw_example_3 = '''
    S This reminds me of a trip that I have recently been to and the place is Agra .
    A 11 12|||R:PREP|||on|||REQUIRED|||-NONE-|||0
    A 15 15|||M:OTHER|||I visited|||REQUIRED|||-NONE-|||0
    A 15 16|||R:VERB:TENSE|||was|||REQUIRED|||-NONE-|||0
    '''

    @staticmethod
    def _clean_raw_lines(raw_lines: str):
        return TestExample.raw_line_cleaner.sub('', raw_lines).strip()

    @staticmethod
    def _sentence_and_correction_lines(raw_lines: str):
        line_list = [line.strip() for line in raw_lines.split('\n') if line.strip()]
        return line_list[0], line_list[1:]

    def test_basic_methods(self):
        e1 = Example(*self._sentence_and_correction_lines(self.raw_example_1))
        self.assertEqual(3, len(e1.corrections))
        self.assertEqual('The rich people will buy a car but the poor people always need to use a bus or taxi .',
                         e1.original)
        self.assertEqual(False, e1.is_noop())
        self.assertEqual(frozenset([0]), e1.get_annotator_ids())
        self.assertEqual(self._clean_raw_lines(self.raw_example_1), e1.get_full_raw())

        e2 = Example(*self._sentence_and_correction_lines(self.raw_example_2))
        self.assertEqual(5, len(e2.corrections))
        self.assertEqual('Depending on the distance and duration to the desired place , mode'
                         ' of transport is chosen accordingly .', e2.original)
        self.assertEqual(False, e2.is_noop())
        self.assertEqual(frozenset([0, 1]), e2.get_annotator_ids())
        self.assertEqual(self._clean_raw_lines(self.raw_example_2), e2.get_full_raw())

        e3 = Example('S This is a no - op .', [])
        self.assertEqual(True, e3.is_noop())
        self.assertEqual(frozenset([]), e3.get_annotator_ids())

        e4 = Example('S This is also a no - op .', ['A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0'])
        self.assertEqual(True, e4.is_noop())
        self.assertEqual(frozenset([0]), e4.get_annotator_ids())

    def test_corrections(self):
        e1 = Example(*self._sentence_and_correction_lines(self.raw_example_1))
        self.assertEqual(len(e1.get_corrections()), len(e1.corrections))
        self.assertEqual(len(e1.get_corrections(correction_operation=Correction.UNNECESSARY)), 2)
        self.assertEqual(len(e1.get_corrections(correction_type='DET')), 2)
        self.assertEqual(len(e1.get_corrections(correction_type='VERB')), 0)
        self.assertEqual(True, e1.has_correction(correction_type='PUNCT'))
        self.assertEqual(False, e1.has_correction(correction_type='VERB'))
        self.assertEqual('Rich people will buy a car , but poor people always need to use a bus or taxi .',
                         e1.get_corrected_form())
        pass

    def test_to_json(self):
        pass

    def test_token_alignments(self):
        pass



