#
# 
#


class Foo:
    def __init__(self, a: int, b: int | None = None) -> None:
        self.a = a
        self.b = b


def main() -> None:
    import subprocess
    command = ['where', 'python']
    res = subprocess.Popen(command, encoding='utf-8')
    print(res.stdout)


if __name__ == '__main__':
    main()
