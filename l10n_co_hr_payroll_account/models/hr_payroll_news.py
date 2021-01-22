# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, _


class HrPayrollNews(models.Model):
    _name = 'hr.payroll.news'
    _description = 'Payroll news'

    input_id = fields.Many2one(comodel_name='hr.rule.input',
                               string='News',
                               required=True,
                               help="Novelty code or name")
    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string='Employee',
                                  required=True,
                                  domain=[('active', '=', 'true')],
                                  help="ID or full name of the employee")
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    value = fields.Float(string='Value', required=True, default=0.0)

    _sql_constraints = [
        ('novedad_uniq', 'unique(input_id, date_from, date_to, employee_id)',
         'The novelty must be unique for the period and ID'),
    ]
