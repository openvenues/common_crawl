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

class FindFilesJob(CommonCrawlJob):
    def configure_options(self):
        super(FindFilesJob, self).configure_options()
        self.add_passthrough_option('--extensions')
        self.add_passthrough_option('--pattern')
        self.add_passthrough_option('--insensitive', default=None)

    def mapper_init(self):
        self.valid_extensions = set([s.strip() for s in self.options.extensions.split(',')])
        if self.options.pattern:
            regex_flags = re.I if self.options.insensitive is not None else None
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
            if 'href' not in tag.attrs:
                continue                
            href = tag.attrs['href'].strip()
            # If the href is relative, joins with the base, otherwise just the real url
            norm_href = urlparse.urljoin(url, href) 
            extension = parse_file_ext_from_url(norm_href)
            if extension and extension.lower() in self.valid_extensions:
                yield norm_href, 1

    def reducer(self, key, values):
        yield key, sum(values)

    combiner = reducer

if __name__ == '__main__':
    FindFilesJob.run() 