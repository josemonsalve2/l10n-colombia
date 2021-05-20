# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    deduction_line_ids = fields.One2many(
        string='Detail of Deductions',
        comodel_name='hr.payslip.deduction.line',
        inverse_name='slip_id',
        readonly=True)

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = []

        contracts = self.env['hr.contract'].browse(contract_ids)
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        sorted_rule_ids = [
            id for id, sequence in sorted(rule_ids, key=lambda x: x[1])
        ]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')

        for contract in contracts:
            for input in inputs:
                #Determina si existe posible(s) valor(es) para la entrada
                amount = 0.00
                param = [('contract_id', '=', contract.id),
                         ('input_id', '=', input.id)]
                deduction_ids = self.env['hr.contract.deduction'].search(param)

                if deduction_ids:
                    for deduction in deduction_ids:
                        #Si es un prestamo valida que no se exceda el valor total.
                        if deduction.period == 'limited':
                            if deduction.total_deduction > deduction.total_accumulated:
                                if (deduction.total_accumulated +
                                        deduction.amount
                                    ) > deduction.total_deduction:
                                    amount += deduction.total_deduction - deduction.total_accumulated
                                else:
                                    amount += deduction.amount
                        else:
                            amount += deduction.amount

                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'amount': amount,
                    'contract_id': contract.id,
                }

                res += [input_data]

        return res

    @api.multi
    def action_payslip_done(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.details_by_salary_rule_category:
                amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                partner_id = line._get_partner_id(credit_account=False)

                if line.salary_rule_id.analytic_account_id:
                    analytic_account_id = line.salary_rule_id.analytic_account_id.id
                else:
                    analytic_account_id = slip.contract_id.analytic_account_id and slip.contract_id.analytic_account_id.id or False

                if slip.contract_id:
                    registers = self.env['hr.contract.register'].browse(
                        slip.contract_id.register_ids)

                    for register in registers:
                        if line.salary_rule_id.register_id.id == register.id.register_id.id:
                            partner_id = register.id.partner_id.id
                            if register.id.account_debit_id:
                                debit_account_id = register.id.account_debit_id.id
                            if register.id.account_credit_id:
                                credit_account_id = register.id.account_credit_id.id
                            if register.id.analytic_account_id:
                                analytic_account_id = register.id.analytic_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name':
                        line.name,
                        'partner_id':
                        partner_id,
                        'account_id':
                        debit_account_id,
                        'journal_id':
                        slip.journal_id.id,
                        'date':
                        date,
                        'debit':
                        amount > 0.0 and amount or 0.0,
                        'credit':
                        amount < 0.0 and -amount or 0.0,
                        'analytic_account_id':
                        analytic_account_id,
                        'tax_line_id':
                        line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2][
                        'credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name':
                        line.name,
                        'partner_id':
                        partner_id,
                        'account_id':
                        credit_account_id,
                        'journal_id':
                        slip.journal_id.id,
                        'date':
                        date,
                        'debit':
                        amount < 0.0 and -amount or 0.0,
                        'credit':
                        amount > 0.0 and amount or 0.0,
                        'analytic_account_id':
                        analytic_account_id,
                        'tax_line_id':
                        line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2][
                        'debit']

            if float_compare(credit_sum, debit_sum,
                             precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly configured the Credit Account!'
                          ) % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum,
                               credit_sum,
                               precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly configured the Debit Account!'
                          ) % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date, 'state': 'done'})
            move.post()
