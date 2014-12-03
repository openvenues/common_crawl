from setuptools import setup, find_packages

setup(name='common_crawl',
    version='0.1',
    install_requires = [
        'ujson',
        'warc',
        'awscli',
        'boto',
        'mrjob',
        'BeautifulSoup4',
        'cchardet',
        'chardet',
    ],
    packages=find_packages(),
    description='Common Crawl MapReduce utilities using MRJob',
    url='http://github.com/openvenues/common_crawl',
    author='Al Barrentine',
    author_email='pelias@mapzen.com',
    license='MIT',
    zip_safe=False
)
