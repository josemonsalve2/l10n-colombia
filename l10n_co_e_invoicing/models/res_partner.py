# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
	_inherit = "res.partner"

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

		if not self.person_type:
			raise UserError(msg1 % self.name)

		if self.country_id:
			if self.country_id.code == 'CO' and not self.zip_id:
				raise UserError(msg2 % self.name)
			elif self.country_id.code == 'CO' and not self.state_id:
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
			if (not self.property_account_position_id.tax_level_code_id
					or not self.property_account_position_id.tax_scheme_id):
				raise UserError(msg8 % self.name)
		else:
			raise UserError(msg9 % self.name)

		return {
			'AdditionalAccountID': self.person_type,
			'Name': self.name,
			'AddressID': self.zip_id.code,
			'AddressCityName': self.zip_id.city,
			'AddressPostalZone': self.zip_id.name,
			'AddressCountrySubentity': self.state_id.name,
			'AddressCountrySubentityCode': self.state_id.code,
			'AddressLine': self.street or '',
			'CompanyIDschemeID': self.check_digit,
			'CompanyIDschemeName': self.document_type_id.code,
			'CompanyID': self.identification_document,
			'TaxLevelCode': self.property_account_position_id.tax_level_code_id.code,
			'TaxSchemeID': self.property_account_position_id.tax_scheme_id.code,
			'TaxSchemeName': self.property_account_position_id.tax_scheme_id.name,
			'CorporateRegistrationSchemeName': self.ref,
			'CountryIdentificationCode': self.country_id.code,
			'CountryName': self.country_id.name}

	def _get_tax_representative_party_values(self):
		return {
			'IDschemeID': self.check_digit,
			'IDschemeName': self.document_type_id.code,
			'ID': self.identification_document}
