# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockIncoterms(models.Model):
	_inherit = "stock.incoterms"

	is_einvoicing = fields.Boolean(string="Does it Apply for E-Invoicing?")

	def name_get(self):
		res = []
		for record in self:
			if record.is_einvoicing:
				name = u'[DIAN][%s] %s' % (record.code or '', record.name or '')
			else:
				name = u'[%s] %s' % (record.code or '', record.name or '')
			res.append((record.id, name))

		return res
