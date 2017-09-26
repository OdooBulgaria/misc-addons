# -*- coding: utf-8 -*-
# Copyright 2017 Naglis Jonaitis
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'OpenProject Connector',
    'version': '10.0.1.0.0',
    'author': 'Naglis Jonaitis',
    'category': 'Connector',
    'website': 'https://github.com/naglis',
    'license': 'AGPL-3',
    'summary': 'Synchronize OpenProject with Odoo',
    'external_dependencies': {
        'python': [
            'isodate',
            'requests',
            'requests_mock',
        ],
    },
    'depends': [
        'connector',
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/mail_message_subtype.xml',
        'data/res_partner.xml',
        'views/backend.xml',
        'views/op_account_analytic_line.xml',
        'views/op_res_users.xml',
        'views/op_project_task.xml',
        'views/op_project_project.xml',
    ],
    'installable': True,
    'application': True,
}
