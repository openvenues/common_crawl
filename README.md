common_crawl
============

Python MapReduce jobs for processing the Common Crawl plus command-line utilities.

### Getting started

Make sure you have an EC2 account set up (http://aws.amazon.com). You'll need the following handy:

1. Your access key and secret to launch EC2 instances
2. A bucket to use on S3 for storing intermediate and final jobs results
3. Sign up for Elastic MapReduce (EMR). You don't need to launch any clusters as MRJob creates a temporary one on each job launch by default (although that is configurable if you want to reuse an existing cluster see: http://mrjob.readthedocs.org/en/latest/guides/emr-advanced.html).

### Basic usage of command-line jobs

This repo uses MRJob, a Python MapReduce library from Yelp which is particularly useful for spinning up temporary Elastic MapReduce (EMR) clusters on AWS, running a single job and spinning down instances on failure/completion. MRJob can run locally or on a standard (non-EMR) Hadoop cluster, but we focus on EMR and the more cost-effective spot instances by default since running a job over the full Common Crawl requires > 100 cores.

1. Download the repo and start a config:
```bash
git clone https://github.com/openvenues/common_crawl
cd common_crawl
cp mrjob.conf.example mrjob.conf
```

2. Using your favorite text editor, open up mrjob.conf. There are several numbered, commented lines in the file that indicate where you need to change various settings (your EC2 access key, etc.) Feel free to drop us a line if there are any problems with this part.

3. Run a job by module name:
```bash
./bin/ccjob find_links --output-dir=s3://your/output/bucket --num-ec2-core-instances=50 --ec2-core-instance-type=c3.2xlarge --ec2-core-instance-bid-price=0.42 --insensitive --no-output --pattern=".*/arcgis/rest/services.*" `./bin/get_latest_cc /tmp`
```

`ccjob` runs a job by name. The list of currently implemented jobs can be found in the "common_crawl" directory. Just use the module name minus the ".py" extension to run the job command-line.

`get_latest_cc` is a shell script that pulls the warcs.path (just a manifest file with pointers to the crawl data, ~10MB) down to local disk and uses it as input to the job.

All MRJob options are valid, see the documentation (http://mrjob.readthedocs.org/en/latest/index.html) for more details.

### Writing your own jobs

To write a custom job using the Common Crawl data, just subclass CommonCrawlJob like so:

```python
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
```

Unlike in MRJob, where you'd typically write a function named "mapper", we've abstracted some of the details of the WARC file format that Common Crawl uses to store its files. Subclassing CommonCrawlJob offers a few convenience methods you can override so that your code only has to deal with HTML. In general, override `process_html` and optionally `parse_content` as shown above. See `commoncrawl/base.py` for all the 

The result of this job will be a number of files containing tab-separated key/value pairs, one per line, both JSON-encoded.

### BeautifulSoup vs. lxml.html
The first version of the Common Crawl extraction job was written using lxml.html, a fast C library based on libxml2's HTMLParser. However, running said parser over billions of badly-encoded webpages revealed some bugs in lxml/libxml2 related to reading from uninitialized memory at the C level (see https://bugs.launchpad.net/lxml/+bug/1240696), which eats up all the system's memory and crashes the program. The bug occurs non-deterministically, so is hard to track down, but will occur, on different documents, if the job is run for long enough. 

Until there's a fix, lxml won't be usable for this project. BeautifulSoup is a forgiving pure-Python parser designed for working with "tag soup". It has pluggable backends for parsing the raw HTML and we're currently using Python's HTMLParser. It's up to 100x slower than lxml, so we try wherever possible to filter down the number of tags we consider using `SoupStrainer` and the `parse_only` keyword to BeautifulSoup. This means if all we're only looking for a few selectors, we can get away without building a full parse tree of the entire document. Still, until the referenced bug in lxml/libxml2 is fixed or we find a faster parser (libhubbub looks promising) that can handle all the documents in Common Crawl, be prepared to use 50-100 8-core machines for about 6 days to run a job over all 4B docs.


### TODOS
1. Add sampling for getting quick counts
2. Investigate options for HTML parsers to make jobs faster/cheaper