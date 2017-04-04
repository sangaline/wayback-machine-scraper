import json
from datetime import datetime, timezone
from urllib.request import pathname2url

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
                time = time.replace(tzinfo=timezone.utc)
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
            if len(snapshot_requests) < 1:
                return Response(meta['wayback_machine_original_request'].url, status=404)

            # schedule all of the snapshots
            for snapshot_request in snapshot_requests:
                self.crawler.engine.schedule(snapshot_request, spider)

            # abort this request
            raise UnhandledIgnoreRequest

        # clean up snapshot responses
        if meta.get('wayback_machine_url'):
            return response.replace(url=meta['wayback_machine_original_request'].url)

        return response

    def build_cdx_request(self, request):
        cdx_url = self.cdx_url_template.format(url=pathname2url(request.url))
        cdx_request = Request(cdx_url)
        cdx_request.meta['wayback_machine_original_request'] = request
        cdx_request.meta['wayback_machine_cdx_request'] = True
        return cdx_request

    def build_snapshot_requests(self, response, meta):
        assert meta.get('wayback_machine_cdx_request'), 'Not a CDX request meta.'

        # parse the CDX snapshot data
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            # forbidden by robots.txt
            data = []
        if len(data) < 2:
            return []
        keys, rows = data[0], data[1:]
        def build_dict(row):
            new_dict = {}
            for i, key in enumerate(keys):
                if key == 'timestamp':
                    try:
                        time = datetime.strptime(row[i], self.timestamp_format)
                        new_dict['datetime'] = time.replace(tzinfo=timezone.utc)
                    except ValueError:
                        # this means an error in their date string (it happens)
                        new_dict['datetime'] = None
                new_dict[key] = row[i]
            return new_dict
        snapshots = list(map(build_dict, rows))
        del rows

        snapshot_requests = []
        for snapshot in self.filter_snapshots(snapshots):
            # update the url to point to the snapshot
            url = self.snapshot_url_template.format(**snapshot)
            original_request = meta['wayback_machine_original_request']
            snapshot_request = original_request.replace(url=url)

            # attach extension specify metadata to the request
            snapshot_request.meta.update({
                'wayback_machine_original_request': original_request,
                'wayback_machine_url': snapshot_request.url,
                'wayback_machine_time': snapshot['datetime'],
            })

            snapshot_requests.append(snapshot_request)

        return snapshot_requests

    def filter_snapshots(self, snapshots):
        filtered_snapshots = []
        initial_snapshot = None
        last_digest = None
        for i, snapshot in enumerate(snapshots):
            # ignore entries with invalid timestamps
            if not snapshot['datetime']:
                continue
            timestamp = snapshot['datetime'].timestamp()

            # ignore bot detections (e.g status="-")
            if len(snapshot['statuscode']) != 3:
                continue

            # also don't download redirects (because the redirected URLs are also present)
            if snapshot['statuscode'][0] == '3':
                continue


            # include the snapshot active when we first enter the range
            if len(filtered_snapshots) == 0:
                if timestamp > self.time_range[0]:
                    if initial_snapshot:
                        filtered_snapshots.append(initial_snapshot)
                        last_digest = initial_snapshot['digest']
                else:
                    initial_snapshot = snapshot

            # ignore before the range
            if timestamp < self.time_range[0]:
                continue

            # ignore the rest are past the specified time range
            if timestamp > self.time_range[1]:
                break

            # don't download unchanged snapshots
            if last_digest == snapshot['digest']:
                continue
            last_digest = snapshot['digest']

            filtered_snapshots.append(snapshot)

        return filtered_snapshots
