from common_crawl.base import CommonCrawlJob

from bs4 import BeautifulSoup, SoupStrainer

class CSSSelectJob(CommonCrawlJob):
    def configure_options(self):
        super(CSSSelectJob, self).configure_options()
        self.add_passthrough_option('--selector', action='append')

    def mapper_init(self):
        if not self.options.selector:
            # Fail early if no valid extensions are supplied
            raise ValueError("Must specify at least one selector")

        self.strainer = SoupStrainer(self.options.selector) 

    def parse_content(self, content):
        # html.parser makes no attempt to make the document valid HTML
        return BeautifulSoup(content, 'html.parser', parse_only=self.strainer)

    def process_html(self, url, headers, content, soup):
        if not soup.find_next():
            return

        yield url, content

if __name__ == '__main__':
    CSSSelectJob.run() 
