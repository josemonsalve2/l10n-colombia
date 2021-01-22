# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    setting_ids = fields.One2many(comodel_name='hr.contract.setting',
                                  inverse_name='contract_id',
                                  string='Configuratión')
    deduction_ids = fields.One2many(comodel_name='hr.contract.deduction',
                                    inverse_name='contract_id',
                                    string='Deductions')
    settlement_ids = fields.One2many(comodel_name='hr.contract.settlement',
                                     inverse_name='contract_id',
                                     string='Settlement')
    accumulated_ids = fields.One2many(comodel_name='hr.contract.accumulated',
                                      inverse_name='contract_id',
                                      string='Accumulated')
    change_wage_ids = fields.One2many(comodel_name='hr.contract.change.wage',
                                      inverse_name='contract_id',
                                      string='Salary changes')
    risk_id = fields.Many2one(comodel_name='hr.contract.risk',
                              required=True,
                              string='Professional risk')
    date_bunus = fields.Date(string='Bunus settlement date')
    date_layoff_fund = fields.Date(string='Date Layoff Fund')
    date_holidays = fields.Date(string='Holiday settlement date')
    date_settlement = fields.Date(string="Contract settlement date")
    factor = fields.Float(string='Salary factor', required=True, default=0.0)
    parcial = fields.Boolean(string='Part time', default=False)
    pensionary = fields.Boolean(string='Pensionary', default=False)
    integral = fields.Boolean(string='integral salary', default=False)
    condition = fields.Float(string='Previous condition',
                             default=0.0,
                             digits_compute=dp.get_precision('Payroll'))
    compensation = fields.Float(string='Compensation',
                                default=0.0,
                                digits_compute=dp.get_precision('Payroll'))
    date_to = fields.Date(string="Fixed contract termination")
