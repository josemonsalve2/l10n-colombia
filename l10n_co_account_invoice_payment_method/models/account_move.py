# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method.dian",
        string="Payment Method",
        copy=False,
        default=False,
    )
    payment_method_code_id = fields.Many2one(
        comodel_name="account.payment.method.dian.code",
        string="Method of Payment",
        copy=False,
    )

    @api.onchange("payment_term_id")
    def _onchange_payment_term(self):
        payment_term_obj = self.env["ir.model.data"]
        payment_method_code_obj = self.env["account.payment.method.dian.code"]
        id_payment_term = payment_term_obj.get_object_reference(
            "account", "account_payment_term_immediate"
        )[1]
        payment_term_id = self.env["account.payment.term"].browse(id_payment_term)

        if self.payment_term_id and self.payment_term_id != payment_term_id:
            self.payment_method_code_id = payment_method_code_obj.search(
                [("code", "=", "1")]
            ).id

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)

        for invoice in res:
            invoice._onchange_payment_term()

        return res

    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)

        if vals.get("invoice_date"):
            for invoice in self:
                invoice._onchange_invoice_dates()

        return res

    @api.onchange("invoice_date", "invoice_date_due")
    def _onchange_invoice_dates(self):
        payment_method_obj = self.env["ir.model.data"]

        if not self.invoice_date:
            payment_method_id = False
        elif self.invoice_date == self.invoice_date_due:
            id_payment_method = payment_method_obj.get_object_reference(
                "l10n_co_account_invoice_payment_method", "account_payment_method_1"
            )[1]
            payment_method_id = self.env["account.payment.method.dian"].browse(
                id_payment_method
            )
        else:
            id_payment_method = payment_method_obj.get_object_reference(
                "l10n_co_account_invoice_payment_method", "account_payment_method_2"
            )[1]
            payment_method_id = self.env["account.payment.method.dian"].browse(
                id_payment_method
            )

        self.payment_method_id = payment_method_id
