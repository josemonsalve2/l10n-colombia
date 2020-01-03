# -*- coding: utf-8 -*-
# Copyright 2017 Marlon Falcón Hernandez
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self):
        msg1 = _('Please define a sequence for the refunds')
        msg2 = _('Please define a sequence for the debit notes')
        msg3 = _('Please define a sequence on the journal.')
        invoice = self._context.get('invoice', False)
        self._post_validate()

        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence or
                        # debit_note_sequence then use that one or use the regular one
                        sequence = journal.sequence_id

                        if invoice and invoice.type in ['out_refund', 'in_refund']:
                            if journal.refund_sequence and invoice.refund_type == 'credit':
                                if not journal.refund_sequence_id:
                                    raise UserError(msg1)

                                sequence = journal.refund_sequence_id

                            if journal.debit_note_sequence and invoice.refund_type == 'debit':
                                if not journal.debit_note_sequence_id:
                                    raise UserError(msg2)

                                sequence = journal.debit_note_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(msg3)

                if new_name:
                    move.name = new_name

        return self.write({'state': 'posted'})
