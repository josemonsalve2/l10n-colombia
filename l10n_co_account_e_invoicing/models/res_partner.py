# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import re

class ResPartner(models.Model):
	_inherit = "res.partner"

	send_zip_code = fields.Boolean(string='Send Zip Code?')
	is_einvoicing_agent = fields.Selection(
        [('no', 'No'),
         ('yes', 'Yes'),
         ('unknown', 'Unknown')],
        string='Is E-Invoicing Agent?',
        default=False)
	einvoicing_email = fields.Char(string='E-Invoicing Email')
	view_einvoicing_email_field = fields.Boolean(
		string="View E-Invoicing Email Fields",
		compute='_get_view_einvoicing_email_field',
		store=False)

	@api.multi
	def _get_view_einvoicing_email_field(self):
		user = self.env['res.users'].search([('id', '=', self._uid)])
		view_einvoicing_email_field = False

		if user.has_group('l10n_co_account_e_invoicing.group_view_einvoicing_email_fields'):
			view_einvoicing_email_field = True

		for partner in self:
			partner.view_einvoicing_email_field = view_einvoicing_email_field

	@api.constrains('einvoicing_email')
	@api.onchange('einvoicing_email')
	def validate_mail(self):
	   if self.einvoicing_email:
			match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", self.einvoicing_email)
			if match == None:
				raise ValidationError(_('The field "E-invoicing email" is not correctly filled.\n\n'+
										'Please add @ and dot (.)'))

	def _get_accounting_partner_party_values(self):
		msg1 = _("'%s' does not have a person type established.")
		msg2 = _("'%s' does not have a city established.")
		msg3 = _("'%s' does not have a state established.")
		msg4 = _("'%s' does not have a country established.")
		msg5 = _("'%s' does not have a verification digit established.")
		msg6 = _("'%s' does not have a document type established.")
		msg7 = _("'%s' does not have a identification document established.")
		msg8 = _("'%s' does not have a fiscal position correctly configured.")
		msg9 = _("'%s' does not have a fiscal position established.")
		msg10 = _("E-Invoicing Agent: '%s' does not have a E-Invoicing Email.")
		zip_code = False
		tax_level_codes = ''
		first_name = False
		family_name = False
		middle_name = False
		telephone = False

		if not self.person_type:
			raise UserError(msg1 % self.name)

		if self.country_id:
			if self.country_id.code == 'CO':
				if not self.zip_id:
					raise UserError(msg2 % self.name)
				elif not self.state_id:
					raise UserError(msg3 % self.name)
		else:
			raise UserError(msg4 % self.name)

		if self.document_type_id:
			if self.document_type_id.code == '31' and not self.check_digit:
				raise UserError(msg5 % self.name)
		else:
			raise UserError(msg6 % self.name)

		if not self.identification_document:
			raise UserError(msg7 % self.name)

		if self.property_account_position_id:
			if (not self.property_account_position_id.tax_level_code_ids
					or not self.property_account_position_id.tax_scheme_id
					or not self.property_account_position_id.listname):
				raise UserError(msg8 % self.name)
		else:
			raise UserError(msg9 % self.name)

		if ((self.is_einvoicing_agent == 'yes' or not self.is_einvoicing_agent)
				and not self.einvoicing_email):
			raise UserError(msg10 % self.name)

		if self.send_zip_code:
			if self.zip_id:
				zip_code = self.zip_id.name

		for tax_level_code_id in self.property_account_position_id.tax_level_code_ids:
			if tax_level_codes == '':
				tax_level_codes = tax_level_code_id.code
			else:
				tax_level_codes += ';' + tax_level_code_id.code

		if self.firstname:
			first_name = self.firstname
			middle_name = self.othernames
		else:
			first_name = self.othernames

		if self.lastname and self.lastname2:
			family_name = self.lastname + self.lastname2
		elif self.lastname:
			family_name = self.lastname
		elif self.lastname2:
			family_name = self.lastname2

		if self.phone and self.mobile:
			telephone = self.phone + " / " + self.mobile
		elif self.lastname:
			telephone = self.phone
		elif self.lastname2:
			telephone = self.mobile

		return {
			'AdditionalAccountID': self.person_type,
			'PartyName': self.commercial_name,
			'Name': self.name,
			'AddressID': self.zip_id.code,
			'AddressCityName': self.zip_id.city,
			'AddressPostalZone': zip_code,
			'AddressCountrySubentity': self.state_id.name,
			'AddressCountrySubentityCode': self.state_id.code,
			'AddressLine': self.street or '',
			'CompanyIDschemeID': self.check_digit,
			'CompanyIDschemeName': self.document_type_id.code,
			'CompanyID': self.identification_document,
			'listName': self.property_account_position_id.listname,
			'TaxLevelCode': tax_level_codes,
			'TaxSchemeID': self.property_account_position_id.tax_scheme_id.code,
			'TaxSchemeName': self.property_account_position_id.tax_scheme_id.name,
			'CorporateRegistrationSchemeName': self.coc_registration_number,
			'CountryIdentificationCode': self.country_id.code,
			'CountryName': self.country_id.name,
			'FirstName': first_name,
			'FamilyName': family_name,
			'MiddleName': middle_name,
			'Telephone': telephone,
			'Telefax': self.fax,
			'ElectronicMail': self.einvoicing_email}

	def _get_delivery_values(self):
		msg1 = _("'%s' does not have a city established.")
		msg2 = _("'%s' does not have a state established.")
		msg3 = _("'%s' does not have a country established.")
		zip_code = False

		if self.country_id:
			if self.country_id.code == 'CO':
				if not self.zip_id:
					raise UserError(msg1 % self.name)
				elif not self.state_id:
					raise UserError(msg2 % self.name)
		else:
			raise UserError(msg3 % self.name)

		if self.send_zip_code:
			if self.zip_id:
				zip_code = self.zip_id.name

		return {
			'AddressID': self.zip_id.code,
			'AddressCityName': self.zip_id.city,
			'AddressPostalZone': zip_code,
			'AddressCountrySubentity': self.state_id.name,
			'AddressCountrySubentityCode': self.state_id.code,
			'AddressLine': self.street or '',
			'CountryIdentificationCode': self.country_id.code,
			'CountryName': self.country_id.name}

	def _get_tax_representative_party_values(self):
		msg1 = _("'%s' does not have a verification digit established.")
		msg2 = _("'%s' does not have a document type established.")
		msg3 = _("'%s' does not have a identification document established.")

		if self.document_type_id:
			if self.document_type_id.code == '31' and not self.check_digit:
				raise UserError(msg1 % self.name)
		else:
			raise UserError(msg2 % self.name)

		if not self.identification_document:
			raise UserError(msg3 % self.name)

		return {
			'IDschemeID': self.check_digit,
			'IDschemeName': self.document_type_id.code,
			'ID': self.identification_document}
