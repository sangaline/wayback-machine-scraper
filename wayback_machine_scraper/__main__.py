import argparse
from pkg_resources import get_distribution

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
        'unix': args.unix,
    }
    settings = Settings({
        'USER_AGENT': (
            'Wayback Machine Scraper/{0} '
            '(+https://github.com/sangaline/scrapy-wayback-machine)'
        ).format(get_distribution('wayback-machine-scraper').version),
        'LOG_LEVEL': 'DEBUG' if args.verbose else 'INFO',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_wayback_machine.WaybackMachineMiddleware': 5,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_DEBUG': args.verbose,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': args.concurrency,
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
    parser.add_argument('-c', '--concurrency', default=10.0, help=(
        'Target concurrency for crawl requests.'
        'The crawl rate will be automatically adjusted to match this target.'
        'Use values less than 1 to be polite and higher values to scrape more quickly.'
    ))
    parser.add_argument('-u', '--unix', action='store_true', help=(
        'Save snapshots as `UNIX_TIMESTAMP.snapshot` instead of '
        'the default `YYYYmmddHHMMSS.snapshot`.'
    ))
    parser.add_argument('-v', '--verbose', action='store_true', help=(
        'Turn on debug logging.'
    ))

    return parser.parse_args()
