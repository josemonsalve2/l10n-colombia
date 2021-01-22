# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrContractRisk(models.Model):
    _name = 'hr.contract.risk'
    _description = 'Occupational hazards'

    code = fields.Char(string='Code', size=10, required=True)
    name = fields.Char(string='Name', size=100, required=True)
    percent = fields.Float(string='Percentage',
                           default=0,
                           required=True,
                           help="Percentage of occupational risk")
    date = fields.Date(string="Effective date")
