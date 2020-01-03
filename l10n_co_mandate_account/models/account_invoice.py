# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    mandante_partner_id = fields.Many2one(
        'res.partner',
        string='Mandante')

    @api.multi
    def update_mandante_partner(self):
        for invoice_line in self.invoice_line_ids:
            invoice_line.mandante_partner_id = self.mandante_partner_id
        
        return True
