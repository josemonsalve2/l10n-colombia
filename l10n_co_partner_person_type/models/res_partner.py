# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class ResPartner(models.Model):
	_inherit = "res.partner"

	person_type = fields.Selection([
        ("1", "Juridical Person and assimilated"),
        ("2", "Natural Person and assimilated")], string="Person Type")

	@api.onchange("person_type")
	def onchange_person_type(self):
		if self.person_type == "1":
			self.company_type = "company"
		elif self.person_type == "2":
			self.company_type = "person"
