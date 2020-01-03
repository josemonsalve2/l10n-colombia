# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
	_inherit = "res.partner"

	def _get_information_content_provider_party_values(self):
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
