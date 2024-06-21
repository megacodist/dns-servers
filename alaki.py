#
# 
#

from collections import namedtuple
import re
from urllib.parse import ParseResult


def floatToEngineering(num: float, precision=3) -> str:
    """Converts a float number to its engineering representation. It raises
    `ValueError` if prefix is smaller or larger that support.
    """
    from decimal import Decimal
    # Defining scientific prefixes and their corresponding powers of 10
    prefixes = {
        24: 'yotta',
        21: 'zetta',
        18: 'exa',
        15: 'peta',
        12: 'tera',
        9: 'giga',
        6: 'mega',
        3: 'kilo',
        0: '',
        -3: 'milli',
        -6: 'micro',
        -9: 'nano',
        -12: 'pico',
        -15: 'femto',
        -18: 'atto',
        -21: 'zepto',
        -24: 'yocto',}
    # Converting the number to a string in scientific notation
    sciNotation = f"{num:.2e}"
    # Spliting the scientific notation into the coefficient and the exponent
    coeff, exponent = sciNotation.split('e')
    exponent = int(exponent)
    #
    a = exponent % 3
    try:
        prefix = prefixes[exponent - a]
    except KeyError:
        raise ValueError(f'no prefix for {exponent - a}')
    n = Decimal(coeff) * (10 ** a)
    return f'{float(n)} {prefix}'


def main() -> None:
    try:
        while True:
            a = float(input('Enter a number: '))
            print(floatToEngineering(a))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
