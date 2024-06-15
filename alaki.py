#
# 
#



def main() -> None:
    from urllib.parse import urlparse, urlunparse
    url = urlparse(input('Enter a URL: '), scheme='https')
    sUrl = urlunparse(url)
    print(urlparse(sUrl))


if __name__ == '__main__':
    main()
