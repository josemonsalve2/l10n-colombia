# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountFiscalYear(models.Model):
    _inherit = "account.fiscal.year"
    _order = "date_from, id"

    state = fields.Selection(
        [("draft", "Abierto"), ("done", "Cerrado")],
        "Estado",
        readonly=True,
        copy=False,
        default="draft",
    )

    def _check_duration(self):
        obj_fy = self
        if obj_fy.date_to < obj_fy.date_from:
            return False
        return True

    _constraints = [
        (
            _check_duration,
            "Error!\nThe start date of a fiscal year must precede its end date.",
            ["date_from", "date_to"],
        )
    ]

    def find(self, dt=None, exception=True):
        res = self.finds(dt, exception)
        return res and res[0] or False

    def finds(self, dt=None, exception=True):
        if not dt:
            dt = fields.Date.context_today(self)
        args = [("date_from", "<=", dt), ("date_to", ">=", dt)]

        if self._context.get("company_id", False):
            company_id = self._context["company_id"]
        else:
            company_id = self.env["res.users"].browse(self._uid).company_id.id

        args.append(("company_id", "=", company_id))
        ids = self.search(args)
        if not ids:
            raise UserError(_("No existe periodo fiscal abierto para la fecha %s") % dt)

        return ids
