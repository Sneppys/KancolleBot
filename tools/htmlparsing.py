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


def get_images_on_wiki_page(ship_name):
    ship_name = ship_name.replace(' ', '_')
    page = urllib.request.urlopen("http://kancolle.wikia.com/wiki/%s" % ship_name)

    parser = KCImageParser("Full")
    parser.feed(str(page.read()))
    parser.close()

    return parser.imgs
