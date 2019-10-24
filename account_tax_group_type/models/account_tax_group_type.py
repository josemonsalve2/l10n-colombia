# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class AccountTaxGroupType(models.Model):
    _name = 'account.tax.group.type'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    description = fields.Char(string='Description')

    _sql_constraints = [(
        'code_uniq',
        'unique (code)',
        _('The code of Tax Group Type must be unique!'))]
