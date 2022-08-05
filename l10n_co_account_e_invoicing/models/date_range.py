# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class DateRange(models.Model):
    _inherit = 'date.range'

    out_invoice_sent = fields.Integer(string='Invoices Sent', default=0)
    out_refund_credit_sent = fields.Integer(string='Credit Notes Sent', default=0)
    out_refund_debit_sent = fields.Integer(string='Debit Notes Sent', default=0)
    in_invoice_sent = fields.Integer(string='Support Documents Sent', default=0)
    in_refund_sent = fields.Integer(
        string='Support Document Credit Notes Sent', default=0)
    application_response_sent = fields.Integer(
        string='ApplicationResponses Sent', default=0)
