# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    eps = fields.Many2one(comodel_name='res.partner',
                          string='Health Pretender Entity',
                          required=True)
    pension = fields.Many2one(comodel_name='res.partner',
                              string='Pension Pretender Entity',
                              required=True)
    layoff_fund = fields.Many2one(comodel_name='res.partner',
                                  string='Pension Pretender Entity',
                                  required=True)
