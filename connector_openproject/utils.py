# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

import re
import string


ALPHANUMERIC = frozenset(string.ascii_letters + string.digits)


def parse_openproject_link_relation(link, endpoint):
    pattern = re.compile(r'^(?x)/api/v\d/%s/(?P<id>\d+)$' % endpoint)
    match = pattern.match(link.get('href') or '')
    return None if match is None else match.group('id')


def slugify(s, replacement='_'):
    r, prev = [], None
    for c in s:
        if c in ALPHANUMERIC:
            r.append(c)
            prev = c
        else:
            if prev == replacement:
                continue
            r.append(replacement)
            prev = replacement

    return ''.join(r).strip(replacement).lower()


def job_func(rec, func_name, delay=True, **kwargs):
    if delay:
        return getattr(rec.with_delay(**kwargs), func_name)
    return getattr(rec, func_name)
