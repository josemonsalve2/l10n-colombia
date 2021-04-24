# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import fields, models, _
import odoo.addons.decimal_precision as dp

class HrPayslipDeductionLine(models.Model):
    _name = 'hr.payslip.deduction.line'
    _description = 'Detail of Deductions'
    _order = 'employee_id, contract_id, deduction_id'

    slip_id = fields.Many2one(
        string = 'Pay Slip',
        comodel_name = 'hr.payslip',
        required = True,
        ondelete = 'cascade',
        index = True
    )

    employee_id = fields.Many2one(
        string = 'Employee',
        comodel_name = 'hr.employee',
        required = True
    )

    contract_id = fields.Many2one(
        string = 'Contract',
        comodel_name = 'hr.contract',
        required = True
    )

    deduction_id = fields.Many2one(
        string = 'Deduction',
        comodel_name = 'hr.contract.deduction',
        required = True
    )

    amount = fields.Float(
        string = 'Amount',
        digits = dp.get_precision('Payroll'),
        default = 0
    )