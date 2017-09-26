# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

import base64
import collections
import json
import logging

import requests

from .const import USER_AGENT
from .exceptions import OpenProjectAPIError


_logger = logging.getLogger(__name__)


def pretty_print_request(req):
    return '{req.method} {req.url}\n{headers}\n\n{body}'.format(
        req=req,
        headers='\n'.join(
            '{}: {}'.format(k, v) for k, v in req.headers.iteritems()),
        body=req.body or '',
    )


def pretty_print_response(response):
    body = json.dumps(json.loads(response.content), indent=2)
    return '{resp.url}\n{headers}\n\n{body}'.format(
        resp=response,
        headers='\n'.join(
            '{}: {}'.format(k, v) for k, v in response.headers.iteritems()),
        body=body,
    )


def chunk_elements(gen):
    for chunk in gen:
        for element in chunk.get('_embedded', {}).get('elements', []):
            yield element


class OpenProject(object):
    API_VERSION = 'v3'

    def __init__(self, instance_url, api_key, page_size=25, debug=False,
                 timeout=None):
        if instance_url.endswith('/'):
            instance_url = instance_url.rstrip('/')
        self.instance_url = instance_url
        self.api_url = instance_url + '/api/%s' % self.API_VERSION
        self._api_key = api_key
        self.page_size = page_size
        self.debug = debug
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def auth_header(self):
        auth = base64.b64encode('apikey:%s' % self._api_key)
        return 'Basic %s' % auth

    def _raise_for_error(self, response):
        data = response.json()
        if data.get('_type') == 'Error':
            raise OpenProjectAPIError(
                data.get('message') or 'Unknown OpenProject API error')

    def _request(self, method, url, headers=None, params=None):
        offset = 1
        request_headers = {
            'User-Agent': USER_AGENT,
        }
        if headers:
            request_headers.update(headers)

        while True:
            request_params = collections.OrderedDict([
                ('offset', offset),
                ('pageSize', self.page_size),
            ])
            if params:
                request_params.update(params)

            endpoint_url = '%s%s' % (self.api_url, url)

            request = requests.Request(
                method,
                endpoint_url,
                params=request_params,
                headers=request_headers,
                auth=requests.auth.HTTPBasicAuth('apikey', self._api_key),
            )
            prepared_request = self.session.prepare_request(request)
            if self.debug:
                _logger.info(pretty_print_request(prepared_request))
            response = self.session.send(
                prepared_request, timeout=self.timeout)
            if self.debug:
                _logger.info(pretty_print_response(response))
            self._raise_for_error(response)
            data = response.json()
            yield data
            has_next = bool(data.get('_links', {}).get('nextByOffset'))
            if has_next:
                offset += 1
            else:
                break

    def get(self, *a, **kw):
        return self._request('GET', *a, **kw)

    def projects(self):
        for el in chunk_elements(self.get('/projects')):
            yield el

    def statuses(self):
        for el in chunk_elements(self.get('/statuses')):
            yield el

    def users(self):
        for el in chunk_elements(self.get('/users?pageSize=250')):
            yield el

    def project_work_packages(self, project_id):
        for el in chunk_elements(
                self.get('/projects/%s/work_packages' % project_id)):
            yield el

    def project_time_entries(self, project_id):
        params = {
            'filters': json.dumps([
                {
                    'project': {
                        'operator': '=',
                        'values': [
                            project_id,
                        ],
                    },
                },
            ]),
        }
        for el in chunk_elements(self.get('/time_entries', params=params)):
            yield el
