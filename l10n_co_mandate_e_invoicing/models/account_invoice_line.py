# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def _get_information_content_provider_party_values(self):
        msg = _("'%s' does not have a mandante partner.")
        res = super(AccountInvoiceLine, self)._get_information_content_provider_party_values()

        if self.invoice_id.operation_type == '11':
            if not self.mandante_partner_id:
                raise UserError(msg % self.name)
            else:
                res = self.mandante_partner_id._get_information_content_provider_party_values()

        return res
