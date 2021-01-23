# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analityc Account',
        required=False)
    salary_rule_ids = fields.One2many(comodel_name='hr.department.salary.rule',
                                      inverse_name='department_id',
                                      string='Salary Rules')
