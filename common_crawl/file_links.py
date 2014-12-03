from common_crawl.base import *
from common_crawl.url_normalization import *

from bs4 import BeautifulSoup, SoupStrainer

only_a_tags = SoupStrainer("a")

class FindFilesJob(CommonCrawlJob):
    def configure_options(self):
        super(FindFilesJob, self).configure_options()
        self.add_passthrough_option('--extensions', default='')
        self.add_passthrough_option('--pattern')
        self.add_passthrough_option('--insensitive', action="store_true", default=False)

    def mapper_init(self):
        self.valid_extensions = set([s.strip('. ') for s in self.options.extensions.split(',')])
        if self.options.pattern:
            regex_flags = re.I if self.options.insensitive else None
            self.valid_extension_pattern = re.compile(self.options.pattern, regex_flags)
        else:
            self.valid_extension_pattern = None
        # Fail early if no valid extensions are supplied
        if not self.valid_extensions and not self.valid_extension_pattern:
            raise ValueError("Must specify at least one extension type")

    def parse_content(self, content):
        return BeautifulSoup(content, parse_only=only_a_tags)

    def process_html(self, url, headers, soup):
        for tag in soup:
            if 'href' not in getattr(tag, 'attrs', {}):
                continue                
            href = tag.attrs['href'].strip()
            # If the href is relative, joins with the base, otherwise just the real url
            norm_href = normalize_url(urlparse.urljoin(url, href))
            if not norm_href:
                continue
            extension = parse_file_ext_from_url(norm_href)
            if extension and extension[-1].lower() in self.valid_extensions or '.'.join(extension[-2:]).lower() in self.valid_extensions:
                self.increment_counter('commoncrawl', 'links_found', 1)
                yield norm_href, 1

    def reducer(self, key, values):
        yield key, sum(values)

    combiner = reducer

if __name__ == '__main__':
    FindFilesJob.run() 
