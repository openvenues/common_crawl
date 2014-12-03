from common_crawl.base import CommonCrawlJob

from bs4 import BeautifulSoup, SoupStrainer

only_a_tags = SoupStrainer("a")

def parse_file_ext_from_url(url):
    parsed = urlparse.urlparse(url)
    last_path = parsed.path.split('/', 1)[-1]
    if '.' in last_path:
        extension = last_path.split('.')[-1].strip()
        if extension:
            return extension
    return None

class RegexURLJob(CommonCrawlJob):
    OUTPUT_PROTOCOL = RawValueProtocol
    def configure_options(self):
        super(RegexURLJob, self).configure_options()
        self.add_passthrough_option('--pattern')
        self.add_passthrough_option('--insensitive', default=None)
        self.add_passthrough_option('--exact', default=None)

    def mapper_init(self):
        if not self.options.pattern:
            # Fail early if no valid extensions are supplied
            raise ValueError("Must specify regex pattern")
 
        regex_flags = re.I if self.options.insensitive is not None else None
        self.link_pattern = re.compile(self.options.pattern, regex_flags)
        self.exact = self.options.exact is not None
        self.match_func = self.link_pattern.search if not self.exact else self.link_pattern.match

    def mapper(self, record):
        url = record.url
        if self.match_func(url):
            yield url

if __name__ == '__main__':
    RegexURLJob.run() 
