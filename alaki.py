#
# 
#

from collections import namedtuple
import re
from urllib.parse import ParseResult



def main() -> None:
    with open(r'h:/alaki.txt', mode='rt') as fileObj:
        names = fileObj.read()
    names = [name.lower() for name in names.splitlines()]
    lsNames = list(set(names))
    lsNames.sort()
    print(repr(lsNames))
    input()


if __name__ == '__main__':
    main()
