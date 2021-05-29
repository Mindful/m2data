from itertools import takewhile, repeat
from typing import Iterable, Union
from collections.abc import Sized

from m2data.example import Example


# this is sometimes off by an example or two for very large files, but that probably doesn't matter much
def fast_example_count(filename) -> int:
    f = open(filename, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
    return sum(buf.count(b'\nS ') for buf in bufgen) + 1  # no linebreak for first example


class M2ReaderException(Exception):
    def __init__(self, text: str):
        super().__init__(text)


class Reader:
    """Returns an Example object for each sentence with corrections in an .m2 file. """
    def __init__(self, input_data: Union[Iterable[str], str], progress_bar: bool = False):
        """
        :param input_data: the filename of an .m2 file to read in, or an iterable of lines as read from an .m2 file
        :param progress_bar: whether or not to display a progress bar for reading the file. Requires tqdm if True
        """
        self.progress_bar = progress_bar

        if self.progress_bar:
            try:
                from tqdm import tqdm
                self.tqdm = tqdm
            except ModuleNotFoundError:
                print("Warning: progress bar requires tqdm, which was not found. Proceeding without progress bar")
                self.progress_bar = False

        if isinstance(input_data, str):
            self.input_file = open(input_data, 'r')
            if self.progress_bar:
                self.total_examples = fast_example_count(input_data)
                self.desc = 'reading examples from {}'.format(input_data)

            self.input_gen = (line for line in (line.strip() for line in self.input_file) if line)

        elif isinstance(input_data, Iterable):
            if self.progress_bar:
                if isinstance(input_data, Sized):
                    self.total_examples = len(input_data)
                    self.desc = 'reading examples from input'
                else:
                    self.progress_bar = False
                    print('Warning: Progress bar requires that input is a filename or iterable with length. Proceeding'
                          'without progress bar.')

            self.input_gen = (line for line in (line.strip() for line in input_data) if line)

        else:
            raise TypeError('Input to reader must be either a string filename or an iterable of lines as strings')

    def __iter__(self) -> Iterable[Example]:
        if self.progress_bar:
            progress_bar = self.tqdm(total=self.total_examples, desc=self.desc)

        original_content_line = None
        correction_lines = None
        for line in self.input_gen:
            if line[0] == 'S':
                if original_content_line:  # we've hit the start of a new example, yield the last one
                    progress_bar.update(1) if self.progress_bar else None
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
        progress_bar.update(1) if self.progress_bar else None

        if self.progress_bar:
            progress_bar.close()
        if hasattr(self, 'input_file'):
            self.input_file.close()

    def __del__(self):
        if hasattr(self, 'input_file'):
            self.input_file.close()