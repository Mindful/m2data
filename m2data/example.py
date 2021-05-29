from functools import reduce
from typing import List, FrozenSet, Optional, Dict, Iterable

from m2data.correction import Correction
from m2data.token_alignments import TokenAlignments


class Example:
    """Represents a single sentence with corrections"""
    __slots__ = ['original', 'corrections']

    def __init__(self, original_line: str, correction_lines: List[str]):
        self.original = original_line[2:]
        self.corrections = sorted((Correction(line) for line in correction_lines), key=lambda c: c.start)

    def get_raw_sentence_line(self):
        return 'S ' + self.original

    def get_full_raw(self):
        return '\n'.join([self.get_raw_sentence_line()] + [c.raw_line for c in self.corrections])

    def to_json(self, all_corrected_forms: bool = False, include_full_raw: bool = False,
                include_raw_corrections: bool = False, annotator_id: int = 0) -> Dict:
        json = {s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)}

        if include_full_raw:
            json['raw'] = self.get_full_raw()

        if all_corrected_forms:
            json['corrected'] = [self.get_corrected_form(annotator_id) for annotator_id in self.get_annotator_ids()]
        else:
            json['corrected'] = self.get_corrected_form(annotator_id)

        json['corrections'] = [cor.to_json(include_raw_line=include_raw_corrections) for cor in json['corrections']]
        return json

    def json_per_annotator(self, all_corrected_forms: bool = False, include_full_raw: bool = False,
                           include_raw_corrections: bool = False) -> Iterable[Dict]:
        for annotator_id in self.get_annotator_ids():
            yield self.to_json(all_corrected_forms=all_corrected_forms, include_full_raw=include_full_raw,
                               include_raw_corrections=include_raw_corrections, annotator_id=annotator_id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str({s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)})

    def get_corrections(self, correction_type: str = None, correction_subtype: str = None,
                        correction_operation: str = None,
                        annotator_ids: Optional[FrozenSet[int]] = None,
                        include_ignored_types: bool = False) -> List[Correction]:
        """

        :param correction_type: Return only corrections of this type
        :param correction_subtype: Return only corrections of this subtype
        :param correction_operation: Return only corrections which perform this operation (insert/delete/replace)
        :param annotator_ids: Return only corrections made by annotators with IDs in this set
        :param include_ignored_types: Whether to include NOOP/UNK/UM correction types
        :return: a list containing corrections for this Example
        """

        return [c for c in self.corrections if (correction_type is None or c.type == correction_type)
                and (correction_subtype is None or c.subtype == correction_subtype)
                and (correction_operation is None or c.operation == correction_operation)
                and (annotator_ids is None or c.annotator in annotator_ids)
                and (include_ignored_types or c.type not in Correction.IGNORED_TYPES)]

    def has_correction(self, correction_type: str = None, correction_subtype: str = None,
                       correction_operation: str = None, annotator_ids: Optional[FrozenSet[int]] = None) -> bool:
        return len(self.get_corrections(correction_type, correction_subtype, correction_operation, annotator_ids)) > 0

    def is_noop(self, compare_corrected_form: bool = False) -> bool:
        """Whether the correction is a no-op. By default, this just looks at whether meaningful corrections are present,
        but if compare_corrected_form is set to True it will compare the original string. The result should be the same
        as long as correction content is sane, but if your data contains corrections that replace words with identical
        content, they will only be marked as no-op with compare_corrected_form set to True."""
        if compare_corrected_form:
            return self.original == self.get_corrected_form()
        else:
            # this is also true if corrections is empty, conveniently
            return len(self.get_corrections(correction_type=Correction.NOOP, include_ignored_types=True))\
               == len(self.corrections)

    def get_corrected_form(self, annotator_id: int = 0) -> str:
        if len(self.get_annotator_ids()) > 0 and annotator_id not in self.get_annotator_ids():
            raise RuntimeError('Invalid annotator ID')
        # simplified from https://www.cl.cam.ac.uk/research/nl/bea2019st/data/corr_from_m2.py
        # apply corrections in reverse to avoid having to deal with offsets
        return ' '.join(reduce(lambda x, y: y.apply_to_tokenlist(x),
                               reversed([c for c in self.corrections if c.annotator == annotator_id]),
                               self.original.split()))

    def get_annotator_ids(self) -> FrozenSet[int]:
        return frozenset(c.annotator for c in self.corrections)

    def get_corrected_token_alignments(self) -> TokenAlignments:
        """Make a best effort to get corrected token alignments. This is fundamentally subjective in some cases, so
        if you need specific behavior for edge cases it's recommended that you use your own implementation. This method
        should be sufficient for simple cases, however."""
        token_offset = 0
        alignments = TokenAlignments(len(self.get_corrected_form().split()))
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
