![The Wayback Machine Scraper Logo](img/logo.png)

# The Wayback Machine Scraper

The repository consists of a command-line utility `wayback-machine-scraper` that can be used to scrape or download website data as it appears in [archive.org](http://archive.org)'s [Wayback Machine](https://archive.org/web/).
It crawls through historical snapshots of a website and saves the snapshots to disk.
This can be useful when you're trying to scrape a site that has scraping measures that make direct scraping impossible or prohibitively slow.
It's also useful if you want to scrape a website as it appeared at some point in the past or to scrape information that changes over time.

The command-line utility is highly configurable in terms of what it scrapes but it only saves the unparsed content of the pages on the site.
If you're interested in parsing data from the pages that are crawled then you might want to check out [scrapy-wayback-machine](https://github.com/sangaline/scrapy-wayback-machine) instead.
It's a downloader middleware that handles all of the tricky parts and passes normal `response` objects to your [Scrapy](https://scrapy.org) spiders with archive timestamp information attached.
The middleware is very unobtrusive and should work seamlessly with existing [Scrapy](https://scrapy.org) middlewares, extensions, and spiders.
It's what `wayback-machine-scraper` uses behind the scenes and it offers more flexibility for advanced use cases.

## Installation

The package can be installed using `pip`.

```bash
pip install wayback-machine-scraper
```

## Command-Line Interface

Writing a custom [Scrapy](https://scrapy.org) spider and using the `WaybackMachine` middleware is the preferred way to use this project, but a command line interface for basic mirroring is also included.
The usage information can be printed by running `wayback-machine-scraper -h`.

```
usage: wayback-machine-scraper [-h] [-o DIRECTORY] [-f TIMESTAMP]
                               [-t TIMESTAMP] [-a REGEX] [-d REGEX]
                               [-c CONCURRENCY] [-u] [-v]
                               DOMAIN [DOMAIN ...]

Mirror all Wayback Machine snapshots of one or more domains within a specified
time range.

positional arguments:
  DOMAIN                Specify the domain(s) to scrape. Can also be a full
                        URL to specify starting points for the crawler.

optional arguments:
  -h, --help            show this help message and exit
  -o DIRECTORY, --output DIRECTORY
                        Specify the domain(s) to scrape. Can also be a full
                        URL to specify starting points for the crawler.
                        (default: website)
  -f TIMESTAMP, --from TIMESTAMP
                        The timestamp for the beginning of the range to
                        scrape. Can either be YYYYmmdd, YYYYmmddHHMMSS, or a
                        Unix timestamp. (default: 10000101)
  -t TIMESTAMP, --to TIMESTAMP
                        The timestamp for the end of the range to scrape. Use
                        the same timestamp as `--from` to specify a single
                        point in time. (default: 30000101)
  -a REGEX, --allow REGEX
                        A regular expression that all scraped URLs must match.
                        (default: ())
  -d REGEX, --deny REGEX
                        A regular expression to exclude matched URLs.
                        (default: ())
  -c CONCURRENCY, --concurrency CONCURRENCY
                        Target concurrency for crawl requests.The crawl rate
                        will be automatically adjusted to match this
                        target.Use values less than 1 to be polite and higher
                        values to scrape more quickly. (default: 10.0)
  -u, --unix            Save snapshots as `UNIX_TIMESTAMP.snapshot` instead of
                        the default `YYYYmmddHHMMSS.snapshot`. (default:
                        False)
  -v, --verbose         Turn on debug logging. (default: False)
```

## Examples

The usage can be perhaps be made more clear with a couple of concrete examples.

### A Single Page Over Time

One of the key advantages of `wayback-machine-scraper` over other projects, such as [wayback-machine-downloader](https://github.com/hartator/wayback-machine-downloader), is that it offers the capability to download all available [archive.org](https://archive.org) snapshots.
This can be extremely useful if you're interested in analyzing how pages change over time.

For example, say that you would like to analyze many snapshots of the [Hacker News](news.ycombinator.com) front page as I did writing [Reverse Engineering the Hacker News Algorithm](http://sangaline.com/post/reverse-engineering-the-hacker-news-ranking-algorithm/).
This can be done by running

```bash
wayback-machine-scraper -a 'news.ycombinator.com$' news.ycombinator.com
```

where the `--allow` regular expression `news.ycombinator.com$` limits the crawl to the front page.
This produces a file structure of

```
website/
└── news.ycombinator.com
    ├── 20070221033032.snapshot
    ├── 20070226001637.snapshot
    ├── 20070405032412.snapshot
    ├── 20070405175109.snapshot
    ├── 20070406195336.snapshot
    ├── 20070601184317.snapshot
    ├── 20070629033202.snapshot
    ├── 20070630222527.snapshot
    ├── 20070630222818.snapshot
    └── etc.
```

with each snapshot file containing the full HTML body of the front page.

A series of snapshots for any page can be obtained in this way as long as suitable regular expressions and start URLs are constructed.
If we are interested in a page other than the homepage then we should use it as the start URL instead.
To get all of the snapshots for a specific story we could run

```bash
wayback-machine-scraper -a 'id=13857086$' 'news.ycombinator.com/item?id=13857086'
```

which produces

```
website/
└── news.ycombinator.com
    └── item?id=13857086
        ├── 20170313225853.snapshot
        ├── 20170313231755.snapshot
        ├── 20170314043150.snapshot
        ├── 20170314165633.snapshot
        └── 20170320205604.snapshot
```

### A Full Site Crawl at One Point In Time

If the goal is to take a snapshot of an entire site at once then this can also be easily achieved.
Specifying both the `--from` and `--to` options as the same point in time will assure that only one snapshot is saved for each URL.
Running

```
wayback-machine-scraper -f 20080623 -t 20080623 news.ycombinator.com
```

produces a file structure of

```
website
└── news.ycombinator.com
    ├── 20080621143814.snapshot
    ├── item?id=221868
    │   └── 20080622151531.snapshot
    ├── item?id=222157
    │   └── 20080622151822.snapshot
    ├── item?id=222341
    │   └── 20080620221102.snapshot
    └── etc.
```

with a single snapshot for each page in the crawl as it appeared on June 23, 2008.
