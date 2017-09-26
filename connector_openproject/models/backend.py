# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

import datetime
import itertools

from odoo import api, fields, models
from odoo.addons.queue_job.job import job

from ..components.backend_adapter import op_filter
from ..const import IMPORT_DELTA_BUFFER
from ..utils import job_func

(
    PRIORITY_USERS,
    PRIORITY_PROJECTS,
    PRIORITY_WORK_PACKAGES,
    PRIORITY_WORK_PACKAGE,
    PRIORITY_ACTIVITIES,
    PRIORITY_TIME_ENTRIES,
    PRIORITY_TIME_ENTRY_CHUNKS,
) = range(1, 8)


def chunks(iterable, size=10):
    iterator = iter(iterable)
    for first in iterator:
        yield itertools.chain([first], itertools.islice(iterator, size - 1))




class OpenProjectBackend(models.Model):
    _name = 'openproject.backend'
    _description = 'OpenProject Backend'
    _inherit = 'connector.backend'

    @api.model
    def select_versions(self):
        return [
            ('7.3', '7.3+'),
        ]

    version = fields.Selection(
        selection='select_versions',
        required=True,
        default='7.3',
    )
    active = fields.Boolean(
        default=True,
    )
    debug = fields.Boolean(
        help='Output requests/responses to/from OpenProject API to the logs',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    instance_url = fields.Char(
        string='OpenProject URL',
        help='URL to the OpenProject instance',
        required=True,
    )

    api_key = fields.Char(
        string='API Key',
        help='The API key of the OpenProject user used for synchronization',
        required=True,
    )
    timeout = fields.Integer(
        help='HTTP request timeout in seconds (0 - no timeout).',
        default=30,
    )
    page_size = fields.Integer(
        string='Page Size',
        help='Number of elements to retrieve from OpenProject in one request',
        default=100,
    )

    op_user_ids = fields.One2many(
        comodel_name='op.res.users',
        inverse_name='backend_id',
        string='OpenProject Users',
    )
    op_project_ids = fields.One2many(
        comodel_name='op.project.project',
        inverse_name='backend_id',
        string='OpenProject Projects',
    )
    op_task_ids = fields.One2many(
        comodel_name='op.project.task',
        inverse_name='backend_id',
        string='OpenProject Work Packages',
    )
    op_time_entry_ids = fields.One2many(
        comodel_name='op.account.analytic.line',
        inverse_name='backend_id',
        string='OpenProject Time Entries',
    )

    user_count = fields.Integer(
        string='Users',
        compute='_compute_record_count',
        store=True,
    )
    project_count = fields.Integer(
        string='Projects',
        compute='_compute_record_count',
        store=True,
    )
    task_count = fields.Integer(
        string='Work Packages',
        compute='_compute_record_count',
        store=True,
    )
    time_entry_count = fields.Integer(
        string='Time Entries',
        compute='_compute_record_count',
        store=True,
    )

    @api.depends('op_user_ids', 'op_project_ids', 'op_task_ids',
                 'op_time_entry_ids')
    def _compute_record_count(self):
        for rec in self:
            rec.user_count = len(rec.op_user_ids)
            rec.project_count = len(rec.op_project_ids)
            rec.task_count = len(rec.op_task_ids)
            rec.time_entry_count = len(rec.op_time_entry_ids)

    @api.multi
    def toggle_debug(self):
        '''
        Inverse the value of the field ``debug`` on the records in ``self``.
        '''
        for rec in self:
            rec.debug = not rec.debug

    @job
    @api.multi
    def import_single_user(self, record):
        self.ensure_one()
        with self.work_on('op.res.users') as work:
            work.component(usage='record.importer').run(record)
        return True

    @job
    @api.multi
    def import_projects(self, delay=True):
        for rec in self:
            job_func(
                rec.env['op.project.project'],
                'import_batch',
                delay=delay,
                priority=PRIORITY_PROJECTS)(rec, delay=delay)

            # with rec.work_on('op.project.project') as work:
                # importer = work.component(usage='batch.importer')
                # adapter = work.component(usage='backend.adapter')
                # for record in adapter.get_collection():
                    # job_func(
                        # rec, 'import_single_project', delay=delay,
                        # priority=PRIORITY_USERS)(record)
        return True

    @api.multi
    def import_project_work_packages(self, delay=True):
        for rec in self:
            for project in rec.op_project_ids.filtered('op_sync'):
                now = datetime.datetime.now()
                filters = [
                    op_filter('project', '=', project.openproject_id),
                ]
                # TODO(naglis): Allow to override with `force=True` etc.
                if project.last_work_package_update:
                    last_updated = fields.Datetime.from_string(
                        project.last_work_package_update)
                    filters.append(
                        op_filter('updatedAt', '<>d',
                                  last_updated.isoformat(), None))
                job_func(
                    rec.env['op.project.task'],
                    'import_batch',
                    delay=delay,
                    priority=PRIORITY_WORK_PACKAGES)(
                        rec, filters=filters, delay=delay)
                project.last_work_package_update = now - IMPORT_DELTA_BUFFER

    # @job
    # @api.multi
    # def import_single_project_work_packages(self, project_id, delay=True):
        # self.ensure_one()
        # with self.work_on('op.project.task') as work:
            # adapter = work.component(usage='backend.adapter')
            # for record in adapter.get_project_work_packages(project_id):
                # job_func(self, 'import_single_work_package', delay=delay,
                          # priority=PRIORITY_WORK_PACKAGE)(record)
        # return True

    # @job
    # @api.multi
    # def import_single_work_package(self, record):
        # self.ensure_one()
        # with self.work_on('op.project.task') as work:
            # work.component(usage='record.importer').run(record)
        # return True

    # @job
    # @api.multi
    # def import_single_project(self, record):
        # self.ensure_one()
        # with self.work_on('op.project.project') as work:
            # work.component(usage='record.importer').run(record)
        # return True

    @api.multi
    def import_project_time_entries(self, delay=True):
        for rec in self:
            for project in rec.op_project_ids.filtered('op_sync'):
                now = datetime.datetime.now()
                filters = [
                    op_filter('project', '=', project.openproject_id),
                ]
                # XXX(naglis): Currently there is no updatedAt filter for
                # time entries.
                # TODO(naglis): File a feature request at OpenProject.
                job_func(
                    rec.env['op.account.analytic.line'],
                    'import_batch',
                    delay=delay,
                    priority=PRIORITY_TIME_ENTRIES)(
                        rec, filters=filters, delay=delay)
                project.last_time_entry_update = now - IMPORT_DELTA_BUFFER

                # job_func(
                    # rec, 'import_single_project_time_entries', delay=delay,
                    # priority=PRIORITY_TIME_ENTRIES)(
                        # project.openproject_id, delay=delay)

    # @job
    # @api.multi
    # def import_single_project_time_entries(self, project_id, delay=True):
        # self.ensure_one()
        # with self.work_on('op.account.analytic.line') as work:
            # adapter = work.component(usage='backend.adapter')
            # for chunk in chunks(
                    # adapter.get_project_time_entries(project_id),
                    # self.page_size):
                # job_func(self, 'import_time_entry_chunk', delay=delay,
                          # priority=PRIORITY_TIME_ENTRY_CHUNKS)(list(chunk))
        # return True

    # @job
    # @api.multi
    # def import_time_entry_chunk(self, chunk):
        # self.ensure_one()
        # with self.work_on('op.account.analytic.line') as work:
            # importer = work.component(usage='record.importer')
            # for record in chunk:
                # importer.run(record)
        # return True

    @api.multi
    def import_work_package_activities(self, delay=True):
        for rec in self:
            for task in rec.op_task_ids:
                job_func(
                    rec, 'import_single_work_package_activities', delay=delay,
                    priority=PRIORITY_ACTIVITIES)(task.openproject_id)

    # @job
    # @api.multi
    # def import_single_work_package_activities(self, work_package_id):
        # self.ensure_one()
        # with self.work_on('op.mail.message') as work:
            # adapter = work.component(usage='backend.adapter')
            # importer = work.component(usage='record.importer')
            # for record in adapter.get_work_package_activties (work_package_id):
                # importer.run(record)
        # return True

    @api.model
    def _cron_sync(self, domain=None):
        backends = self.search(domain or [])
        backends.import_projects()
        backends.import_project_work_packages()
        backends.import_project_time_entries()
        # backends.import_work_package_activities()
