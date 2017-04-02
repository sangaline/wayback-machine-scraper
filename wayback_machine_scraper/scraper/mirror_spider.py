import os
from datetime import datetime

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from wayback_machine_scraper.middleware import WaybackMachine

class MirrorSpider(CrawlSpider):
    name = 'mirror_spider'
    handle_httpstatus_list = [404]

    def __init__(self, domain, directory, allow=(), deny=(), unix=False):
        self.directory = directory
        self.unix = unix
        self.rules = (
            Rule(LinkExtractor(allow=allow, deny=deny), callback='save_page'),
        )
        self.allowed_domains = [domain]
        self.start_urls = [f'http://{domain}']

        super().__init__()

    def save_page(self, response):
        # ignore 404s
        if response.status == 404:
            return

        # make the parent directory
        url_parts = response.url.split('://')[1].split('/')
        parent_directory = os.path.join(self.directory, *url_parts)
        os.makedirs(parent_directory, exist_ok=True)

        # construct the output filename
        time = response.meta['wayback_machine_datetime']
        if self.unix:
            filename = f'{time.timestamp()}.snapshot'
        else:
            filename = f'{time.strftime(WaybackMachine.timestamp_format)}.snapshot'
        full_path = os.path.join(parent_directory, filename)

        # write out the file
        with open(full_path, 'wb') as f:
            f.write(response.body)
