import os
from datetime import datetime

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from scrapy_wayback_machine import WaybackMachineMiddleware

class MirrorSpider(CrawlSpider):
    name = 'mirror_spider'
    handle_httpstatus_list = [404]

    def __init__(self, domains, directory, allow=(), deny=(), unix=False):
        self.directory = directory
        self.unix = unix
        self.rules = (
            Rule(LinkExtractor(allow=allow, deny=deny), callback='save_page'),
        )

        # parse the allowed domains and start urls
        self.allowed_domains = []
        self.start_urls = []
        for domain in domains:
            url_parts = domain.split('://')
            unqualified_url = url_parts[-1]
            url_scheme = url_parts[0] if len(url_parts) > 1 else 'http'
            full_url = '{0}://{1}'.format(url_scheme, unqualified_url)
            bare_domain = unqualified_url.split('/')[0]
            self.allowed_domains.append(bare_domain)
            self.start_urls.append(full_url)

        super().__init__()

    def parse_start_url(self, response):
        # scrapy doesn't call the callbacks for the start urls by default,
        # this overrides that behavior so that any matching callbacks are called
        for rule in self._rules:
            if rule.link_extractor._link_allowed(response):
                if rule.callback:
                    rule.callback(response)

    def save_page(self, response):
        # ignore 404s
        if response.status == 404:
            return

        # make the parent directory
        url_parts = response.url.split('://')[1].split('/')
        parent_directory = os.path.join(self.directory, *url_parts)
        os.makedirs(parent_directory, exist_ok=True)

        # construct the output filename
        time = response.meta['wayback_machine_time']
        if self.unix:
            filename = '{0}.snapshot'.format(time.timestamp())
        else:
            filename = '{0}.snapshot'.format(time.strftime(WaybackMachineMiddleware.timestamp_format))
        full_path = os.path.join(parent_directory, filename)

        # write out the file
        with open(full_path, 'wb') as f:
            f.write(response.body)
