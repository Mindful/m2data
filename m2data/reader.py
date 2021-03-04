from typing import Iterable

from m2data.example import Example


class M2ReaderException(Exception):
    def __init__(self, text: str):
        super().__init__(text)


class Reader:
    def __init__(self, raw_lines: Iterable[str]):
        self.input_gen = (line for line in (line.strip() for line in raw_lines) if line)

    def __iter__(self) -> Iterable[Example]:
        original_content_line = None
        correction_lines = None
        for line in self.input_gen:
            if line[0] == 'S':
                if original_content_line:  # we've hit the start of a new example, yield the last one
                    yield Example(original_content_line, correction_lines)
                original_content_line = line
                correction_lines = []
            else:
                if line[0] != 'A':
                    raise M2ReaderException('Nonempty lines in .m2 files must start with "A" or "S".'
                                            'Found violating line: "{}"'.format(line))
                if correction_lines is None:
                    raise M2ReaderException('Encountered an edit line ("A") before an original sentence line ("S")')
                correction_lines.append(line)

        yield Example(original_content_line, correction_lines)