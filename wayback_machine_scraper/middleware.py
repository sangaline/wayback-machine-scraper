from datetime import datetime

from scrapy import Request
from scrapy.http import Response
from scrapy.exceptions import NotConfigured, IgnoreRequest

class UnhandledIgnoreRequest(IgnoreRequest):
    pass

class WaybackMachine:
    cdx_url_template = ('http://web.archive.org/cdx/search/cdx?url={url}'
                    '&output=json&fl=timestamp,original,statuscode,digest')
    snapshot_url_template = 'http://web.archive.org/web/{timestamp}id_/{original}'
    robots_txt = 'http://web.archive.org/robots.txt'
    timestamp_format = '%Y%m%d%H%M%S'

    def __init__(self, crawler):
        self.crawler = crawler

        # read the settings
        time_range = crawler.settings.get('WAYBACK_MACHINE_TIME_RANGE')
        if not time_range:
            raise NotConfigured
        self.set_time_range(time_range)

    def set_time_range(self, time_range):
        # allow a single time to be passed in place of a range
        if type(time_range) not in [tuple, list]:
            time_range = (time_range, time_range)

        # translate the times to unix timestamps
        def parse_time(time):
            if type(time) in [int, float, str]:
                time = int(time)
                # realistic timestamp range
                if 10**8 < time < 10**13:
                    return time
                # otherwise archive.org timestamp format (possibly truncated)
                time_string = str(time)[::-1].zfill(14)[::-1]
                time = datetime.strptime(time_string, self.timestamp_format)
            return time.timestamp()

        self.time_range = [parse_time(time) for time in time_range]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        # ignore robots.txt requests
        if request.url == self.robots_txt:
            return

        # let Wayback Machine requests through
        if request.meta.get('wayback_machine_url'):
            return
        if request.meta.get('wayback_machine_cdx_request'):
            return

        # otherwise request a CDX listing of available snapshots
        return self.build_cdx_request(request)

    def process_response(self, request, response, spider):
        meta = request.meta

        # parse CDX requests and schedule future snapshot requests
        if meta.get('wayback_machine_cdx_request'):
            snapshot_requests = self.build_snapshot_requests(response, meta)

            # treat empty listings as 404s
            if len(snapshot_requests) < 2:
                return Response(meta['original_request'].url, status=404)


            # schedule all of the snapshots
            for snapshot_request in snapshot_requests:
                self.crawler.engine.schedule(snapshot_request, spider)

            # abort this request
            raise UnhandledIgnoreRequest

        # clean up snapshot responses
        if meta.get('wayback_machine_url'):
            return response.replace(url=meta['original_request'].url)

        return response
