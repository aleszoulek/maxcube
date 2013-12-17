#!/usr/bin/env python3

import sys

from maxcube import parsing
from maxcube import output


def main():
    output.display(
        parsing.start(sys.argv[1], sys.argv[2])
    )


if __name__ == '__main__':
    main()
