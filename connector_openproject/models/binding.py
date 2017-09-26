# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.queue_job.job import job, related_action


class OpenProjectSyncableMixin(models.AbstractModel):
    _name = 'openproject.syncable.mixin'

    op_sync = fields.Boolean(
        string='Sync with OpenProject',
        default=True,
    )


class OpenProjectAgeMixin(models.AbstractModel):
    _name = 'openproject.age.mixin'

    op_create_date = fields.Datetime(
        string='OpenProject Create Date',
        readonly=True,
    )
    op_write_date = fields.Datetime(
        string='OpenProject Last Update Date',
        readonly=True,
    )


class OpenProjectBinding(models.AbstractModel):
    _name = 'openproject.binding'
    _inherit = 'external.binding'
    _description = 'OpenProject Binding (abstract)'

    _sql_constraints = [
        (
            'code_uniq',
            'UNIQUE(backend_id, openproject_id)',
            'OpenProject ID must be unique!',
        ),
    ]

    backend_id = fields.Many2one(
        comodel_name='openproject.backend',
        string='Backend',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    openproject_id = fields.Char(
        'OpenProject ID',
        index=True,
        readonly=True,
    )

    @api.model
    @job(default_channel='root.openproject')
    @related_action(action='related_action_openproject_link')
    def import_record(self, backend, external_id, force=False):
        '''Import a single record from OpenProject.'''
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)

    @api.model
    @job(default_channel='root.openproject')
    def import_batch(self, backend, filters=None, delay=True):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(
                job_options=dict(delay=delay), filters=filters)
