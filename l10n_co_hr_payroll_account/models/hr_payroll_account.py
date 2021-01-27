# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        # use partner of salary rule or fallback on employee's address
        emp_contract = self.env['hr.contract.setting']
        register_partner_db_id = self.salary_rule_id.register_id.partner_id or False
        register_partner_cr_id = self.salary_rule_id.register_credit_id.partner_id or False
        partner_id = self.slip_id.employee_id.address_home_id.id

        #Busca información en el contrato
        if not register_partner_db_id:
            entity_partner_db_id = emp_contract.search([
                ('contract_id', '=', self.slip_id.contract_id.id),
                ('contrib_id', '=', self.salary_rule_id.register_id.id)
            ])

        if not register_partner_cr_id:
            entity_partner_cr_id = emp_contract.search([
                ('contract_id', '=', self.slip_id.contract_id.id),
                ('contrib_id', '=', self.salary_rule_id.register_credit_id.id)
            ])

        if credit_account:
            return (register_partner_cr_id and register_partner_cr_id.id) or (
                entity_partner_cr_id
                and entity_partner_cr_id.partner_id.id) or partner_id or False
        else:
            return (register_partner_db_id and register_partner_db_id.id) or (
                entity_partner_db_id
                and entity_partner_db_id.partner_id.id) or partner_id or False

        return False


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_cancel(self):
        print('*** action_payslip_cancel heredado')
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        #return super(HrPayslip, self).action_payslip_cancel()
        return self.write({'state': 'cancel'})

    @api.multi
    def action_payslip_done(self):
        print('*** action_payslip_done heredado')
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            default_partner_id = slip.employee_id.address_home_id.id

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
                print('regla: ', line.salary_rule_id.name)
                debit_account_id = line.salary_rule_id.account_debit.id
                #busca l cuenta en el departamento
                if not debit_account_id:
                    dept_rule = self.env['hr.department.salary.rule'].search([
                        ('department_id', '=',
                         self.employee_id.department_id.id),
                        ('salary_rule_id', '=', line.salary_rule_id.id)
                    ])
                    debit_account_id = dept_rule and dept_rule[
                        0].account_debit_id and dept_rule[
                            0].account_debit_id.id or False

                credit_account_id = line.salary_rule_id.account_credit.id
                if not credit_account_id:
                    dept_rule = self.env['hr.department.salary.rule'].search([
                        ('department_id', '=',
                         self.employee_id.department_id.id),
                        ('salary_rule_id', '=', line.salary_rule_id.id)
                    ])
                    credit_account_id = dept_rule and dept_rule.account_credit_id and dept_rule.account_credit_id.id or False

                #Veririca si el contrato se distribuye o no
                dis = []
                if slip.contract_id.distribute:
                    if line.salary_rule_id.type_distri == 'hora':  #No aplica

                        self.env.cr.execute(
                            "select m.account_id, round((m.horas/k.total)* 100) porcentaje \
                                  from (select t.employee_id, l.account_id, sum(l.unit_amount) horas \
                                          from hr_timesheet_sheet_sheet t \
                                          inner join hr_analytic_timesheet h on (h.sheet_id = t.id) \
                                          inner join  account_analytic_line l on (l.id = h.line_id) \
                                          where t.state = 'done' \
                                          and l.date between %s and %s \
                                          and t.employee_id = %s \
                                          group by t.employee_id, l.account_id \
                                        ) m \
                                   inner join (select tt.employee_id, sum(ll.unit_amount) total \
                                               from hr_timesheet_sheet_sheet tt \
                                               inner join hr_analytic_timesheet hh on (hh.sheet_id = tt.id) \
                                               inner join  account_analytic_line ll on (ll.id = hh.line_id) \
                                               where tt.state = 'done' \
                                               and ll.date between %s and %s \
                                               and tt.employee_id = %s \
                                               group by tt.employee_id \
                                              ) k on (k.employee_id = m.employee_id)",
                            (slip.date_from, slip.date_to, slip.employee_id.id,
                             slip.date_from, slip.date_to,
                             slip.employee_id.id))

                        res = self.env.cr.fetchall()
                        if res:
                            for account_id, percent in res:
                                dis.append({
                                    'account_analytic_id': account_id,
                                    'porcentaje': percent
                                })
                        else:
                            analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                            dis.append({
                                'account_analytic_id': analytic_account_id,
                                'porcentaje': 100
                            })

                    elif line.salary_rule_id.type_distri == 'dpto':
                        print('Distribucion por contrato')
                        #Distribucion por centros de costo del contrato
                        if slip.contract_id.analytic_ids:
                            for cc in slip.contract_id.analytic_ids:
                                dis.append({
                                    'account_analytic_id':
                                    cc.account_analytic_id.id,
                                    'porcentaje':
                                    cc.percent
                                })
                        else:
                            #Si no tiene distribucion en el contrato no se realiza ninguna distribucion
                            analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                            dis.append({
                                'account_analytic_id': analytic_account_id,
                                'porcentaje': 100
                            })

                    elif line.salary_rule_id.type_distri == 'novedad':
                        #Distribucion por novedad

                        if slip.analytic_ids:
                            #Busca para la regla actual si tiene distribucion
                            analytic = slip_analytic.search(
                                cr, uid, [('slip_id', '=', slip.id),
                                          ('salary_rule_id', '=',
                                           line.salary_rule_id.id)])
                            if analytic:
                                for cc in slip_analytic.browse(
                                        cr, uid, analytic, context=context):
                                    dis.append({
                                        'account_analytic_id':
                                        cc.account_analytic_id.id,
                                        'porcentaje':
                                        cc.percent
                                    })
                            else:
                                analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                                dis.append({
                                    'account_analytic_id': analytic_account_id,
                                    'porcentaje': 100
                                })
                        else:
                            analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                            dis.append({
                                'account_analytic_id': analytic_account_id,
                                'porcentaje': 100
                            })

                    else:
                        analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                        dis.append({
                            'account_analytic_id': analytic_account_id,
                            'porcentaje': 100
                        })
                else:
                    analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or line.contract_id.analytic_account_id and line.contract_id.analytic_account_id.id or slip.employee_id.department_id.account_analytic_id and slip.employee_id.department_id.account_analytic_id.id or False,
                    dis.append({
                        'account_analytic_id': analytic_account_id,
                        'porcentaje': 100
                    })

                amt_total = 0
                l = 0

                for k in dis:
                    if l == len(dis):
                        valor = amount - amt_total
                    else:
                        valor = round(amount * dis[l]['porcentaje'] / 100)
                        amt_total = amt_total + valor

                    if debit_account_id and abs(amount) != 0:

                        debit_line = (0, 0, {
                            'name':
                            line.name,
                            'partner_id':
                            line._get_partner_id(credit_account=False),
                            'account_id':
                            debit_account_id,
                            'journal_id':
                            slip.journal_id.id,
                            'date':
                            date,
                            'debit':
                            valor > 0.0 and valor or 0.0,
                            'credit':
                            valor < 0.0 and -valor or 0.0,
                            'analytic_account_id':
                            dis[l]['account_analytic_id'],
                            'tax_line_id':
                            line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(debit_line)
                        debit_sum += debit_line[2]['debit'] - debit_line[2][
                            'credit']

                    if credit_account_id and abs(amount) != 0:

                        credit_line = (0, 0, {
                            'name':
                            line.name,
                            'partner_id':
                            line._get_partner_id(credit_account=True),
                            'account_id':
                            credit_account_id,
                            'journal_id':
                            slip.journal_id.id,
                            'date':
                            date,
                            'debit':
                            valor < 0.0 and -valor or 0.0,
                            'credit':
                            valor > 0.0 and valor or 0.0,
                            'analytic_account_id':
                            dis[l]['account_analytic_id'],
                            'tax_line_id':
                            line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(credit_line)
                        credit_sum += credit_line[2]['credit'] - credit_line[
                            2]['debit']

                    l = l + 1

                #---------------------------- TERMINA LINEA DE NOMINA

            if float_compare(credit_sum, debit_sum,
                             precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly configured the Credit Account!'
                          ) % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Neto a pagar'),
                    'partner_id': default_partner_id,
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
                    'name': _('Neto a pagar'),
                    'partner_id': default_partner_id,
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

        #return super(HrPayslip, self).action_payslip_done()
        return True


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')
    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account',
                                    'Debit Account',
                                    domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account',
                                     'Credit Account',
                                     domain=[('deprecated', '=', False)])


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')
    journal_id = fields.Many2one('account.journal', 'Salary Journal')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Run'

    journal_id = fields.Many2one(
        'account.journal',
        'Salary Journal',
        states={'draft': [('readonly', False)]},
        readonly=True,
        required=True,
        default=lambda self: self.env['account.journal'].search(
            [('type', '=', 'general')], limit=1))
