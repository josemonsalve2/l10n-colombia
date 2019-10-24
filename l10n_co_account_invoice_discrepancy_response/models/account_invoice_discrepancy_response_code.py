# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceDiscrepancyResponseCode(models.Model):
	_name = 'account.invoice.discrepancy.response.code'

	name = fields.Char(string='Name')
	code = fields.Char(string='Code')
	type = fields.Selection([
		('in_refund', 'Vendor Refund'),
		('out_refund', 'Customer Refund')], string='Type')
