from common_crawl.base import CommonCrawlJob

from bs4 import BeautifulSoup, SoupStrainer

only_a_tags = SoupStrainer("a")

class RegexLinksJob(CommonCrawlJob):
    def configure_options(self):
        super(RegixLinksJob, self).configure_options()
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

    def parse_content(self, content):
        return BeautifulSoup(content, 'html.parser', parse_only=only_a_tags)

    def process_html(self, url, headers, content, soup):
        for tag in soup:
            if 'href' not in tag.attrs:
                continue                
            href = tag.attrs['href'].strip()
            # If the href is relative, joins with the base, otherwise just the real url
            norm_href = urlparse.urljoin(url, href) 

            if self.match_func(norm_href):
                yield norm_href, 1

    def reducer(self, key, values):
        yield key, sum(values)

    combiner = reducer

if __name__ == '__main__':
    RegexLinksJob.run() 
