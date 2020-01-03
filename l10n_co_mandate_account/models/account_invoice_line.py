# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    mandante_partner_id = fields.Many2one(
        'res.partner',
        string='Mandante')
