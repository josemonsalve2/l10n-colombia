# -*- coding: utf-8 -*-
# Copyright 2017 Marlon Falcón Hernandez
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, api, models
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	refund_type = fields.Selection(
		[('debit', 'Debit Note'),
		 ('credit', 'Credit Note')],
		index=True,
		string='Refund Type',
		track_visibility='always')
	discrepancy_response_code_id   = fields.Many2one(
		comodel_name='account.invoice.discrepancy.response.code',
		string='Correction concept for Refund Invoice')

	@api.one
	@api.depends(
		'invoice_line_ids.price_subtotal',
		'tax_line_ids.amount',
		'currency_id',
		'company_id',
		'date_invoice',
		'type')
	def _compute_amount(self):
		round_curr = self.currency_id.round
		self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
		self.amount_tax = sum(round_curr(line.amount) for line in self.tax_line_ids)
		self.amount_total = self.amount_untaxed + self.amount_tax
		amount_total_company_signed = self.amount_total
		amount_untaxed_signed = self.amount_untaxed
		sign = 1

		if (self.currency_id
				and self.company_id
				and self.currency_id != self.company_id.currency_id):
			currency_id = self.currency_id.with_context(date=self.date_invoice)
			amount_total_company_signed = currency_id.compute(
				self.amount_total,
				self.company_id.currency_id)
			amount_untaxed_signed = currency_id.compute(
				self.amount_untaxed,
				self.company_id.currency_id)

		if self.type in ['in_refund', 'out_refund'] and self.refund_type == 'credit':
			sign = -1

		self.amount_total_company_signed = amount_total_company_signed * sign
		self.amount_total_signed = self.amount_total * sign
		self.amount_untaxed_signed = amount_untaxed_signed * sign
	
	@api.one
	@api.depends(
		'state',
		'currency_id',
		'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
	def _compute_residual(self):
		residual = 0.0
		residual_company_signed = 0.0
		sign = 1

		if self.type in ['in_refund', 'out_refund'] and self.refund_type == 'credit':
			sign = -1

		for line in self.sudo().move_id.line_ids:
			if line.account_id.internal_type in ('receivable', 'payable'):
				residual_company_signed += line.amount_residual
				
				if line.currency_id == self.currency_id:
					if line.currency_id:
						residual += line.amount_residual_currency 
					else:
						residual += line.amount_residual
				else:
					if line.currency_id:
						from_currency = line.currency_id.with_context(date=line.date)
					else:
						from_currency = line.company_id.currency_id.with_context(date=line.date)
					
					residual += from_currency.compute(line.amount_residual, self.currency_id)
					
		self.residual_company_signed = abs(residual_company_signed) * sign
		self.residual_signed = abs(residual) * sign
		self.residual = abs(residual)
		digits_rounding_precision = self.currency_id.rounding
		
		if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
			self.reconciled = True
		else:
			self.reconciled = False

	@api.model
	def line_get_convert(self, line, part):
		res = super(AccountInvoice, self).line_get_convert(line, part)
		
		if self.type in ['in_refund', 'out_refund'] and self.refund_type == 'debit':
			amount_currency = 0
			
			if res.get('amount_currency') != 0:
				amount_currency = res.get('amount_currency') * (-1)

			debit = res.get('debit')
			credit = res.get('credit')
			res.update({
				'debit': credit ,
				'credit': debit,
				'amount_currency': amount_currency})

		return res
