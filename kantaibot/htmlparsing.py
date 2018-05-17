from html.parser import HTMLParser
import urllib.request

class KCImageParser(HTMLParser):
    def __init__(self, searchtype):
        self.searchtype = searchtype
        self.imgs = {}
        super(KCImageParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if (tag == 'img'):
            for a, v in attrs:
                if (a == "alt" and self.searchtype in v):
                    urls = [y for x, y in attrs if x == 'data-src']
                    if (len(urls) > 0):
                        self.imgs[v] = urls[0]
                    break

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass


def get_images_on_wiki_page(url):
    print("Sending request to '%s'" % url)
    page = urllib.request.urlopen(url)

    parser = KCImageParser("Full")
    page_data = page.read().decode('utf-8')
    parser.feed(str(page_data))
    parser.close()
    print("Request success")

    return parser.imgs
