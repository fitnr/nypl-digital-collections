#!/usr/bin/env python

import requests
import xmltodict

def stop():
    raise StopIteration

class NYPLsearch(object):
    raw_results = ''
    results = dict()
    request = dict()
    error = None
    next_page = stop

    def __init__(self, token, format=None, page=None, per_page=None):
        self.token = token
        self.format = format or 'json'
        self.page = page or 1
        self.per_page = per_page or 10
        self.base = "http://api.repo.nypl.org/api/v1/items"

    # Return the captures for a given uuid
    # optional value withTitles=yes
    def captures(self, uuid, withTitles=False):
        url = '/'.join([self.base, uuid])
        return self._get(url, withTitles='yes' if withTitles else 'no')

    # Return the item-uuid for a identifier.
    def uuid(self, type, val):
        return self._get('/'.join((self.base, type, val)))

    # Search across all (without field) or in specific field
    # (valid fields at http://www.loc.gov/standards/mods/mods-outline.html)
    def search(self, q, field=None, page=None, per_page=None):
        url = '/'.join((self.base, 'search'))
        return self._get(url, q=q, field=field, page=page, per_page=per_page)

    # Return a mods record for a given uuid
    def mods(self, uuid):
        return self._get('/'.join((self.base, 'mods', uuid)))

    # Generic get which handles call to api and setting of results
    # Return: results dict
    def _get(self, url, **params):
        self.raw_results = self.results = None

        headers = {"Authorization": "Token token=" + self.token}

        params['page'] = params.get('page') or self.page
        params['per_page'] = params.get('per_page') or self.per_page

        r = requests.get(".".join([url, self.format]),
                         params=params,
                         headers=headers)

        self.raw_results = r.text
        self.results = self._to_dict(r)['nyplAPI']['response']

        self.request = r.json()['nyplAPI'].get('request', dict())

        if self.request.get('totalPages') > self.request.get('page'):
            del params['page']
            self.next_page = lambda x: self._get(url, page=self.request.get('page', 0) + 1, **params)
        else:
            self.next_page = stop

        if self.results['headers']['status'] == 'error':
            self.error = {
                'code': self.results['headers']['code'],
                'message': self.results['headers']['message']
            }
        else:
            self.error = None

        return self.results

    def _to_dict(self, r):
        return r.json() if self.format == 'json' else xmltodict.parse(r.text)
