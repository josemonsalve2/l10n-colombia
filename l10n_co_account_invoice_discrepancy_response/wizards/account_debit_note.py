# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"
    _description = "Add DIAN Correction Concept to Debit Note Wizard"

    discrepancy_response_code_id = fields.Many2one(
        comodel_name="account.invoice.discrepancy.response.code",
        string="Correction concept for Debit Note",
    )

    def _prepare_default_values(self, move):
        default_values = super(AccountDebitNote, self)._prepare_default_values(move)
        default_values["discrepancy_response_code_id"] = (
            self.discrepancy_response_code_id.id
        )
        return default_values
