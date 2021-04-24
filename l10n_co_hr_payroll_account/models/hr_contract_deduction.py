# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import api, fields, models, _

class HrContractDeduction(models.Model):
    _name= 'hr.contract.deduction'
    _description = 'Deductions or Periodic Payments'

    input_id = fields.Many2one(
        string = 'Entry',
        comodel_name = 'hr.rule.input',
        help = 'Entry or parameter associated with the salary rule',
        required = True
    )

    type = fields.Selection(
        string = 'Deduction Type',
        selection = [
            ('P', 'Company Loan'),
            ('A', 'Saving'),
            ('S', 'Sure'),
            ('L', 'Lien'),
            ('E', 'Embargo'),
            ('R', 'Retention'),
            ('O', 'Other')
        ],
        default = 'O',
        required = True
    )

    period = fields.Selection(
        string = 'Period',
        selection = [
            ('limited', 'Limited'),
            ('undefined', 'Undefined')
        ],
        default = 'undefined',
        required = True
    ) 

    amount = fields.Float(
        string = 'Amount',
        help = "Value of the quota or percentage according to the formula of the salary rule",
        default = 0,
        required = True
    )

    total_deduction = fields.Float(
        string = 'Total Deduction',
        default = 0,
        help = "Total to Discount"
    )

    total_accumulated = fields.Float(
        string = 'Total Accumulated',
        compute = '_compute_total_accumulated',
        help = "Total paid or accrued from the concept"
    )

    date = fields.Date(
        string = 'Date',
        help = "Date of Loan or Obligation",
        required = True
    )

    appears_on_payslip = fields.Boolean(
        string = 'Appears on Payslip'
    )

    contract_id = fields.Many2one(
        string = 'Deductions',
        comodel_name = 'hr.contract',
        required = True,
        ondelete = 'cascade',
        index = True
    )

    @api.one
    def _compute_total_accumulated(self):
        deduction_line_ids = self.env['hr.payslip.deduction.line'].search([('deduction_id', '=', self.id),('slip_id.state', '=', 'done')])
        deduction_lines = self.env['hr.payslip.deduction.line'].browse(deduction_line_ids)

        self.total_accumulated = sum((line.amount) for line in deduction_lines)