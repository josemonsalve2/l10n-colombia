# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    liquid = fields.Boolean(
        string='Liquidation',
        default=False,
        help=
        "Indica si se ejecuta una estructura para liquidacion de contratos y vacaciones"
    )
    struct_id = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Salary structure',
        help=
        "Define the salary structure that will be used for the settlement of contracts and vacations"
    )
    date_bunus = fields.Date(string='Bunus liquidation date')
    date_layoff_fund = fields.Date(string='Date Layoff Fund')
    date_holidays = fields.Date(string='Holiday liquidation date')
    date_liquidation = fields.Date(string="Contract liquidation date")
    date_payment = fields.Date(string='Date Payment')
    journal_voucher_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment journal',
        help="Define the journal to make payments or proof of expenditure")
    type_liquid = fields.Selection(selection=[
        ('nomina', 'Solo nómina'),
        ('otro', 'Solo vacaciones / contratos / primas'),
        ('nomi_otro', 'Nómina y vacaciones / contratos / primas)')
    ],
                                   string='Type liquidation',
                                   required=True,
                                   default='nomina')
    motive_retirement = fields.Char(string='Motive Retirement', required=False)
    state = fields.Selection(selection=[
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
                        'liquid': run.liquid,
                        'type_liquid': run.type_liquid,
                        'struct_liquida_id': run.struct_id.id,
                        'date_liquidation': run.date_liquidation,
                        'date_bunus': run.date_bunus,
                        'date_layoff_fund': run.date_layoff_fund,
                        'date_holidays': run.date_holidays,
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
            if not run.date_payment:
                raise UserError(
                    _('Debe primero ingresar la fecha de contabilización del pago'
                      ))

            if run.slip_ids:
                for payslip in run.slip_ids:
                    if payslip.state == 'done':
                        payslip.write({
                            'journal_voucher_id':
                            run.journal_voucher_id.id,
                            'date_payment':
                            run.date_payment
                        })
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