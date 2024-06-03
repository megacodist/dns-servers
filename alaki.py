#
# 
#


def GetInterface() -> tuple:
    import subprocess
    cmpl = subprocess.run(
        ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
        capture_output=True,
        text=True,
        check=True,)
    lines = cmpl.stdout.splitlines()
    lines = [line for line in lines if line.strip()]
    if lines[1].split(' -'):
        raise TypeError('Cannot detect dashed line.')
    names = lines[0].s


def main() -> None:
    from pprint import pprint
    import subprocess
    cmpl = subprocess.run(
        ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
        capture_output=True,
        text=True,
        check=True,)
    temp = cmpl.stdout.splitlines()
    result = [line.strip().split() for line in temp]
    pprint(result)


if __name__ == '__main__':
    main()
