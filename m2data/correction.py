from typing import List


class Correction:
    __slots__ = ['start', 'end', 'content', 'operation', 'type', 'subtype', 'raw_line']

    REPLACE = 'R'
    MISSING = 'M'
    UNNECESSARY = 'U'
    UNK = 'UNK'
    NOOP = 'noop'
    DELIMITER = '|||'
    OPERATIONS = {
        MISSING: 'missing something', UNNECESSARY: 'unnecessary', REPLACE: 'to be replaced',
        UNK: 'unknown', NOOP: 'noop'
    }

    def to_json(self, include_raw_line: bool = False):
        return {s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)
                and (s != 'raw_line' or include_raw_line)}

    def _missing(self, token_list: List[str]) -> List[str]:
        # probably only makes sense if len(self.content.split()) == self.end - self.start, but that should be true
        token_list[self.start:self.start] = self.content.split()
        return token_list

    def _unnecessary(self, token_list: List[str]) -> List[str]:
        del token_list[self.start:self.end]
        return token_list

    def _replace(self, token_list: List[str]) -> List[str]:
        token_list[self.start:self.end] = self.content.split()
        return token_list

    def __init__(self, correction_line: str):
        self.raw_line = correction_line
        start_end, correction_type, content, _, _, _ = self.raw_line[2:].split(Correction.DELIMITER)
        start, end = start_end.split()
        self.start = int(start)
        self.end = int(end)
        self.content = content
        if correction_type == 'noop':
            self.operation, self.type, self.subtype = Correction.NOOP, Correction.NOOP, None
            self.content = None
        elif correction_type == 'UNK':
            self.operation, self.type = Correction.UNK, Correction.UNK
            self.subtype = None
        else:
            correction_metadata = correction_type.split(':')
            if len(correction_metadata) == 3:
                self.operation, self.type, self.subtype = correction_metadata
            else:
                self.operation, self.type = correction_metadata
                self.subtype = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '{} : {}'.format({'start': self.start, 'end': self.end, 'type': self.type,
                                 'subtype': self.subtype, 'operation': self.operation},
                                self.content)

    def apply_to_tokenlist(self, token_list: List[str]):
        if self.operation == Correction.MISSING:
            return self._missing(token_list)
        elif self.operation == Correction.UNNECESSARY:
            return self._unnecessary(token_list)
        elif self.operation == Correction.REPLACE:
            return self._replace(token_list)
        else:
            return token_list
