from typing import List


class Correction:
    """Represents a single correction, or one correction line in an .m2 file"""
    __slots__ = ['start', 'end', 'content', 'operation', 'type', 'subtype', 'raw_line', 'annotator']

    REPLACE = 'R'
    MISSING = 'M'
    UNNECESSARY = 'U'
    UNK = 'UNK'
    UM = 'Um'  # also means unknown
    NOOP = 'noop'
    DELIMITER = '|||'
    OPERATIONS = {
        MISSING: 'missing something', UNNECESSARY: 'unnecessary', REPLACE: 'to be replaced',
        UNK: 'unknown', NOOP: 'noop'
    }

    IGNORED_TYPES = {NOOP, UNK, UM}

    def to_json(self, include_raw_line: bool = False):
        return {s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)
                and (s != 'raw_line' or include_raw_line)}

    def __repr__(self):
        return str(self.to_json())

    def __str__(self):
        return self.raw_line

    def __init__(self, correction_line: str):
        self.raw_line = correction_line
        start_end, correction_type, content, _, _, annotator = self.raw_line[2:].split(Correction.DELIMITER)
        start, end = start_end.split()
        self.start = int(start)
        self.end = int(end)
        self.annotator = int(annotator)
        self.content = content
        if correction_type == self.NOOP:
            self.operation, self.type, self.subtype = Correction.NOOP, Correction.NOOP, None
            self.content = None
        elif correction_type in [self.UM, self.UNK]:
            self.operation, self.type = Correction.UNK, Correction.UNK
            self.subtype = None
        else:
            correction_metadata = correction_type.split(':')
            if len(correction_metadata) == 3:
                self.operation, self.type, self.subtype = correction_metadata
            else:
                self.operation, self.type = correction_metadata
                self.subtype = None

    def apply_to_tokenlist(self, token_list: List[str]) -> List[str]:
        # must either only apply one correction, or apply these starting from the end of the sentence, since
        # token offsets change if preceding corrections are applied
        if self.operation not in self.IGNORED_TYPES:
            token_list[self.start:self.end] = self.content.split()

        return token_list
