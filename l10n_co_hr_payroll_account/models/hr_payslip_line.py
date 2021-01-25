# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrPayslipLine(models.Model):
    _name = "hr.payslip.line"
    _inherit = "hr.payslip.line"

    deduction_id = fields.Many2one(comodel_name='hr.contract.deduction',
                                   string='Deductión',
                                   required=False)
    register_credit_id = fields.Many2one(
        comodel_name='hr.contribution.register',
        string='Credit contribution record',
        help="Identification of the credit movement of the wage rule")
