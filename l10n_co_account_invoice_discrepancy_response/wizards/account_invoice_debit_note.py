# -*- coding: utf-8 -*-
# Copyright 2017 Marlon Falcón Hernandez
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountInvoiceDebitNote(models.TransientModel):
    """Debit Note Invoice"""
    _name = "account.invoice.debit.note"
    _description = "Debit Note"

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            return inv.name
        return ''

    date_invoice = fields.Date(
        string='Debit Note Date',
        default=fields.Date.context_today,
        required=True)
    date = fields.Date(string='Accounting Date')
    description = fields.Char(
        string='Reason',
        required=True,
        default=_get_reason)
    discrepancy_response_code_id   = fields.Many2one(
		comodel_name='account.invoice.discrepancy.response.code',
		string='Correction concept for Refund Invoice')
    filter_debit_note = fields.Selection(
        [('debit', 'Create a draft debit note')],
        default='debit',
        string='Debit Note Method',
        required=True,
        help='Debit Note base on this type. You can not Modify and Cancel if the invoice is '
             'already reconciled')
    
    @api.multi
    def compute_debit_note(self, mode='debit'):
        msg1 = _('Cannot refund draft/proforma/cancelled invoice.')
        msg2 = _('Cannot refund invoice which is already reconciled, invoice should be '
                 'unreconciled first. You can only refund this invoice.')
        inv_obj = self.env['account.invoice']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False

            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise UserError(msg1)

                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(msg2)

                date = form.date or False
                description = form.description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)
                refund.update({
                    'refund_type': 'debit',
                    'discrepancy_response_code_id': form.discrepancy_response_code_id.id,
                    'name': 'debit'})
                created_inv.append(refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("Debit Note Invoice")
                body = description
                refund.message_post(body=body, subject=subject)

        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = safe_eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain

            return result

        return True

    @api.multi
    def invoice_debit_note(self):
        data_debit_note = self.read(['filter_debit_note'])[0]['filter_debit_note']

        return self.compute_debit_note(data_debit_note)
