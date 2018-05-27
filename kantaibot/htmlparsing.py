"""Handles HTML web calls and parsing."""
from html.parser import HTMLParser
import urllib.request


class KCImageParser(HTMLParser):
    """A HTMLParser for the kancolle wiki."""

    def __init__(self, searchtype):
        """Initialize the parser.

        Parameters
        ----------
        searchtype : str
            The type of image to look for.
            The type is in the name of the image.
        """
        self.searchtype = searchtype
        self.imgs = {}
        super(KCImageParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        """Handle the start of a new tag."""
        if (tag == 'img'):
            for a, v in attrs:
                if (a == "alt" and self.searchtype in v):
                    urls = [y for x, y in attrs if x == 'data-src']
                    if (len(urls) > 0):
                        self.imgs[v] = urls[0]
                    break

    def handle_endtag(self, tag):
        """Handle the end of a tag."""
        pass

    def handle_data(self, data):
        """Handle the inside of a tag."""
        pass


def get_images_on_wiki_page(url):
    """Get all the images on the given wiki page.

    Returns
    -------
    dict
        Dictionary of all images, key being image name, value being URL.
    """
    print("Sending request to '%s'" % url)
    page = urllib.request.urlopen(url)

    parser = KCImageParser("Full")
    page_data = page.read().decode('utf-8')
    parser.feed(str(page_data))
    parser.close()
    print("Request success")

    return parser.imgs
