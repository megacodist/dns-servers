#
# 
#



def main() -> None:
    from urllib.parse import urlparse, urlunparse
    try:
        while True:
            sUrl = input('Enter a URL: ')
            urlObj = urlparse(sUrl if '://' in sUrl else 'https://' + sUrl)
            print('URL parts ======================')
            print('Scheme:', urlObj.scheme)
            print('Username:', urlObj.username)
            print('Password:', urlObj.password)
            print('Host:', urlObj.hostname)
            print('Port:', urlObj.port)
            print('Path:', urlObj.path)
            print('Params:', urlObj.params)
            print('Fragment:', urlObj.fragment)
            print(urlunparse(urlObj))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
