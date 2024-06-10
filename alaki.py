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

def main2():
    import subprocess
    output = subprocess.check_output(["systemd-resolve", "query", "-t", "nameserver"]).decode("utf-8")
    print(output)


if __name__ == '__main__':
    main2()
