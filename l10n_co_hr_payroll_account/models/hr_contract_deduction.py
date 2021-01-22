# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class HrContractDeduction(models.Model):
    _name = 'hr.contract.deduction'
    _description = 'Periodic deductions or payments'

    input_id = fields.Many2one(
        comodel_name='hr.rule.input',
        string='Salary rule',
        required=True,
        help="Parameter associated with the salary rule")

    period = fields.Selection(selection=[('limited', 'Limitado'),
                                         ('indefinite', 'Indefinido')],
                              default='indefinite',
                              string='Type',
                              required=True)
    amount = fields.Float(
        string='Share Value',
        default=0,
        help=
        "Value of the quota or percentage according to the formula of the salary rule",
        required=True)

    total_deduction = fields.Float(string='Total obligation',
                                   default=0,
                                   help="Total to discount")
    total_accumulated = fields.Float(
        string='Previous accumulated',
        default=0,
        help="Total paid or accumulated of the concept")
    total_acumulados = fields.Float(string='Accumulated Odoo',
                                    compute='_compute_saldo',
                                    default=0.0,
                                    readonly=True)
    current_balance = fields.Float(string='Saldo actual',
                                   compute='_compute_saldo',
                                   default=0.0,
                                   readonly=True)
    date = fields.Date(string='Start date',
                       select=True,
                       help="Date of loan or obligation")
    contract_id = fields.Many2one(comodel_name='hr.contract',
                                  string='Contract',
                                  required=True,
                                  ondelete='cascade',
                                  select=True)

    @api.one
    @api.depends('amount', 'period', 'total_deduction', 'total_accumulated')
    def _compute_saldo(self):

        for line in self:
            result = 0.0
            if line.period == 'limited':
                #              self.env.cr.execute("""select  sum(l.total) as total
                #                      from hr_payslip_line l
                #                      inner join hr_payslip p on (p.id = l.slip_id)
                #                      inner join hr_payslip_input i on (i.payslip_id = p.id and i.salary_rule_id = l.salary_rule_id)
                #                      where i.deduction_id = %s""" %  (line.id,))

                # Basado solo en entradas
                self.env.cr.execute(
                    """select  coalesce(sum(i.amount),0.0) as total 
                      from hr_payslip_input i
                      inner join hr_payslip p on (p.id = i.payslip_id)
                      where i.deduction_id = %(prestamo_id)s
                      """, {'prestamo_id': line.id})

                res = self.env.cr.fetchone() or False
                if res:
                    result = res[0] or 0.0
                    result = result

            line.total_acumulados = result