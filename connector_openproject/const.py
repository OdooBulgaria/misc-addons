# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

import collections
import datetime

from odoo import release

OpenProjectLink = collections.namedtuple(
    'OpenProjectLink', ['key', 'endpoint', 'model'])

OP_ASSIGNEE_LINK = OpenProjectLink(
    key='assignee', endpoint='users', model='op.res.users')
OP_PROJECT_LINK = OpenProjectLink(
    key='project', endpoint='projects', model='op.project.project')
OP_STATUS_LINK = OpenProjectLink(
    key='status', endpoint='statuses', model='op.project.task.type')
OP_USER_LINK = OpenProjectLink(
    key='user', endpoint='users', model='op.res.users')
OP_WORK_PACKAGE_LINK = OpenProjectLink(
    key='workPackage', endpoint='work_packages', model='op.project.task')

IMPORT_DELTA_BUFFER = datetime.timedelta(seconds=30)

USER_AGENT = '{r.product_name} {r.series}'.format(r=release)
