from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from .mirror_spider import MirrorSpider


def main():
    # configure the settings for the crawler and spider
    config = {
        'domain': 'reddit.com',
        'directory': 'website',
    }
    settings = Settings({
        'LOG_LEVEL': 'INFO',
        'DOWNLOADER_MIDDLEWARES': {
            'wayback_machine_scraper.middleware.WaybackMachine': 5,
        },
        'WAYBACK_MACHINE_TIME_RANGE': (20170101, 20170102),
    })

    # start the crawler
    process = CrawlerProcess(settings)
    process.crawl(MirrorSpider, **config)
    process.start()

