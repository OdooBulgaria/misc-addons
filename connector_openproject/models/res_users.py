# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OpenProjectUser(models.Model):
    _name = 'op.res.users'
    _inherit = [
        'openproject.binding',
        'openproject.age.mixin',
    ]
    _inherits = {
        'res.users': 'odoo_id',
    }
    _description = 'OpenProject User'

    odoo_id = fields.Many2one(
        comodel_name='res.users',
        string='Odoo User',
        ondelete='cascade',
        required=True,
    )
