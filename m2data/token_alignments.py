from collections import defaultdict
from typing import Optional, Dict


# we store a lot of duplicate alignments here that could be more efficiently handled with a binary-tree like structure
# that just retained the locations where alignments changed, but it would be a lot of effort for minimal upside
class TokenAlignments:
    """
    Holds alignments from corrected to tokens to uncorrected tokens.
    If you want the opposite, call inverted().
    """
    def __init__(self, length: int):
        self.offset_thresholds: Dict[int, int] = {}
        self.correction_alignments: Dict[int, Optional[range]] = {}
        self.length = length
        super().__init__()

    def __len__(self):
        return self.length

    def __setitem__(self, new: int, original: Optional[range]):
        raise RuntimeError('Cannot directly set values, use add_correction_alignment()')

    def __contains__(self, item):
        return item in self.correction_alignments

    def __eq__(self, other):
        return isinstance(other, TokenAlignments) and self.offset_thresholds == other.offset_thresholds and \
               self.correction_alignments == other.correction_alignments

    def __getitem__(self, idx: int) -> Optional[range]:
        if idx >= self.length:
            raise IndexError('Token alignment index out of range')
        elif idx in self.correction_alignments:
            return self.correction_alignments[idx]
        else:
            possible_offset_thresholds = [key for key in self.offset_thresholds.keys() if key <= idx]
            if len(possible_offset_thresholds) > 0:
                offset_threshold = max(possible_offset_thresholds)
                offset = self.offset_thresholds[offset_threshold]
            else:
                offset = 0

            result = idx - offset
            return range(result, result+1)

    def add_correction_alignment(self, new: int, original: range, current_token_offset: int):
        self.correction_alignments[new] = original
        latest_offset = 0
        if len(self.offset_thresholds) > 0:
            latest_offset_threshold = max(self.offset_thresholds.keys())
            latest_offset = self.offset_thresholds[latest_offset_threshold]
        if current_token_offset != latest_offset:
            self.offset_thresholds[new] = current_token_offset

    def inverted(self) -> Dict:
        output = defaultdict(list)
        for idx in range(self.length):
            if self[idx] is not None:
                for corresponding_idx in self[idx]:
                    output[corresponding_idx].append(idx)

        output = {
            key: range(min(val), max(val)+1) for key, val in output.items()
        }

        new_length = max(output.keys())
        for idx in range(new_length):
            if idx not in output:
                output[idx] = None

        return output








