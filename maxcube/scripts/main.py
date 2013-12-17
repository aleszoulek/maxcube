#!/usr/bin/env python3

import sys

from maxcube import parsing
from maxcube import output
from maxcube import network


def main():
    raw_data = network.read_raw_data(sys.argv[1], int(sys.argv[2]))
    output.display(
        parsing.start(raw_data)
    )


if __name__ == '__main__':
    main()
