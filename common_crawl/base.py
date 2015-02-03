import os
import shutil
import string
import subprocess
import sys

import boto

import traceback
import warnings
import logging

from collections import *

from mrjob.protocol import *
from mrjob.job import *
import ujson as json

from mrjob.util import unarchive, log_to_stream

from boto.s3.connection import Key, Bucket

import gzip
import warc

import re

from bs4 import UnicodeDammit, BeautifulSoup

import cgi
import cchardet

from httplib import HTTPResponse
from cStringIO import StringIO

from collections import *
from itertools import chain, product

logger = logging.getLogger('commoncrawl_job')

logging.root.setLevel(logging.ERROR)

class JsonProtocol(PickleProtocol):
    def _loads(self, value):
        return json.loads(value)
    
    def _dumps(self, value):
        return json.dumps(value)


class CommonCrawlJob(MRJob):
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = JSONProtocol
    HADOOP_INPUT_FORMAT = 'org.apache.hadoop.mapreduce.lib.input.NLineInputFormat'

    def jobconf(self):
        return {'mapreduce.input.lineinputformat.linespermap': '1',
                'mapreduce.input.fileinputformat.split.maxsize': '1'}

    def process_record(self, record):
        content = None
        try:
            payload = record.payload.read()
            s = FakeSocket(payload)
            response = HTTPResponse(s)
            response.begin()
            status_code = response.status
            if status_code != 200:
                return
            content_type = response.getheader('Content-Type', '')
            if 'text/html' not in content_type:
                return

            headers = response.getheaders()
            content = response.read(len(payload))
        except Exception:
            self.increment_counter('errors', 'process_record', 1)
            logging.error('Error processing record: {}', traceback.format_exc())
            return

        if content is not None:
            content = content.strip()

        if not content:
            return

        for item in self.process_content(record.url, headers, content):
            yield item

    def parse_html(self, content):
        return BeautifulSoup(content, 'html.parser')

    def filter(self, url, headers, content):
        return True

    def process_content(self, url, headers, content):
        parsed = None
        try:
           
            doc = UnicodeDammit(content, is_html=True)
            if not doc.unicode_markup or not self.filter(url, headers, doc.unicode_markup):
                self.increment_counter('commoncrawl', 'filter_not_matched', 1)
                return

            doc = doc.unicode_markup
            parsed = self.parse_html(doc)
            for item in self.process_html(url, headers, doc, parsed):
                yield item
        except Exception as e:
            self.increment_counter('errors', 'process_content', 1)
            logger.error(traceback.format_exc())
        finally:
            if parsed is not None:
                parsed.clear()

    # Override this method
    def process_html(self, url, headers, content, parsed):
        logger.error('In base process_html: {}'.format(traceback.format_exc()))
        return

    def mapper(self, _, line):
        line = line.rstrip().split('\t', 1)[-1]
        
        filename = line.rsplit('/', 1)[-1]
        first_rec = None
        f = open(filename, 'w')
        for i in xrange(10):
            try:
                conn = boto.connect_s3(anon=True)
                bucket = conn.get_bucket('aws-publicdatasets')
                key = Key(bucket, line)
                key.get_contents_to_file(f)
                f.close()
                records = warc.WARCFile(fileobj=gzip.open(filename, 'rb'))
                break
            except Exception as e:
                continue
        else:
            logger.error('10 attempts to get file {} failed, skipping...'.format(filename))
            return
 
        try:
            for i, record in enumerate(records):
                if record.type != 'response':
                    _ = record.payload.read()
                    continue
                for key, value in self.process_record(record):
                    yield key, value
                self.increment_counter('commoncrawl', 'processed_records', 1)
        except Exception:
            logger.error(traceback.format_exc())
            self.increment_counter('errors', 'general', 1)
        finally:
            f.close()
            os.unlink(filename)


class FakeSocket(object):
    def __init__(self, s):
        self.f = StringIO(s)

    def makefile(self, *args, **kw):
        return self.f
