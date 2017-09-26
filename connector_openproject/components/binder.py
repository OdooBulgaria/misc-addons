# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent, Component


class OpenProjectBaseBinder(AbstractComponent):
    _name = 'base.openproject.binder'
    _inherit = [
        'base.binder',
        'base.openproject.connector',
    ]
    _external_field = 'openproject_id'
    _usage = 'binder'


class OpenProjectBinder(Component):
    _name = 'openproject.binder'
    _inherit = 'base.openproject.binder'
    _apply_on = [
        'op.account.analytic.line',
        'op.mail.message',
        'op.project.project',
        'op.project.task',
        'op.project.task.type',
        'op.res.users',
    ]
