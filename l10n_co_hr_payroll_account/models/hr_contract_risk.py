# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrContractRisk(models.Model):
    _name = 'hr.contract.risk'
    _description = 'Professionals Risks'

    code = fields.Char(string='Code', size=10, help='Risk Code', required=True)
    name = fields.Char(string='Name',
                       size=100,
                       help='Risk Name',
                       required=True)
    percent = fields.Float(string='Percentage',
                           default=0.00,
                           help='Percentage of Professional Risk',
                           required=True)
    date = fields.Date(string='Effective Date')
