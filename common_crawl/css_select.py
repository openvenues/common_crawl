from common_crawl.base import CommonCrawlJob

from bs4 import BeautifulSoup, SoupStrainer
from itertools import imap


class CSSSelectJob(CommonCrawlJob):
    strainer = None

    def configure_options(self):
        super(CSSSelectJob, self).configure_options()
        self.add_passthrough_option('--selector', action='append',
                                    help='One or more css selectors')
        self.add_passthrough_option('--parse-only', action='append',
                                    help='List of tags *for faster parsing)')

    def mapper_init(self):
        if not self.options.selector:
            # Fail early if no valid extensions are supplied
            raise ValueError("Must specify at least one selector")

        self.selectors = self.options.selector

        if self.options.parse_only:
            self.strainer = SoupStrainer(self.options.selector)

    def parse_content(self, content):
        # html.parser makes no attempt to make the document valid HTML
        return BeautifulSoup(content, 'html.parser', parse_only=self.strainer)

    def process_html(self, url, headers, content, soup):
        if not any(imap(soup.select, self.selectors)):
            return

        yield url, content

if __name__ == '__main__':
    CSSSelectJob.run()
