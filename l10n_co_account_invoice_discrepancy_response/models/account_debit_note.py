# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError


class DebitNoteAccountMove(models.Model):
    _inherit = "account.move"

    is_debit_note = fields.Boolean(
        string="Is Debit Note",
        readonly=True,
        compute="_compute_is_debit_note",
        store=False,
    )

    def _compute_is_debit_note(self):
        for record in self:
            record.is_debit_note = record.debit_origin_id is not False
