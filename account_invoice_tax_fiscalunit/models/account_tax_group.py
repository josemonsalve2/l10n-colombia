# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import odoo.addons.decimal_precision as dp

class AccountTaxGroup(models.Model):
	_inherit = "account.tax.group"

	fiscalunit_factor = fields.Float(
		string="Fiscal Unit Factor",
		help="Number of Fiscal Units from which the tax is calculated",
		digits=dp.get_precision("Fiscal Unit"))
