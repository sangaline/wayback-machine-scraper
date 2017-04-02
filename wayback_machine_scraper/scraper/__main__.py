import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from .mirror_spider import MirrorSpider


def main():
    # configure the settings for the crawler and spider
    args = parse_args()
    config = {
        'domains': args.domains,
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

def parse_args():
    parser = argparse.ArgumentParser(description=(
        'Mirror all Wayback Machine snapshots of one or more domains '
        'within a specified time range.'
    ))
    parser.add_argument('domains', metavar='DOMAIN', nargs='+', help=(
        'Specify the domain(s) to scrape.'
    ))

    return parser.parse_args()
