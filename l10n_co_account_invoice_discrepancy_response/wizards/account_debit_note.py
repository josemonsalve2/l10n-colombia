# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


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
