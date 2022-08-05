# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        'invoice_id.company_id', 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        sign = 1

        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price,
                currency,
                self.quantity,
                product=self.product_id,
                partner=self.invoice_id.partner_id
            )
        self.price_subtotal = price_subtotal_signed = (
            taxes['total_excluded'] if taxes else self.quantity * price
        )
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal

        if (self.invoice_id.currency_id
                and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id):
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(
                price_subtotal_signed,
                self.invoice_id.company_id.currency_id,
                self.company_id or self.env.user.company_id,
                date or fields.Date.today()
            )

        if (self.invoice_id.type in ['in_refund', 'out_refund']
                and self.invoice_id.refund_type == 'credit'):
            sign = -1

        self.price_subtotal_signed = price_subtotal_signed * sign
