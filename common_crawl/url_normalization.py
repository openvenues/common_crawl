import urlnorm
import urlparse
import re

shebang_regex = re.compile('^(/#!/).*?')

def parse_file_ext_from_url(url):
    parsed = urlparse.urlparse(url)
    last_path = parsed.path.split('/', 1)[-1]
    if '.' in last_path:
        extension = last_path.strip().split('.')
        if extension:
            return extension
    return None

def domain_and_canonical_url(url, remove_https=True, remove_www=True):
    try:
        url_tuple = urlparse.urlparse(url)
        scheme, netloc, path, params, query, fragment = url_tuple
        if not scheme:
            scheme, netloc, path, params, query, fragment = urlparse.urlparse('http://' + url)
    except Exception:
        return None, None
    if remove_https:
        scheme = 'http' if scheme == 'https' else scheme
    domain = netloc.split('.')
    if remove_www and domain and len(domain) > 2 and domain[0].startswith('www') and len(domain[0]) <= 4:
        netloc = '.'.join(domain[1:])
    
    url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
    return netloc, url

def normalize_canonical_url(url, use_url_norm=True):
    try:
        if use_url_norm:
            url = urlnorm.norm(url)

        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        host = urlparse.urlunparse((scheme, netloc, '', '', '', ''))
        path = urlparse.urlunparse(('', '', path, params, query, fragment))
        path = shebang_regex.sub('/', path)
        url = host + path
        
        return url.rstrip('/')
    except Exception:
        return None

def normalize_url(url, use_urlnorm=True, remove_https=True, remove_www=True):
    domain, url = domain_and_canonical_url(url, remove_https=remove_https, remove_www=remove_www)
    return normalize_canonical_url(url, use_urlnorm)
