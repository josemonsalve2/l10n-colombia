# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	dian_document_lines = fields.One2many(
		comodel_name='account.invoice.dian.document',
		inverse_name='invoice_id',
		string='Dian Document Lines')

	@api.multi
	def invoice_validate(self):
		res = super(AccountInvoice, self).invoice_validate()

		if self.company_id.einvoicing_enabled:
			if self.type != "in_invoice":
				dian_document_obj = self.env['account.invoice.dian.document']
				dian_document = dian_document_obj.create({
					'invoice_id': self.id,
					'company_id': self.company_id.id})
				dian_document._set_files()
				dian_document.sent_zipped_file()
				dian_document.GetStatusZip()

		return res

	@api.multi
	def action_cancel(self):
		res = super(AccountInvoice, self).action_cancel()

		for dian_document in self.dian_document_lines:
			if dian_document.state == 'done':
				raise UserError('You cannot cancel a invoice sent to DIAN')
			else:
				dian_document

		return res

	def _get_active_dian_resolution(self):
		msg1 = _("Your active dian resolution has no technical key, " +
				 "contact with your administrator.")
		msg2 = _("You do not have an active dian resolution, " +
				 "contact with your administrator.")
		resolution_number = False

		for date_range_id in self.journal_id.sequence_id.date_range_ids:
			if date_range_id.active_resolution:
				resolution_number = date_range_id.resolution_number
				date_from = date_range_id.date_from
				date_to = date_range_id.date_to
				number_from = date_range_id.number_from
				number_to = date_range_id.number_to

				if not date_range_id.technical_key:
					raise UserError(msg1)

				technical_key = date_range_id.technical_key
				break

		if not resolution_number:
			raise UserError(msg2)

		return {
			'InvoiceAuthorization': resolution_number,
			'StartDate': date_from,
			'EndDate': date_to,
			'Prefix': self.journal_id.sequence_id.prefix or '',
			'From': number_from,
			'To': number_to,
			'technical_key': technical_key}

	def _get_billing_reference(self):
		billing_reference = {}

		for origin_invoice in self.origin_invoice_ids:
			if origin_invoice.state in ('open', 'paid'):
				for dian_document in origin_invoice.dian_document_lines:
					if dian_document.state == 'done':
						billing_reference['ID'] = origin_invoice.number
						billing_reference['UUID'] = dian_document.cufe_cude
						billing_reference['IssueDate'] = origin_invoice.date_invoice

		if not billing_reference:
			raise UserError('Credit Note has not Billing Reference')
		else:
			return billing_reference

	def _get_payment_exchange_rate(self):
		company_currency = self.company_id.currency_id
		rate = 1
		date = self._get_currency_rate_date() or fields.Date.context_today(self)

		if self.currency_id != company_currency:
			currency =self.currency_id.with_context(date=date)
			rate = currency.compute(rate, company_currency)

		return {
			'SourceCurrencyCode': self.currency_id.name,
			'TargetCurrencyCode': company_currency.name,
			'CalculationRate': rate,
			'Date': date}

	def _get_einvoicing_taxes(self):
		msg1 = _("Your tax: '%s', has no e-invoicing tax group type, " +
				 "contact with your administrator.")
		msg2 = _("Your withholding tax: '%s', has positive amount, the taxes " +
		         "must have negative amount, contact with your administrator.")
		msg3 = _("Your tax: '%s', has negative amount, the taxes must have " + 
		         "positive amount, with your administrator.")
		taxes = {}
		withholding_taxes= {}

		for tax in self.tax_line_ids:
			if tax.tax_id.tax_group_id.is_einvoicing:
				if not tax.tax_id.tax_group_id.tax_group_type_id:
					raise UserError(msg1 % tax.name)

				tax_code = tax.tax_id.tax_group_id.tax_group_type_id.code
				tax_name = tax.tax_id.tax_group_id.tax_group_type_id.name
				tax_type = tax.tax_id.tax_group_id.tax_group_type_id.type

				if tax_type == 'withholding_tax':
					if tax.tax_id.amount < 0:
						tax_percent = '{:.2f}'.format(tax.tax_id.amount * (-1))
					else:
						raise UserError(msg2 % tax.name)

					if tax_code not in withholding_taxes:
						withholding_taxes[tax_code] = {}
						withholding_taxes[tax_code]['total'] = 0
						withholding_taxes[tax_code]['name'] = tax_name
						withholding_taxes[tax_code]['taxes'] = {}

					if tax_percent not in withholding_taxes[tax_code]['taxes']:
						withholding_taxes[tax_code]['taxes'][tax_percent] = {}
						withholding_taxes[tax_code]['taxes'][tax_percent]['base'] = 0
						withholding_taxes[tax_code]['taxes'][tax_percent]['amount'] = 0

					withholding_taxes[tax_code]['total'] += tax.amount * (-1)
					withholding_taxes[tax_code]['taxes'][tax_percent]['base'] += tax.base
					withholding_taxes[tax_code]['taxes'][tax_percent]['amount'] += tax.amount * (-1)
				else:
					if tax.tax_id.amount > 0:
						tax_percent = '{:.2f}'.format(tax.tax_id.amount)
					else:
						raise UserError(msg3 % tax.name)

					if tax_code not in taxes:
						taxes[tax_code] = {}
						taxes[tax_code]['total'] = 0
						taxes[tax_code]['name'] = tax_name
						taxes[tax_code]['taxes'] = {}

					if tax_percent not in taxes[tax_code]['taxes']:
						taxes[tax_code]['taxes'][tax_percent] = {}
						taxes[tax_code]['taxes'][tax_percent]['base'] = 0
						taxes[tax_code]['taxes'][tax_percent]['amount'] = 0

					taxes[tax_code]['total'] += tax.amount
					taxes[tax_code]['taxes'][tax_percent]['base'] += tax.base
					taxes[tax_code]['taxes'][tax_percent]['amount'] += tax.amount

		if '01' not in taxes:
			taxes['01'] = {}
			taxes['01']['total'] = 0
			taxes['01']['name'] = 'IVA'
			taxes['01']['taxes'] = {}
			taxes['01']['taxes']['0.00'] = {}
			taxes['01']['taxes']['0.00']['base'] = 0
			taxes['01']['taxes']['0.00']['amount'] = 0

		if '04' not in taxes:
			taxes['04'] = {}
			taxes['04']['total'] = 0
			taxes['04']['name'] = 'ICA'
			taxes['04']['taxes'] = {}
			taxes['04']['taxes']['0.00'] = {}
			taxes['04']['taxes']['0.00']['base'] = 0
			taxes['04']['taxes']['0.00']['amount'] = 0

		if '03' not in taxes:
			taxes['03'] = {}
			taxes['03']['total'] = 0
			taxes['03']['name'] = 'INC'
			taxes['03']['taxes'] = {}
			taxes['03']['taxes']['0.00'] = {}
			taxes['03']['taxes']['0.00']['base'] = 0
			taxes['03']['taxes']['0.00']['amount'] = 0

		if '06' not in withholding_taxes:
			withholding_taxes['06'] = {}
			withholding_taxes['06']['total'] = 0
			withholding_taxes['06']['name'] = 'ReteRenta'
			withholding_taxes['06']['taxes'] = {}
			withholding_taxes['06']['taxes']['0.00'] = {}
			withholding_taxes['06']['taxes']['0.00']['base'] = 0
			withholding_taxes['06']['taxes']['0.00']['amount'] = 0

		return {'TaxesTotal': taxes, 'WithholdingTaxesTotal': withholding_taxes}

	def _get_invoice_lines(self):
		msg1 = _("Your tax: '%s', has no e-invoicing tax group type, " +
				 "contact with your administrator.")
		msg2 = _("Your withholding tax: '%s', has positive amount, the withholding " +
				 "taxes must have negative amount, contact with your administrator.")
		msg3 = _("Your tax: '%s', has negative amount, the taxes must have " + 
		         "positive amount, contact with your administrator.")
		invoice_lines = {}
		count = 1

		for invoice_line in self.invoice_line_ids:
			disc_amount = 0
			total_wo_disc = 0

			if invoice_line.price_subtotal != 0 and invoice_line.discount != 0:
				disc_amount = (invoice_line.price_subtotal * invoice_line.discount ) / 100

			if invoice_line.price_unit != 0 and invoice_line.quantity != 0:
				total_wo_disc = invoice_line.price_unit * invoice_line.quantity

			invoice_lines[count] = {}
			invoice_lines[count]['Quantity'] = '{:.2f}'.format(
				invoice_line.quantity)
			invoice_lines[count]['LineExtensionAmount'] = '{:.2f}'.format(
				invoice_line.price_subtotal)
			invoice_lines[count]['MultiplierFactorNumeric'] = '{:.2f}'.format(
				invoice_line.discount)
			invoice_lines[count]['AllowanceChargeAmount'] = '{:.2f}'.format(
				disc_amount)
			invoice_lines[count]['AllowanceChargeBaseAmount'] = '{:.2f}'.format(
				total_wo_disc)
			invoice_lines[count]['TaxesTotal'] = {}
			invoice_lines[count]['WithholdingTaxesTotal'] = {}

			for tax in invoice_line.invoice_line_tax_ids:
				if tax.amount_type == 'group':
					tax_ids = tax.children_tax_ids
				else:
					tax_ids = tax

				for tax_id in tax_ids:
					if tax_id.tax_group_id.is_einvoicing:
						if not tax_id.tax_group_id.tax_group_type_id:
							raise UserError(msg1 % tax.name)

						tax_type = tax_id.tax_group_id.tax_group_type_id.type

						if tax_type == 'withholding_tax':
							if tax_id.amount < 0:
								invoice_lines[count]['WithholdingTaxesTotal'] = (
									invoice_line._get_invoice_lines_taxes(
										tax_id,
										tax_id.amount * (-1),
										invoice_lines[count]['WithholdingTaxesTotal']))
							else:
								raise UserError(msg2 % tax_id.name)
						else:
							if tax_id.amount > 0:
								invoice_lines[count]['TaxesTotal'] = (
									invoice_line._get_invoice_lines_taxes(
										tax_id,
										tax_id.amount,
										invoice_lines[count]['TaxesTotal']))
							else:
								raise UserError(msg3 % tax_id.name)

			if '01' not in invoice_lines[count]['TaxesTotal']:
				invoice_lines[count]['TaxesTotal']['01'] = {}
				invoice_lines[count]['TaxesTotal']['01']['total'] = 0
				invoice_lines[count]['TaxesTotal']['01']['name'] = 'IVA'
				invoice_lines[count]['TaxesTotal']['01']['taxes'] = {}
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00'] = {}
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00']['base'] = invoice_line.price_subtotal
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00']['amount'] = 0
			'''
			if '04' not in invoice_lines[count]['TaxesTotal']:
				invoice_lines[count]['TaxesTotal']['04'] = {}
				invoice_lines[count]['TaxesTotal']['04']['total'] = 0
				invoice_lines[count]['TaxesTotal']['04']['name'] = 'ICA'
				invoice_lines[count]['TaxesTotal']['04']['taxes'] = {}
				invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00'] = {}
				invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00']['base'] = invoice_line.price_subtotal
				invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00']['amount'] = 0

			if '03' not in invoice_lines[count]['TaxesTotal']:
				invoice_lines[count]['TaxesTotal']['03'] = {}
				invoice_lines[count]['TaxesTotal']['03']['total'] = 0
				invoice_lines[count]['TaxesTotal']['03']['name'] = 'INC'
				invoice_lines[count]['TaxesTotal']['03']['taxes'] = {}
				invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00'] = {}
				invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00']['base'] = invoice_line.price_subtotal
				invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00']['amount'] = 0
			'''
			if '06' not in invoice_lines[count]['WithholdingTaxesTotal']:
				invoice_lines[count]['WithholdingTaxesTotal']['06'] = {}
				invoice_lines[count]['WithholdingTaxesTotal']['06']['total'] = 0
				invoice_lines[count]['WithholdingTaxesTotal']['06']['name'] = 'ReteRenta'
				invoice_lines[count]['WithholdingTaxesTotal']['06']['taxes'] = {}
				invoice_lines[count]['WithholdingTaxesTotal']['06']['taxes']['0.00'] = {}
				invoice_lines[count]['WithholdingTaxesTotal']['06']['taxes']['0.00']['base'] = invoice_line.price_subtotal
				invoice_lines[count]['WithholdingTaxesTotal']['06']['taxes']['0.00']['amount'] = 0

			invoice_lines[count]['ItemDescription'] = invoice_line.name
			invoice_lines[count]['PriceAmount'] = '{:.2f}'.format(
				invoice_line.price_unit)

			count += 1

		return invoice_lines
