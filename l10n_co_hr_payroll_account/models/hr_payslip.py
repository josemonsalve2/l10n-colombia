# -*- coding: utf-8 -*-
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta, time
from dateutil import relativedelta
from calendar import monthrange
import babel
from pytz import timezone

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


def days_between(start_date, end_date):
    #Add 1 day to end date to solve different last days of month
    #s1, e1 =  datetime.strptime(start_date,"%Y-%m-%d") , datetime.strptime(end_date,"%Y-%m-%d")  + timedelta(days=1)
    s1, e1 = start_date, end_date + timedelta(days=1)
    #Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    #Count days between the two 360 dates and return tuple (months, days)
    res = divmod(e360 - s360, 30)
    return ((res[0] * 30) + res[1]) or 0


class HrPayslipInput(models.Model):
    _name = "hr.payslip.input"
    _inherit = "hr.payslip.input"

    salary_rule_id = fields.Many2one('hr.salary.rule',
                                     'Regla salarial',
                                     required=False)
    deduction_id = fields.Many2one('hr.contract.deduction',
                                   'Deducción',
                                   required=False)


class HrPayslipWorkedDays(models.Model):
    _name = "hr.payslip.worked_days"
    _inherit = "hr.payslip.worked_days"

    holiday_id = fields.Many2one('hr.holidays', 'Asusencia')


class HrPayslip_Line(models.Model):
    _name = "hr.payslip.line"
    _inherit = "hr.payslip.line"

    deduction_id = fields.Many2one('hr.contract.deduction',
                                   'Deducción',
                                   required=False)
    register_credit_id = fields.Many2one(
        'hr.contribution.register',
        'Registro contribución crédito',
        help="Identificación del movimiento cédito de la regla salarial")


class HrPayslipAnalytic(models.Model):
    _name = 'hr.payslip.analytic'
    _description = 'Distribucion regla por cuenta analitica'
    _order = 'salary_rule_id'

    salary_rule_id = fields.Many2one('hr.salary.rule',
                                     'Regla salarial',
                                     required=True)
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Cuenta analítica',
                                          required=True)
    percent = fields.Float('Porcentaje', required=True, default=0)
    slip_id = fields.Many2one('hr.payslip',
                              'Nómina',
                              required=True,
                              ondelete='cascade',
                              select=True)

    _sql_constraints = [
        ('rule_analytic_uniq',
         'unique(slip_id, salary_rule_id, account_analytic_id)',
         'La distribucion para la misma regla y cuenta analitica debe ser unica'
         ),
    ]


class HrPayslipDetails(models.Model):
    _name = 'hr.payslip.details'
    _description = 'Detalle de las reglas salariales para prestaciones sociales'
    _order = 'salary_rule_id'

    slip_id = fields.Many2one('hr.payslip',
                              'Nómina',
                              required=True,
                              ondelete='cascade',
                              select=True)
    salary_rule_id = fields.Many2one('hr.salary.rule',
                                     'Regla salarial',
                                     required=True)
    date_from = fields.Date('Fecha inicial', required=True)
    date_to = fields.Date('Fecha final', required=True)
    days_total = fields.Integer('Total días', required=True, default=0)
    days_leave = fields.Integer('Días ausencia', required=True, default=0)
    days_neto = fields.Integer('Días neto', required=True, default=0)
    wage_actual = fields.Float('Salario básico actual',
                               required=True,
                               default=0)
    wage_total = fields.Float('Acumulado salario', required=True, default=0)
    wage_average = fields.Float('Promedio salario', required=True, default=0)
    variable_total = fields.Float('Total variable', required=True, default=0)
    variable_average = fields.Float('Promedio variable',
                                    required=True,
                                    default=0)
    subsidio_transporte = fields.Float('Subsidio transporte',
                                       required=True,
                                       default=0)
    total_average = fields.Float('Base', required=True, default=0)
    amount = fields.Float('Neto', required=True, default=0)

    _sql_constraints = [
        ('_uniq', 'unique(slip_id, salary_rule_id)',
         'Ya existe una regla para misma nomina'),
    ]


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    liquida = fields.Boolean(
        'Liquidación',
        default=False,
        help=
        "Indica si se ejecuta una estructura para liquidacion de contratos y vacaciones"
    )
    struct_id = fields.Many2one(
        'hr.payroll.structure',
        'Estructura salarial',
        help=
        "Defina la estructura salarial que se usará para la liquidacion de contratos y vacaciones"
    )
    date_prima = fields.Date('Fecha de liquidación de prima')
    date_cesantias = fields.Date('Fecha de liquidación de cesantías')
    date_vacaciones = fields.Date('Fecha de liquidación de vacaciones')
    date_liquidacion = fields.Date('Fecha de liquidación contrato')
    journal_voucher_id = fields.Many2one(
        'account.journal',
        'Diario de pago',
        help="Defina el diario para realizar los pagos o comprobante de egreso"
    )
    tipo_liquida = fields.Selection(
        [('nomina', 'Solo nómina'),
         ('otro', 'Solo vacaciones / contratos / primas'),
         ('nomi_otro', 'Nómina y vacaciones / contratos / primas)')],
        'Tipo liquidación',
        required=True,
        default='nomina')
    motivo_retiro = fields.Char('Motivo retiro', required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
        ('paid', 'Pagada'),
    ],
                             string='Status',
                             index=True,
                             readonly=True,
                             copy=False,
                             default='draft')

    @api.multi
    def draft_payslip_run(self):
        for run in self:
            if run.slip_ids:
                for payslip in run.slip_ids:
                    #if payslip.state == 'paid':
                    #   raise UserError(_('La nómina "%s" esta pagada. Primero debe romper conciliación en procesamiento No. %s')%(run.number, payslip.id))

                    if payslip.state == 'done':
                        payslip.action_payslip_cancel()
                        payslip.action_payslip_draft()

        return self.write({'state': 'draft'})

    @api.multi
    def close_payslip_run(self):
        for run in self:
            if run.slip_ids:
                for payslip in run.slip_ids:
                    #run.date_valid = payslip.date_valid
                    #No se recalcula al momento de contabilizar
                    #payslip.compute_sheet()
                    if payslip.state == 'draft':
                        payslip.action_payslip_done()

        return self.write({'state': 'close'})

    @api.multi
    def generate_payslip_run(self):
        res = True
        for run in self:
            if run.slip_ids:
                for payslip in run.slip_ids:
                    #actualiza los datos de liquidación si aplica

                    vals = {
                        'liquida': run.liquida,
                        'tipo_liquida': run.tipo_liquida,
                        'struct_liquida_id': run.struct_id.id,
                        'date_liquidacion': run.date_liquidacion,
                        'date_prima': run.date_prima,
                        'date_cesantias': run.date_cesantias,
                        'date_vacaciones': run.date_vacaciones,
                    }
                    payslip.write(vals)
                    payslip.compute_sheet()

        return True

    @api.multi
    def generate_voucher_run(self):
        res = True
        for run in self:
            if not run.journal_voucher_id:
                raise UserError(_('Debe primero ingresar el diario de pago'))
            if run.slip_ids:
                for payslip in run.slip_ids:
                    if payslip.state == 'done':
                        payslip.write(
                            {'journal_voucher_id': run.journal_voucher_id.id})
                        #payslip.process_voucher()
                        payslip.process_payment()

        return self.write({'state': 'paid'})

    @api.multi
    def unlink_voucher_run(self):
        res = True
        for run in self:
            if run.slip_ids:
                for payslip in run.slip_ids:
                    if payslip.state == 'paid':
                        #payslip.process_unlink_voucher()
                        payslip.process_unlink_payment()

        return self.write({'state': 'close'})

    @api.multi
    def unlink(self):
        for run in self:
            if run.slip_ids:
                for payslip in run.slip_ids:
                    if payslip.state != 'draft':
                        raise UserError(
                            _('La nómina "%s" no se puede eliminar porque no esta en borrador'
                              ) % (payslip.number))
                    else:
                        payslip.unlink()

        return super(HrPayslipRun, self).unlink()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Pay Slip'

    liquida = fields.Boolean(
        'Liquidación',
        default=False,
        help=
        "Indica si se ejecuta una estructura para liquidacion de contratos y vacaciones"
    )
    #deduction_line_ids = fields.One2many('hr.payslip.deduction.line', 'slip_id', 'Detalle deducciones', readonly=True)
    analytic_ids = fields.One2many('hr.payslip.analytic', 'slip_id',
                                   'Distribucion cuentas analiticas')
    details_ids = fields.One2many('hr.payslip.details', 'slip_id',
                                  'Detalle cálculos')
    date_prima = fields.Date('Fecha inicio prima')
    date_cesantias = fields.Date('Fecha inicio cesantías')
    date_vacaciones = fields.Date('Fecha inicio de vacaciones')
    date_liquidacion = fields.Date('Fecha de liquidación')
    payment_id = fields.Many2one('account.payment', string='Egreso No.')
    move_bank_id = fields.Many2one('account.move',
                                   string='Asiento contable pago')
    move_bank_name = fields.Char('Número pago')
    struct_liquida_id = fields.Many2one(
        'hr.payroll.structure',
        'Estructura salarial',
        help=
        "Defina la estructura salarial que se usará para la liquidacion de contratos y vacaciones"
    )
    tipo_liquida = fields.Selection(
        [('nomina', 'Solo nómina'),
         ('otro', 'Solo vacaciones / contratos / primas'),
         ('nomi_otro', 'Nómina y vacaciones / contratos / primas)')],
        'Tipo liquidación',
        required=True,
        default='nomina')
    motivo_retiro = fields.Char('Motivo retiro', required=False)
    recupera = fields.Boolean(
        'Recupera novedades',
        help=
        "Indica si se cargan nuevamente las novedades antes de hacer los cálculos",
        default=True)
    identification_id = fields.Char(related="employee_id.identification_id",
                                    store=True,
                                    string='Identificación')
    journal_voucher_id = fields.Many2one(
        'account.journal',
        'Diario de pago',
        help="Defina el diario para realizar los pagos o comprobante de egreso"
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('done', 'Done'),
            ('cancel', 'Rejected'),
            ('paid', 'Pagada'),
        ],
        string='Status',
        index=True,
        readonly=True,
        copy=False,
        default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")

    @api.multi
    def get_all_structures(self):
        """
        Adiciona funcion para encontrar las estructuras        
        """
        if not self.struct_liquida_id:
            return []

        return list(set(self.struct_liquida_id._get_parent_structure().ids))

    @api.multi
    def process_unlink_payment(self):
        # Elimina el comprobante de egreso
        for slip in self:
            #si esta asentado debe cancelarlo primero
            if slip.move_bank_id:
                for line in slip.move_bank_id.line_ids:
                    # refresh to make sure you don't unreconcile an already unreconciled entry
                    line.refresh()
                    if line.full_reconcile_id:
                        move_lines = [
                            move_line.id for move_line in
                            line.full_reconcile_id.reconciled_line_ids
                        ]
                        move_lines.remove(line.id)
                        line.remove_move_reconcile()

            if slip.payment_id and slip.payment_id.state == 'posted':
                slip.payment_id.cancel()

        return self.write({'move_bank_id': None, 'state': 'done'})

    @api.multi
    def process_unlink_voucher(self):
        # Elimina los asientos contables
        move_pool = self.env['account.move']
        for slip in self:
            #si esta asentado debe cancelarlo primero
            if slip.move_bank_id:
                for line in slip.move_bank_id.line_ids:
                    # refresh to make sure you don't unreconcile an already unreconciled entry
                    line.refresh()
                    if line.full_reconcile_id:
                        move_lines = [
                            move_line.id for move_line in
                            line.full_reconcile_id.reconciled_line_ids
                        ]
                        move_lines.remove(line.id)
                        line.remove_move_reconcile()

                    slip.move_bank_id.unlink()

        return self.write({'move_bank_id': None, 'state': 'done'})

    @api.multi
    def process_voucher(self):
        # Este procedimiento crea directamente los asientos contables sin el documento de egreso
        slip_line_obj = self.env['hr.payslip.line']
        move_pool = self.env['account.move']
        move_obj = self.env['account.move.line']
        precision = self.env['decimal.precision'].precision_get('Payroll')
        timenow = time.strftime('%Y-%m-%d')

        for slip in self:
            if not slip.journal_voucher_id:
                raise UserError(_('Debe primero ingresar el diario de pago'))

            #Busca el neto pagado
            slip_line_ids = slip_line_obj.search([('slip_id', '=', slip.id),
                                                  ('code', '=', 'NETO')])
            if slip_line_ids:
                for line in slip_line_ids:

                    if line.total != 0.0:
                        line_ids = []

                        default_partner_id = slip.employee_id.address_home_id.id
                        name = _('Pago nomina %s') % (slip.employee_id.name)
                        if slip.move_bank_name:
                            move = {
                                'name': slip.move_bank_name,
                                'narration': name,
                                'date': slip.date_to,
                                'ref': 'Pago ' + slip.number,
                                'journal_id': slip.journal_voucher_id.id,
                            }
                        else:
                            move = {
                                'narration': name,
                                'date': slip.date_to,
                                'ref': 'Pago ' + slip.number,
                                'journal_id': slip.journal_voucher_id.id,
                            }

                        acc_id = slip.journal_voucher_id.default_credit_account_id.id
                        if not acc_id:
                            raise UserError(
                                _('El diario "%s" no tiene configurado la cuenta crédito!'
                                  ) % (slip.journal_voucher_id.name))

                        adjust_credit = (
                            0,
                            0,
                            {
                                'name': 'Pago nomina ' + slip.number,
                                'date': slip.date_to,
                                'partner_id': default_partner_id,
                                'account_id': acc_id,
                                'journal_id': slip.journal_voucher_id.id,
                                'debit': 0.0,
                                'credit': line.total,
                                #'analytic_account_id': slip.contract_id.analytic_account_id.id or False,
                            })
                        line_ids.append(adjust_credit)

                        acc_id = slip.journal_id.default_debit_account_id.id
                        if not acc_id:
                            raise UserError(
                                _('El diario "%s" no tiene configurado la cuenta debito!'
                                  ) % (slip.journal_id.name))

                        adjust_debit = (
                            0,
                            0,
                            {
                                'name': 'Pago nomina ' + slip.number,
                                'date': slip.date_to,
                                'partner_id': default_partner_id,
                                'account_id': acc_id,
                                'journal_id': slip.journal_voucher_id.id,
                                'debit': line.total,
                                'credit': 0.0,
                                #'analytic_account_id': slip.contract_id.analytic_account_id.id or False,
                            })
                        line_ids.append(adjust_debit)

                        move.update({'line_ids': line_ids})
                        move_id = move_pool.create(move)

                        #Busca el pago creado en el paso anterior
                        if move_id:
                            for lin in move_id.line_ids:
                                if lin.account_id.id == slip.journal_id.default_debit_account_id.id:
                                    lines2rec = lin

                        #Busca la causación
                        lines = move_obj.search([
                            ('move_id', '=', slip.move_id.id),
                            ('account_id', '=',
                             slip.journal_id.default_credit_account_id.id),
                            ('credit', '=', line.total)
                        ])
                        if not lines:
                            raise UserError(
                                _('La nómina "%s" no presenta una cuenta por pagar por valor de "%s"'
                                  ) % (slip.number, line.total))

                        total = 0.0
                        for mov in lines:
                            lines2rec += mov
                            total = total + mov.credit

                        if len(lines2rec) > 2:
                            raise UserError(
                                _('La nómina "%s" presenta más de una contabilización!'
                                  ) % (slip.number))

                        diff = line.total - total
                        if diff != 0.0:
                            raise UserError(
                                _('La nómina "%s" presenta una diferencia al conciliar de "%s"'
                                  ) % (slip.number, diff))

                        lines2rec.reconcile()
                        move_id.post()

        return self.write({
            'move_bank_id': move_id.id,
            'move_bank_name': move_id.name,
            'state': 'paid'
        })

    @api.multi
    def process_payment(self):
        # Este procedimiento crea el comprobante de egreso y luego lo contabiliza
        slip_line_obj = self.env['hr.payslip.line']
        move_obj = self.env['account.move.line']
        precision = self.env['decimal.precision'].precision_get('Payroll')
        timenow = fields.Date.today()

        for slip in self:
            print('* slip: ', slip.number)
            if not slip.journal_voucher_id:
                raise UserError(_('Debe primero ingresar el diario de pago'))

            #Busca el neto pagado
            slip_line_ids = slip_line_obj.search([('slip_id', '=', slip.id),
                                                  ('code', '=', 'NETO')])
            if not slip_line_ids:
                raise UserError(
                    _('La nómina "%s" no presenta neto a pagar. Recalcular y recontabilizar esta nómina o eliminarla'
                      ) % (slip.number))

            if slip_line_ids:
                for line in slip_line_ids:

                    if line.total != 0.0:
                        line_ids = []

                        acc_id = slip.journal_voucher_id.default_credit_account_id.id
                        if not acc_id:
                            raise UserError(
                                _('El diario "%s" no tiene configurado la cuenta crédito!'
                                  ) % (slip.journal_voucher_id.name))

                        acc_id = slip.journal_id.default_debit_account_id.id
                        if not acc_id:
                            raise UserError(
                                _('El diario "%s" no tiene configurado la cuenta débito!'
                                  ) % (slip.journal_id.name))

                        #Busca la causación
                        lines = move_obj.search([
                            ('move_id', '=', slip.move_id.id),
                            ('account_id', '=',
                             slip.journal_id.default_credit_account_id.id),
                            ('credit', '=', line.total)
                        ])
                        if not lines:
                            raise UserError(
                                _('La nómina "%s" no presenta una cuenta por pagar por valor de "%s"'
                                  ) % (slip.number, line.total))

                        name = _('Pago nómina %s') % (slip.employee_id.name)
                        payment = {
                            'payment_type': 'outbound',
                            'payment_date': slip.date_to,
                            'partner_type': 'supplier',
                            'partner_id': slip.employee_id.address_home_id.id,
                            'communication': 'Pago nómina ' + slip.number,
                            'journal_id': slip.journal_voucher_id.id,
                            'amount': line.total,
                            'payment_method_id': 1,
                            'epago': False,
                        }

                        if slip.payment_id:
                            if slip.payment_id.state in [
                                    'posted', 'reconciled'
                            ]:
                                raise UserError(
                                    _('La nómina "%s" tiene asociado el egreso "%s" validado. Debe estar en borrador o anulado'
                                      ) % (slip.number, slip.payment_id.name))

                            if slip.payment_id.state == 'cancel':
                                slip.payment_id.action_draft()

                            slip.payment_id.write(payment)
                            payment_id = slip.payment_id

                        else:
                            payment_id = self.env['account.payment'].create(
                                payment)

                        payment_id.post()

                        # modifica la cuenta por la cuenta por pagar de salarios
                        for lin in payment_id.move_line_ids:
                            if lin.debit != 0:
                                move = lin.move_id
                                line_id = line

                                if lin.move_id.state == 'posted':
                                    lin.move_id.button_cancel()

                                lin.write({
                                    'account_id':
                                    slip.journal_id.default_credit_account_id.
                                    id
                                })
                                lin.move_id.post()
                                lines2rec = lin

                                # Hace la conciliacion de la cuenta por pagar y el egreso
                                total = 0.0
                                for mov in lines:
                                    lines2rec += mov
                                    total = total + mov.credit

                                if len(lines2rec) > 2:
                                    raise UserError(
                                        _('La nómina "%s" presenta más de una contabilización!'
                                          ) % (slip.number))

                                diff = line.total - total
                                if diff != 0.0:
                                    raise UserError(
                                        _('La nómina "%s" presenta una diferencia al conciliar de "%s"'
                                          ) % (slip.number, diff))

                                lines2rec.reconcile()

        return self.write({
            'move_bank_id': move.id,
            'payment_id': payment_id.id,
            'move_bank_name': payment_id.name,
            'state': 'paid'
        })

    @api.model
    def get_contract(self, employee, date_from, date_to):
        print('*** get_contract Sobreescrito')
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = [
            '&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)
        ]
        # OR if it starts between the given dates
        clause_2 = [
            '&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)
        ]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = [
            '&', ('date_start', '<=', date_from), '|',
            ('date_end', '=', False), ('date_end', '>=', date_to)
        ]
        #clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
        clause_final = [('employee_id', '=', employee.id),
                        ('state', 'in', ('open', 'cancel')), '|', '|'
                        ] + clause_1 + clause_2 + clause_3

        return self.env['hr.contract'].search(clause_final).ids

    @api.multi
    def compute_sheet(self):
        print('** compute_sheet en hr_payroll_co')
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code(
                'salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            payslip.worked_days_line_ids.unlink()
            payslip.input_line_ids.unlink()

            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                payslip.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)

            #computation of the salary input
            contracts = payslip.env['hr.contract'].browse(contract_ids)
            worked_days_line_ids = [
                (0, 0, day) for day in payslip.get_worked_day_lines(
                    contracts, payslip.date_from.strftime('%Y-%m-%d'),
                    payslip.date_to.strftime('%Y-%m-%d'))
            ]
            input_line_ids = [(0, 0, intput) for intput in payslip.get_inputs(
                contracts, payslip.date_from.strftime('%Y-%m-%d'),
                payslip.date_to.strftime('%Y-%m-%d'))]

            payslip.write({
                'worked_days_line_ids': worked_days_line_ids,
                'input_line_ids': input_line_ids
            })

            lines = [(0, 0, line) for line in payslip._get_payslip_lines(
                contract_ids, payslip.id)]

            payslip.write({'line_ids': lines, 'number': number})

        return True

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        print('--------------------- get_inputs en hr_payroll_co')
        res = []

        #++ Se utiliza la estructura del payslip en vez de la del contrato
        structure_ids = []
        if self.tipo_liquida in ('nomina',
                                 'nomi_otro') or not self.tipo_liquida:
            structure_ids = contracts.get_all_structures()

        if self.tipo_liquida in ('otro',
                                 'nomi_otro') and self.struct_liquida_id:
            structure_ids += self.get_all_structures()

        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        sorted_rule_ids = [
            id for id, sequence in sorted(rule_ids, key=lambda x: x[1])
        ]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')

        for contract in contracts:
            for input in inputs:
                #Determina si existe un posible(s) valor(es) para la entrada
                amount = 0.0
                deduction_ids = self.env['hr.contract.deduction'].search([
                    ('contract_id', '=', contract.id),
                    ('input_id', '=', input.id), ('date', '<=', date_to)
                ])
                ded_id = False
                if deduction_ids:
                    for reg in deduction_ids:
                        #Si es un prestamo valida que no se exceda el valor total
                        if reg.period == 'limited':
                            if (reg.total_accumulated +
                                    reg.amount) > reg.total_deduction:
                                amount = reg.total_deduction - reg.total_accumulated
                            else:
                                amount = amount + reg.amount
                        else:
                            amount = amount + reg.amount
                        ded_id = reg.id

                #Busca el valor en las novedades, sino encontro en las deducciones
                if amount == 0.0:
                    #novedades_ids = self.env['hr.payroll.news'].search([('identification_id', '=',contract.employee_id.identification_id),('code','=',input.code),('date_from','=',date_from),('date_to','=',date_to),('value','!=',0)])
                    novedades_ids = self.env['hr.payroll.news'].search([
                        ('employee_id', '=', contract.employee_id.id),
                        ('input_id', '=', input.id),
                        ('date_from', '=', date_from),
                        ('date_to', '=', date_to), ('value', '!=', 0)
                    ])
                    if novedades_ids:
                        for nov in novedades_ids:
                            amount = amount + nov.value

                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                    'amount': amount,
                    'salary_rule_id': input.input_id.id,
                    'deduction_id': ded_id,
                }
                res += [input_data]

        return res

    @api.model
    def get_inputs_analytics(self, contracts, date_from, date_to):
        #print('*** get_inputs_analytics')
        res = []
        contract_obj = self.env['hr.contract']
        rule_obj = self.env['hr.salary.rule']
        novedades_obj = self.env['hr.payroll.news']

        structure_ids = contract_obj.get_all_structures()
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(
            structure_ids)
        sorted_rule_ids = [
            id for id, sequence in sorted(rule_ids, key=lambda x: x[1])
        ]
        day_from = datetime.strptime(date_from, "%Y-%m-%d")
        day_to = datetime.strptime(date_to, "%Y-%m-%d")

        for contract in contracts:
            for rule in rule_obj.browse(sorted_rule_ids):
                if rule.input_ids:
                    for input in rule.input_ids:
                        amount = 0.0
                        #Busca el total en las novedades
                        distribuir = False
                        #novedades_ids = novedades_obj.search([('identification_id', '=',contract.employee_id.identification_id),('code','=',input.code),('date_from','=',date_from),('date_to','=',date_to),('value','!=',0)])
                        novedades_ids = novedades_obj.search([
                            ('employee_id', '=', contract.employee_id.id),
                            ('input_id', '=', input.id),
                            ('date_from', '=', date_from),
                            ('date_to', '=', date_to), ('value', '!=', 0)
                        ])
                        if novedades_ids:
                            for nov in novedades_obj.browse(novedades_ids):
                                amount = amount + nov.value
                                if nov.account_analytic_id:
                                    distribuir = True

                        if distribuir:
                            acumulado = 0.0
                            registro = 1
                            #print 'amount ',amount
                            #novedades_ids = novedades_obj.search(cr, uid, [('identification_id', '=',contract.employee_id.identification_id),('code','=',input.code),('date_from','=',date_from),('date_to','=',date_to),('account_analytic_id','!=',False),('value','!=',0)], context=context)
                            novedades_ids = novedades_obj.search([
                                ('employee_id', '=', contract.employee_id.id),
                                ('input_id', '=', input.id),
                                ('date_from', '=', date_from),
                                ('date_to', '=', date_to),
                                ('account_analytic_id', '!=', False),
                                ('value', '!=', 0)
                            ])
                            for nov in novedades_obj.browse(novedades_ids):
                                if len(novedades_ids) == registro:
                                    #Si está en el último registro se coloca el saldo
                                    porcentaje = 100 - acumulado
                                else:
                                    if amount != 0:
                                        porcentaje = round(
                                            (nov.value / amount) * 100, 2)
                                    else:
                                        porcentaje = 0
                                acumulado = acumulado + porcentaje

                                #inserta el registro
                                input_analytic = {
                                    'salary_rule_id':
                                    rule.id,
                                    'account_analytic_id':
                                    nov.account_analytic_id.id,
                                    'percent':
                                    porcentaje,
                                }
                                res += [input_analytic]
                                registro += 1

        return res

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        print('** get_worked_day_lines sobreescrito')
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(
                day_from, day_to, calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:

                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(
                    holiday.holiday_status_id, {
                        'name':
                        holiday.holiday_status_id.name or _('Global Leaves'),
                        'sequence':
                        5,
                        'code':
                        holiday.holiday_status_id.name or 'GLOBAL',
                        'number_of_days':
                        0.0,
                        'number_of_hours':
                        0.0,
                        'contract_id':
                        contract.id,
                    })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct[
                        'number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(
                day_from, day_to, calendar=contract.resource_calendar_id)

            #Febrero
            nb_of_days = 0
            if day_to.month == 2:
                if day_to.day == 28:
                    nb_of_days = 2
                if day_to.day == 29:
                    nb_of_days = 1

            if (day_from.month in (1, 3, 5, 7, 8, 10,
                                   12)) and (day_from.month != day_to.month):
                nb_of_days = -1

            #si no calcula nómina, los días trabajados deben ser cero
            #if self.tipo_liquida in ['otro']:
            if self.tipo_liquida in ['otro']:
                work_data['days'] = 0
                nb_of_days = 0
                work_data['hours'] = 0

            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'] + nb_of_days,
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict['categories'].dict[
                category.code] = category.code in localdict[
                    'categories'].dict and localdict['categories'].dict[
                        category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_mount(self, code, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category hc WHERE hp.id = pl.slip_id AND pl.category_id = hc.id AND hp.contract_id = %s AND hp.date_from >= (to_char(%s::date,'YYYY-mm')||'-01')::date\
                                  AND hp.date_to <= (to_char(%s::date,'YYYY-mm-dd'))::date AND hc.code = %s",
                    (self.contract_id.id, from_date, to_date, code))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_mount_inicial(self, code, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category hc WHERE hp.id = pl.slip_id AND pl.category_id = hc.id AND hp.contract_id = %s AND hp.date_from between (to_char(%s::date,'YYYY-mm-dd'))::date\
                                  AND (to_char(%s::date,'YYYY-mm-dd'))::date AND hc.code = %s",
                    (self.contract_id.id, from_date, to_date, code))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_mount_before(self, code, from_date):
                #suma una regla salaria por categoria
                #date_start = datetime.strptime(from_date,"%Y-%m-%d")
                date_start = from_date
                mes = date_start.month - 1
                ano = date_start.year
                if mes == 0:
                    mes = 12
                    ano = ano = date_start.year - 1

                from_date = str(ano) + '-' + str(mes) + '-01'

                if mes == 2:
                    dia = 28
                else:
                    dia = 30

                to_date = str(ano) + '-' + str(mes) + '-' + str(dia)

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category hc WHERE hp.id = pl.slip_id AND pl.category_id = hc.id AND hp.contract_id = %s AND hp.date_from >= %s::date\
                                  AND hp.date_to <= %s::date AND hc.code = %s",
                    (self.contract_id.id, from_date, to_date, code))

                res = self.env.cr.fetchone()
                valor = res and res[0] or 0.0

                return res and res[0] or 0.0

            def sum_rule_before(self, code, from_date):
                #suma una regla salarial del mes anterior
                #date_start = datetime.strptime(from_date,"%Y-%m-%d")
                #date_start = from_date
                #mes = date_start.month -1
                #ano = date_start.year
                #if mes == 0:
                #   mes = 12
                #   ano = ano = date_start.year -1

                #from_date = str(ano)+'-'+str(mes)+'-01'

                #if mes == 2:
                #   dia = 28
                #else:
                #   dia = 30

                #stop_date = str(ano)+'-'+str(mes)+'-'+str(dia)
                #start_date = str(ano)+'-'+str(mes)+'-'+'01'

                fecha_mes_anterior = from_date - timedelta(days=30)
                stop_date = from_date.replace(day=1) - timedelta(days=1)
                start_date = fecha_mes_anterior.replace(day=1)

                self.env.cr.execute(
                    """SELECT COALESCE(sum(pl.total),0) as suma
                                   FROM hr_payslip_line as pl
                                   inner join hr_payslip as hp on (hp.id = pl.slip_id)
                                   inner join hr_salary_rule r on (r.id = pl.salary_rule_id)
                                   WHERE hp.contract_id = %(contrato)s
                                   AND hp.date_from between %(fecha_desde)s::date and %(fecha_hasta)s::date
                                   AND r.code = %(regla)s""", {
                        'contrato': self.contract_id.id,
                        'fecha_desde': start_date,
                        'fecha_hasta': stop_date,
                        'regla': code,
                    })
                res = self.env.cr.fetchone()
                valor = res and res[0] or 0.0

                #Suma tambien los acumulados
                self.env.cr.execute(
                    """select coalesce(sum(a.amount),0) as suma
                         from hr_contract_acumulados a
                         inner join hr_salary_rule r on (r.id = a.salary_rule_id)
                         where a.amount <> 0
                           and a.contract_id = %(contrato)s
                           and r.code = %(regla)s
                           and a.date between %(fecha_desde)s::date and %(fecha_hasta)s::date
                         """, {
                        'contrato': self.contract_id.id,
                        'fecha_desde': start_date,
                        'fecha_hasta': stop_date,
                        'regla': code,
                    })
                res = self.env.cr.fetchone()
                valor = valor + (res and res[0] or 0.0)

                return valor

            #Recupera el auxilio de transporte del ano fiscal
            def get_auxtransporte_ano(self, from_date):
                #date_start = datetime.strptime(from_date,"%Y-%m-%d")
                date_start = from_date
                ano = date_start.year

                from_date = str(ano) + '-01-01'
                to_date = str(ano) + '-12-31'

                self.env.cr.execute(
                    "select sub_transporte from account_fiscalyear where date_start = %s::date and date_stop = %s::date",
                    (from_date, to_date))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            #Recupera el salario del ano fiscal
            def get_minsalary_ano(self, from_date):
                #date_start = datetime.strptime(from_date,"%Y-%m-%d")
                date_start = from_date
                ano = date_start.year

                from_date = str(ano) + '-01-01'
                to_date = str(ano) + '-12-31'

                self.env.cr.execute(
                    "select salario_minimo from account_fiscalyear where date_start = %s::date and date_stop = %s::date",
                    (from_date, to_date))

                res = self.env.cr.fetchone()
                valor = res and res[0] or 0.0
                salario = res and res[0] or 0.0

                return res and res[0] or 0.0

            def sum_rule(self, rule_id, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category hc WHERE hp.id = pl.slip_id AND pl.category_id = hc.id AND hp.contract_id = %s AND hp.date_from >= (to_char(%s::date,'YYYY-mm')||'-01')::date\
                                  AND hp.date_to <= (to_char(%s::date,'YYYY-mm')||'-15')::date AND pl.salary_rule_id = %s",
                    (self.contract_id.id, from_date, to_date, rule_id))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_rule_inicial(self, rule_id, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category hc WHERE hp.id = pl.slip_id AND pl.category_id = hc.id AND hp.contract_id = %s AND hp.date_from between (to_char(%s::date,'YYYY-mm-dd'))::date\
                                  AND (to_char(%s::date,'YYYY-mm-dd'))::date AND pl.salary_rule_id = %s",
                    (self.contract_id.id, from_date, to_date, rule_id))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_rule_range_acumulados(self, code, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    """select sum(a.amount) 
                              from hr_contract_acumulados a
                              inner join hr_salary_rule r on (r.id = a.salary_rule_id)
                              where r.code = %(regla)s
                                and a.contract_id = %(contrato)s
                                and p.special = False
                                and a.date between %(from_date)s::date and %(to_date)s::date
                                ''""", {
                        'contrato': self.contract_id.id,
                        'fecha_inicial': from_date,
                        'fecha_final': to_date,
                        'regla': code,
                    })
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_rule_range(self, code, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule sr WHERE hp.id = pl.slip_id AND pl.salary_rule_id = sr.id AND hp.contract_id = %s AND %s::date between hp.date_from\
                                  AND hp.date_to AND sr.code = %s",
                    (self.contract_id.id, from_date, code))

                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

            def sum_rule_discount(self, code, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                "Esta funciona tiene como objetivo determinar si se realiza o no un descuento, especial para cuando el empleado sale a vacaciones"
                self.env.cr.execute(
                    "SELECT COALESCE(sum(pl.total),0) as suma FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule sr WHERE hp.id = pl.slip_id AND pl.salary_rule_id = sr.id AND hp.contract_id = %s AND %s::date between hp.date_from\
                                  AND hp.date_to AND sr.code = %s",
                    (self.contract_id.id, from_date, code))
                res = self.env.cr.fetchone()
                valor = res and res[0] or 0.0

                if valor != 0.0:
                    self.env.cr.execute(
                        "SELECT hp.date_from as fecha FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule sr WHERE hp.id = pl.slip_id AND pl.salary_rule_id = sr.id AND hp.contract_id = %s AND %s::date between hp.date_from\
                                  AND hp.date_to AND sr.code = %s",
                        (self.contract_id.id, from_date, code))
                    fecha = self.env.cr.fetchone()[0] or False

                    if fecha:
                        date_from_discount = datetime.strptime(
                            fecha, "%Y-%m-%d")
                        date_from_nomina = datetime.strptime(
                            from_date, "%Y-%m-%d")

                        if date_from_discount.month != date_from_nomina.month:
                            valor = 0.0

                return valor

            def sum_days(self, from_date, to_date):
                from_date = from_date.strftime("%Y-%m-%d")
                to_date = to_date.strftime("%Y-%m-%d")

                self.env.cr.execute(
                    "SELECT coalesce(sum(number_of_days),0) as dias from hr_payslip_worked_days hd, hr_payslip as hp where hd.code IN ('WORK100','VACACIONES_REMUNERADAS') AND hp.id = hd.payslip_id AND hp.contract_id = %s AND hp.date_from between (to_char(%s::date,'YYYY-mm')||'-01')::date\
                                  AND (to_char(%s::date,'YYYY-mm-dd'))::date",
                    (self.contract_id.id, from_date, to_date))

                res = self.env.cr.fetchone()

                return res and res[0] or 0

            def day(self, date_from):
                """
                Funcion que retorna el dia de la fecha recibida como parametro
                """
                res = False
                if date_from:
                    #day_from = datetime.strptime(date_from,"%Y-%m-%d")
                    day_from = date_from
                    return day_from.day
                return res

            def month(self, date_from):
                """
                Funcion que retorna el dia de la fecha recibida como parametro
                """
                res = False
                if date_from:
                    #day_from = datetime.strptime(date_from,"%Y-%m-%d")
                    day_from = date_from
                    return day_from.month
                return res

            def days_between(self, start_date, end_date):
                start_date = start_date.strftime("%Y-%m-%d")
                end_date = end_date.strftime("%Y-%m-%d")

                #s1, e1 =  start_date , end_date + timedelta(days=1)
                s1, e1 = datetime.strptime(
                    start_date, "%Y-%m-%d"), datetime.strptime(
                        end_date, "%Y-%m-%d") + timedelta(days=1)
                #Convert to 360 days
                s360 = (s1.year * 12 + s1.month) * 30 + s1.day
                e360 = (e1.year * 12 + e1.month) * 30 + e1.day
                res = divmod(e360 - s360, 30)
                dias = ((res[0] * 30) + res[1]) or 0
                return dias

        #--------------------------------------
        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {
            'categories': categories,
            'rules': rules,
            'payslip': payslips,
            'worked_days': worked_days,
            'inputs': inputs
        }
        #get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)

        #dependiendo del tipo de nomina toma las estructuras salariales
        structure_ids = []
        if payslip.tipo_liquida in ('nomina', 'nomi_otro'):
            if len(contracts) == 1 and payslip.struct_id:
                structure_ids = list(
                    set(payslip.struct_id._get_parent_structure().ids))
            else:
                structure_ids = contracts.get_all_structures()

        if payslip.tipo_liquida in ('otro',
                                    'nomi_otro') and payslip.struct_liquida_id:
            structure_ids += payslip.get_all_structures()

        #get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        #run the rules by sequence
        sorted_rule_ids = [
            id for id, sequence in sorted(rule_ids, key=lambda x: x[1])
        ]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict,
                             employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                #check if the rule can be applied
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id,
                        tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    #Solo guarda los que tiene valor
                    if amount != 0:
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute':
                            rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base':
                            rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                else:
                    #blacklist this rule and its children
                    blacklist += [
                        id for id, seq in rule._recursive_search_of_rules()
                    ]

        return list(result_dict.values())


class hr_contract(models.Model):
    _name = "hr.contract"
    _inherit = "hr.contract"

    def promedio_vacaciones_comercial(self, date_liquidacion, contract_id):

        fecha_mes_anterior = date_liquidacion - timedelta(days=30)
        fecha_fin = date_liquidacion.replace(day=1) - timedelta(days=1)
        fecha_anterior = fecha_mes_anterior.replace(day=1)
        mes_anterior = 11
        self.env.cr.execute(
            """select round(sum(a.salario)::numeric) total
                          from (
                          select
                             s.contract_id as contract_id,
                             l.total as salario
                          from hr_payslip_line l
                          inner join hr_payslip s on (s.id = l.slip_id)
                          inner join hr_employee e on (e.id = l.employee_id) 
                          inner join hr_salary_rule r on (r.id = l.salary_rule_id)
                          where l.total <> 0
                            and s.contract_id = %(contrato)s
                            and r.promedio = True
                            and s.date_from between (%(fecha)s::date - interval '%(mes_anterior)s month')::date and  %(fecha_fin)s::date
                         union all
                         select 
                            c.id as contract_id,
                            a.amount as salario
                         from hr_contract_acumulados a
                         inner join hr_contract c on (c.id = a.contract_id)
                         inner join hr_employee e on (e.id = c.employee_id)
                         inner join hr_salary_rule r on (r.id = a.salary_rule_id)
                         where a.amount <> 0
                           and c.id = %(contrato)s
                           and r.promedio = True
                           and a.date between (%(fecha)s::date - interval '%(mes_anterior)s month')::date and  %(fecha_fin)s::date                       
                         ) as a
                         group by a.contract_id""", {
                'contrato': contract_id.id,
                'fecha': fecha_anterior,
                'fecha_fin': fecha_fin,
                'mes_anterior': mes_anterior,
            })
        res = self.env.cr.fetchone()
        if res:
            total_salario = res[0] or 0.0
        else:
            total_salario = 0.0

        result = total_salario / 12
        return result

    @api.model
    def promedio_prima(self,
                       contract_id,
                       payslip_detail,
                       proyectado=False,
                       context=None):
        print('########################## promedio_prima')
        result = 0.0

        if payslip_detail.days_neto > 0:
            # Busca las incapacidades en el mismo rango de fechas
            self.env.cr.execute(
                """select coalesce(sum(h.number_of_days_temp),0) from hr_holidays h
                           inner join hr_holidays_status s on (s.id = h.holiday_status_id)
                           where h.employee_id = %(empleado)s
                             and h.date_from::date >= %(fecha_inicial)s::date
                             and h.date_to::date <= %(fecha_final)s::date
                             and s.no_trabajado = True
                             and h.state = 'validate'""", {
                    'empleado': contract_id.employee_id.id,
                    'fecha_inicial': payslip_detail.date_from,
                    'fecha_final': payslip_detail.date_to,
                })

            # Revisa si en los ultimos 6 meses ha cambiado el salario
            self.env.cr.execute(
                """select coalesce(sum(wage),0)/( case when count(*)=0 then 1 else count(*) end  )
                          from hr_contract_change_wage
                          where contract_id = %(contrato)s
                          and date_start >= (SELECT (date_trunc('month', TIMESTAMP %(fecha)s) - interval '5 month')::date)
                          """, {
                    'contrato': contract_id.id,
                    'fecha': payslip_detail.date_to
                })
            wage = self.env.cr.fetchone()[0] or 0.0
            print('Promedio 6 meses ', wage)
            print('Salario basico actual ', contract_id.wage)
            payslip_detail.wage_actual = contract_id.wage

            if 1 == 1:
                print('Calcula acumulados para promedio salarial')
                #Si es proyectdo toma los acumulados desde el mes anterior
                if proyectado:
                    mes_anterior = 1
                else:
                    mes_anterior = 0

                self.env.cr.execute(
                    """select round(sum(a.salario)::numeric) total
                          from (
                          select
                             s.contract_id as contract_id,
                             l.total as salario
                          from hr_payslip_line l
                          inner join hr_payslip s on (s.id = l.slip_id)
                          inner join hr_employee e on (e.id = l.employee_id) 
                          inner join hr_salary_rule r on (r.id = l.salary_rule_id)
                          where l.total <> 0
                            and s.contract_id = %(contrato)s
                            and r.promedio = True
                            and s.date_from between %(fecha_prima)s::date and (%(fecha_liquidacion)s::date - interval '%(mes_anterior)s month')::date
                         union all
                         select 
                            c.id as contract_id,
                            a.amount as salario
                         from hr_contract_acumulados a
                         inner join hr_contract c on (c.id = a.contract_id)
                         inner join hr_employee e on (e.id = c.employee_id)
                         inner join hr_salary_rule r on (r.id = a.salary_rule_id)
                         where a.amount <> 0
                           and c.id = %(contrato)s
                           and r.promedio = True
                           and a.date between %(fecha_prima)s::date and (%(fecha_liquidacion)s::date - interval '%(mes_anterior)s month')::date                       
                         ) as a
                         group by a.contract_id""", {
                        'contrato': contract_id.id,
                        'fecha_prima': payslip_detail.date_from,
                        'fecha_liquidacion': payslip_detail.date_to,
                        'mes_anterior': mes_anterior,
                    })
                res = self.env.cr.fetchone()
                if res:
                    total_salario = res[0] or 0.0
                else:
                    total_salario = 0.0

                payslip_detail.wage_total += total_salario

                print('total salario acumulado', total_salario)

                #Si es proyectado se suma un mes con el salario basico
                if proyectado:
                    payslip_detail.wage_total += contract_id.wage

            #Calcula el salario promedio dependiendo si ha cambiado en lo ultimos 3 meses
            if wage == contract_id.wage or wage == 0.0:
                print('salario actual no cambio en 3 meses ', contract_id.wage)
                payslip_detail.wage_average = contract_id.wage + contract_id.factor
            else:
                if payslip_detail.days_neto != 0:
                    payslip_detail.wage_average = (
                        payslip_detail.wage_total /
                        payslip_detail.days_neto) * 30
                else:
                    raise UserError(_('Error!'),
                                    _("Existe una division por cero"))

            print('salario promedio ', payslip_detail.wage_average)

            #Busca los acumulados incluyendo el recibido por parametro
            print('Busca los acumulados para otros devengados')
            self.env.cr.execute(
                """select sum(a.primas) primas
                          from (
                          select
                             s.contract_id as contract_id,
                             l.total as primas
                          from hr_payslip_line l
                          inner join hr_payslip s on (s.id = l.slip_id)
                          inner join hr_employee e on (e.id = l.employee_id) 
                          inner join hr_salary_rule r on (r.id = l.salary_rule_id)
                          where l.total <> 0
                            and s.contract_id = %(contrato)s
                            and r.prima = True
                            and s.date_from between %(fecha_prima)s::date and %(fecha_liquidacion)s::date                         
                         union all
                         select 
                            c.id as contract_id,
                            a.amount as primas
                         from hr_contract_acumulados a
                         inner join hr_contract c on (c.id = a.contract_id)
                         inner join hr_employee e on (e.id = c.employee_id)
                         inner join hr_salary_rule r on (r.id = a.salary_rule_id)
                         where a.amount <> 0
                           and c.id = %(contrato)s
                           and r.prima = True                           
                           and a.date between %(fecha_prima)s::date and %(fecha_liquidacion)s::date                         
                         ) as a
                         group by a.contract_id""", {
                    'contrato': contract_id.id,
                    'fecha_prima': payslip_detail.date_from,
                    'fecha_liquidacion': payslip_detail.date_to,
                })

            res = self.env.cr.fetchone()
            print('res ', res)
            if res:
                total = res[0]
            else:
                total = 0
            print('total ', total)
            payslip_detail.variable_total += total

            if payslip_detail.days_neto < 30:
                payslip_detail.variable_average = payslip_detail.variable_total
            else:
                payslip_detail.variable_average = (
                    (payslip_detail.variable_total) /
                    payslip_detail.days_neto) * 30

            result = payslip_detail.wage_average + payslip_detail.variable_average

        return result

    @api.model
    def calcular_prima(self,
                       date_liquidacion,
                       date_prima,
                       contract_id,
                       amount=0.0,
                       proyectado=False,
                       amount_salary=0.0,
                       payslip=None,
                       salary_code=None,
                       context=None):
        print('########################### calcular_prima')
        #Elimina calculos previos
        year_id = self.env['account.fiscalyear'].search([
            ('date_start', '<=', date_liquidacion),
            ('date_stop', '>=', date_liquidacion)
        ])
        unlink_ids = self.env['hr.contract.liquidacion'].search([
            ('contract_id', '=', self.id), ('sequence', '=', '1')
        ])
        if unlink_ids:
            for liq in unlink_ids:
                liq.unlink()

        #elimina el detalle previo
        salary_rule = self.env['hr.salary.rule'].search([('code', '=',
                                                          salary_code)])
        details_ids = self.env['hr.payslip.details'].search([
            ('slip_id', '=', payslip.id),
            ('salary_rule_id', '=', salary_rule.id)
        ])
        if details_ids:
            for detail in details_ids:
                detail.unlink()

        for cont in self:

            #------------  PRIMA ------------------

            #valida fecha de liquidacion de contrato
            if not date_liquidacion:
                raise UserError(
                    _('Error!'),
                    _("Debe ingresar fecha de liquidación de contrato"))

            #la fecha de liquidacion debe ser mayor que la de inicio de contrato
            day_start = datetime.strptime(cont.date_start, "%Y-%m-%d")
            day_end = datetime.strptime(date_liquidacion, "%Y-%m-%d")
            if (day_end - day_start).days <= 0:
                raise UserError(
                    _('Error!'),
                    _("La fecha de liquidación de contrato debe ser mayor a la fecha de inicio del mismo"
                      ))

            #calcula prima
            if not date_prima:
                raise UserError(
                    _('Error!'),
                    _("Debe ingresar fecha de liquidación de prima"))

            #la fecha de liquidacion prima debe ser mayor que la de inicio de contrato
            day_to = datetime.strptime(date_prima, "%Y-%m-%d")
            if (day_to - day_start).days < 0:
                day_to = day_start
                #raise UserError(_('Error!'),_("La fecha de liquidación de prima debe ser mayor a la fecha de inicio del contrato"))

            dias = days_between(day_to, day_end)
            print('dias totales ', dias)

            payslip_detail = self.env['hr.payslip.details'].create({
                'slip_id':
                payslip.id,
                'salary_rule_id':
                salary_rule.id,
                'date_from':
                day_to,
                'date_to':
                day_end,
                'days_total':
                dias,
                'wage_total':
                amount_salary,
                'variable_total':
                amount,
            })

            # Busca las incapacidades en el mismo rango de fechas
            self.env.cr.execute(
                """select coalesce(sum(h.number_of_days_temp),0) from hr_holidays h
                           inner join hr_holidays_status s on (s.id = h.holiday_status_id)
                           where h.employee_id = %(empleado)s
                             and h.date_from::date >= %(fecha_inicial)s::date
                             and h.date_to::date <= %(fecha_final)s::date
                             and s.no_trabajado = True
                             and h.state = 'validate'""", {
                    'empleado': contract_id.employee_id.id,
                    'fecha_inicial': date_prima,
                    'fecha_final': date_liquidacion,
                })
            ausencias = self.env.cr.fetchone()[0] or 0
            print('dias ausencias ', ausencias)
            payslip_detail.days_leave = ausencias
            dias = dias - ausencias
            payslip_detail.days_neto = dias
            print('Dias neto ', dias)

            promedio_salario_var = self.promedio_prima(contract_id,
                                                       payslip_detail,
                                                       proyectado,
                                                       context=context)
            print('promedio_salario_var ', promedio_salario_var)

            aux_transporte = 0.00
            if year_id:
                for ano in year_id:
                    #aux_transporte = (ano.sub_transporte /30) * dias
                    #Si gana menos de 2 salarios minimos legal vigente
                    if promedio_salario_var < ano.salario_minimo * 2:
                        aux_transporte = ano.sub_transporte

            print('Subsidio de transporte ', aux_transporte)
            payslip_detail.subsidio_transporte = aux_transporte

            base = round(aux_transporte + promedio_salario_var, 0)
            print('base ', base)
            payslip_detail.total_average = base

            total_prima = round((base * dias) / 360, 0)
            print('total prima ', total_prima)
            payslip_detail.amount = total_prima

            args = {
                'name': 'Prima',
                'base': base,
                'desde': date_prima,
                'hasta': date_liquidacion,
                'dias': dias,
                'amount': total_prima,
                'contract_id': cont.id,
                'sequence': 1,
            }

            self.env['hr.contract.liquidacion'].create(args)

            print('Termina calcular prima')

            return total_prima

    @api.model
    def get_worked_day_lines_OLD(self,
                                 contracts,
                                 date_from,
                                 date_to,
                                 tipo_liquida=False):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)

            # compute leave days
            leaves = {}
            day_leave_intervals = contract.employee_id.iter_leaves(
                day_from, day_to, calendar=contract.resource_calendar_id)
            for day_intervals in day_leave_intervals:
                for interval in day_intervals:
                    holiday = interval[2]['leaves'].holiday_id
                    current_leave_struct = leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.name,
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })
                    leave_time = (interval[1] - interval[0]).seconds / 3600
                    current_leave_struct['number_of_hours'] += leave_time
                    work_hours = contract.employee_id.get_day_work_hours_count(
                        interval[0].date(),
                        calendar=contract.resource_calendar_id)
                    current_leave_struct[
                        'number_of_days'] += leave_time / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(
                day_from, day_to, calendar=contract.resource_calendar_id)

            #Febrero
            nb_of_days = 0
            if day_to.month == 2:
                if day_to.day == 28:
                    nb_of_days = 2
                if day_to.day == 29:
                    nb_of_days = 1

            if (day_from.month in (1, 3, 5, 7, 8, 10,
                                   12)) and (day_from.month != day_to.month):
                nb_of_days = -1

            #si no calcula nómina, los días trabajados deben ser cero
            if self.tipo_liquida in ['otro']:
                work_data['days'] = 0
                nb_of_days = 0
                work_data['hours'] = 0

            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'] + nb_of_days,
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    @api.model
    def create_report_xls(self, payslip):
        print('*** create_report_xls')
        slip = self.env['hr.payslip'].browse([payslip.id])
        home_report = self.env["ir.config_parameter"].get_param(
            "home.odoo.report")
        if not home_report:
            raise ValidationError(
                'Falta configurar el parámetro del sistema con clave home.odoo.report'
            )

        archivo = payslip.number.replace('/', '-') + '.xlsx'
        filename = home_report + archivo

        return filename
