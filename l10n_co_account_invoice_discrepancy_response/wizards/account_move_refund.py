# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountInvoiceRefund(models.TransientModel):
    """Refunds invoice"""

    _inherit = "account.move.reversal"

    discrepancy_response_code_id = fields.Many2one(
        comodel_name="account.invoice.discrepancy.response.code",
        string="Correction concept for Refund Invoice",
    )

    def _prepare_default_reversal(self, move):
        default_values = super(AccountInvoiceRefund, self)._prepare_default_reversal(
            move
        )
        default_values["discrepancy_response_code_id"] = (
            self.discrepancy_response_code_id.id
        )
        return default_values
