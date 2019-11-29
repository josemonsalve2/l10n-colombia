# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import validators
from odoo import api, models, fields
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    einvoicing_enabled = fields.Boolean(string='E-Invoicing Enabled')
    out_invoice_sent = fields.Integer(string='out_invoice Sent')
    out_refund_sent = fields.Integer(string='out_refund Sent')
    in_refund_sent = fields.Integer(string='in_refund Sent')
    invoices_sent = fields.Integer(string='Invoices Sent')
    profile_execution_id = fields.Selection(
        [('1', 'Production'), ('2', 'Test')],
        'Destination Environment of Document',
        default='2',
        required=True)
    test_set_id = fields.Char(string='Test Set Id')
    software_id = fields.Char(string='Software Id')
    software_pin = fields.Char(string='Software PIN')
    certificate_filename = fields.Char(string='Certificate Filename')
    certificate_file = fields.Binary(string='Certificate File')
    certificate_password = fields.Char(string='Certificate Password')
    signature_policy_url = fields.Char(string='Signature Policy Url')
    signature_policy_description = fields.Char(string='Signature Policy Description')
    signature_policy_filename = fields.Char(string='Signature Policy Filename')
    signature_policy_file = fields.Binary(string='Signature Policy File')
    files_path = fields.Char(string='Files Path')
    einvoicing_email = fields.Char(string='E-Invoicing Email')

    @api.onchange('signature_policy_url')
    def onchange_signature_policy_url(self):
        if not validators.url(self.signature_policy_url):
            raise ValidationError('Invalid URL.')
