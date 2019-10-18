# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	payment_mean_id = fields.Many2one(
		comodel_name='account.payment.mean',
		string='Payment Method',
		copy=False,
		default=False)
	'''
	payment_mean_code_id = fields.Many2one(
		comodel='account.payment.mean.code',
		string='Mean of Payment',
		copy=False,
		default=False)
	'''

	@api.multi
	def write(self, vals):
		res = super(AccountInvoice, self).write(vals)

		if vals.get('date_invoice'):
			for invoice in self:
				invoice._onchange_invoice_dates()
		
		return res

	@api.onchange('date_invoice', 'date_due')
	def _onchange_invoice_dates(self):
		payment_mean_obj = self.env['ir.model.data']
		
		if not self.date_invoice:
			payment_mean_id = False
		elif self.date_invoice == self.date_due:
			id_payment_mean = payment_mean_obj.get_object_reference(
				'l10n_co_account_invoice_payment_mean',
				'account_payment_mean_1')[1]
			payment_mean_id = self.env['account.payment.mean'].browse(id_payment_mean)
		else:
			id_payment_mean = payment_mean_obj.get_object_reference(
				'l10n_co_account_invoice_payment_mean',
				'account_payment_mean_2')[1]
			payment_mean_id = self.env['account.payment.mean'].browse(id_payment_mean)

		self.payment_mean_id = payment_mean_id
