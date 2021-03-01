from functools import reduce
from typing import List

from m2data.correction import Correction
from m2data.token_alignments import TokenAlignments


class Example:
    __slots__ = ['original', 'corrections', '_corrected_form', 'raw']

    def __init__(self, original_line: str, correction_lines: List[str]):
        self.original = original_line[2:]
        self.corrections = [Correction(line) for line in correction_lines]
        self._corrected_form = None
        self.raw = '\n'.join(x.strip() for x in [original_line] + correction_lines)

    def to_json(self, include_corrected_form: bool = True,
                include_raw: bool = False, include_raw_corrections: bool = False):
        json = {s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)
                and (s != 'raw' or include_raw)}

        if include_corrected_form and self._corrected_form is None:
            json['_corrected_form'] = self.get_corrected_form()
        json['corrections'] = [cor.to_json(include_raw_line=include_raw_corrections) for cor in json['corrections']]
        return json

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str({s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)})

    def get_corrections(self, correction_type: str = None, correction_subtype: str = None,
                        correction_operation: str = None) -> List[Correction]:
        return [c for c in self.corrections if (correction_type is None or c.type == correction_type)
                and (correction_subtype is None or c.subtype == correction_subtype)
                and (correction_operation is None or c.operation == correction_operation)]

    def has_correction(self, correction_type: str = None, correction_subtype: str = None,
                       correction_operation: str = None) -> bool:
        return len(self.get_corrections(correction_type, correction_subtype, correction_operation)) > 0

    def is_noop(self) -> bool:  # also true if corrections is empty, conveniently
        return len(self.get_corrections(correction_type=Correction.NOOP)) == len(self.corrections)

    # TODO: compare against https://www.cl.cam.ac.uk/research/nl/bea2019st/data/corr_from_m2.py
    # and make sure we're not doing anything wrong, like applying edits from multiple annotators
    # corrections are applied in reverse order (right to left) so as not to invalidate the indices of other corrections
    def get_corrected_form(self) -> str:
        if self._corrected_form is None:
            self._corrected_form = ' '.join(reduce(lambda x, y: y.apply_to_tokenlist(x), reversed(self.corrections),
                                                   self.original.split()))

        return self._corrected_form

    def get_corrected_token_alignments(self) -> TokenAlignments:
        token_offset = 0
        alignments = TokenAlignments()
        for correction in self.corrections:
            if correction.operation == Correction.MISSING:
                content_length = len(correction.content.split())
                assert(content_length > 0)
                for i in range(content_length):
                    original = None
                    new = correction.start + token_offset + i
                    alignments.correction_alignments[new] = original
                token_offset += content_length
                alignments.add_correction_alignment(new, original, token_offset)
            elif correction.operation == Correction.REPLACE:
                content_length = len(correction.content.split())
                assert(content_length > 0)
                for i in range(content_length):
                    new = correction.start + token_offset + i
                    if correction.start + i < correction.end:
                        original = correction.start + i
                    else:
                        original = correction.end - 1
                    alignments.correction_alignments[new] = range(original, original + 1)

                correction_length = correction.end - correction.start
                token_offset += content_length - correction_length
                if content_length < correction_length:  # we're replacing a longer tokenstring with a shorter one
                    alignments.add_correction_alignment(new, range(original, original + 1 + (correction_length - content_length)), token_offset)
                else:
                    alignments.add_correction_alignment(new, range(original, original + 1), token_offset)
                pass
            elif correction.operation == Correction.UNNECESSARY:
                token_offset -= (correction.end - correction.start)
                alignments.offset_thresholds[correction.start] = token_offset

        return alignments