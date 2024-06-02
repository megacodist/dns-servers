#
# 
#


def main() -> None:
    from utils.app import AppSettings
    aa = AppSettings()
    print(aa._GetClassAttrsName())


if __name__ == '__main__':
    main()
