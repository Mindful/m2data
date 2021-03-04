from typing import Optional, Dict


# we store a lot of duplicate alignments here that could be more efficiently handled with a binary-tree like structure
# that just retained the locations where alignments changed, but it would be a lot of effort for minimal upside
class TokenAlignments:
    def __init__(self):
        self.offset_thresholds: Dict[int, int] = {}
        self.correction_alignments: Dict[int, Optional[range]] = {}
        super().__init__()

    def __setitem__(self, new: int, original: Optional[range]):
        raise RuntimeError('Cannot directly set values, use add_correction_alignment()')

    def __contains__(self, item):
        return item in self.correction_alignments

    def __eq__(self, other):
        return isinstance(other, TokenAlignments) and self.offset_thresholds == other.offset_thresholds and \
               self.correction_alignments == other.correction_alignments

    def __getitem__(self, new: int) -> Optional[range]:
        if new in self.correction_alignments:
            return self.correction_alignments[new]
        else:
            possible_offset_thresholds = [key for key in self.offset_thresholds.keys() if key <= new]
            if len(possible_offset_thresholds) > 0:
                offset_threshold = max(possible_offset_thresholds)
                offset = self.offset_thresholds[offset_threshold]
            else:
                offset = 0

            result = new - offset
            return range(result, result+1)

    def add_correction_alignment(self, new: int, original: range, current_token_offset: int):
        self.correction_alignments[new] = original
        latest_offset = 0
        if len(self.offset_thresholds) > 0:
            latest_offset_threshold = max(self.offset_thresholds.keys())
            latest_offset = self.offset_thresholds[latest_offset_threshold]
        if current_token_offset != latest_offset:
            self.offset_thresholds[new] = current_token_offset

