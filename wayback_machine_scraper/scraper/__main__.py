import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from .mirror_spider import MirrorSpider


def main():
    # configure the settings for the crawler and spider
    args = parse_args()
    config = {
        'domains': args.domains,
        'directory': args.output,
        'allow': args.allow,
        'deny': args.deny,
    }
    settings = Settings({
        'LOG_LEVEL': 'INFO',
        'DOWNLOADER_MIDDLEWARES': {
            'wayback_machine_scraper.middleware.WaybackMachine': 5,
        },
        'WAYBACK_MACHINE_TIME_RANGE': (getattr(args, 'from'), args.to),
    })

    # start the crawler
    process = CrawlerProcess(settings)
    process.crawl(MirrorSpider, **config)
    process.start()


def parse_args():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter, description=(
        'Mirror all Wayback Machine snapshots of one or more domains '
        'within a specified time range.'
    ))
    parser.add_argument('domains', metavar='DOMAIN', nargs='+', help=(
        'Specify the domain(s) to scrape. '
        'Can also be a full URL to specify starting points for the crawler.'
    ))
    parser.add_argument('-o', '--output', metavar='DIRECTORY', default='website', help=(
        'Specify the domain(s) to scrape. '
        'Can also be a full URL to specify starting points for the crawler.'
    ))
    parser.add_argument('-f', '--from', metavar='TIMESTAMP', default='10000101', help=(
        'The timestamp for the beginning of the range to scrape. '
        'Can either be YYYYmmdd, YYYYmmddHHMMSS, or a Unix timestamp.'
    ))
    parser.add_argument('-t', '--to', metavar='TIMESTAMP', default='30000101', help=(
        'The timestamp for the end of the range to scrape. '
        'Use the same timestamp as `--from` to specify a single point in time.'
    ))
    parser.add_argument('-a', '--allow', metavar='REGEX', default=(), help=(
        'A regular expression that all scraped URLs must match.'
    ))
    parser.add_argument('-d', '--deny', metavar='REGEX', default=(), help=(
        'A regular expression to exclude matched URLs.'
    ))

    return parser.parse_args()
