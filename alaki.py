#
# 
#



def main() -> None:
    import subprocess
    from ntwrk import readDnsInfo
    primary = '10.202.10.10'
    secondary = '10.202.10.11'
    interName = 'Wi-Fi'
    primary_command = f'netsh interface ip set dns "{interName}" static {primary}'
    res = subprocess.run(primary_command, shell=True, check=True, text=True)
    print(res.stdout)
    print('=' * 30)
    print(res.stderr)
    print(readDnsInfo(interName, {}))


if __name__ == '__main__':
    main()
