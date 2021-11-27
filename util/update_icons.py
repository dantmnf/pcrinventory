from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import httpx
import os
import config

class IconIndexParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = []
    def handle_starttag(self, tag, attrs):
        attrdict = dict(attrs)
        if tag == 'span' and attrdict.get('class') == 'item' and 'data-search' in attrdict:
            self.data.append(attrdict['data-search'])

def download_icon(client: httpx.Client, filename):
    url = 'https://redive.estertion.win/icon/equipment/' + filename
    path = os.path.join(config.resource_root, 'imgreco', 'inventory', 'icons', filename)
    if os.path.exists(path) or os.path.exists(path.removesuffix('.webp') + '.png'):
        print(filename, 'exists')
        return
    print("downloading", url)
    with client.stream("GET", url, follow_redirects=True) as response:
        with open(path, 'wb') as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

def main():
    client = httpx.Client()
    index = httpx.get('https://redive.estertion.win/icon/equipment/', follow_redirects=True)
    parser = IconIndexParser()
    parser.feed(index.text)
    print(parser.data)
    pool = ThreadPoolExecutor(max_workers=4)
    for filename in parser.data:
        if filename.startswith('13'):
            continue
        pool.submit(download_icon, client, filename)
    pool.shutdown(wait=True)

if __name__ == '__main__':
    main()
