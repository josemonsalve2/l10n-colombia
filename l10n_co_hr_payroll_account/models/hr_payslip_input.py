# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrPayslipInput(models.Model):
    _name = "hr.payslip.input"
    _inherit = "hr.payslip.input"

    salary_rule_id = fields.Many2one(comodel_name='hr.salary.rule',
                                     string='Salary Rule',
                                     required=False)
    deduction_id = fields.Many2one(comodel_name='hr.contract.deduction',
                                   string='Deductión',
                                   required=False)