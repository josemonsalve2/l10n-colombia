# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class AccountFiscalPosition(models.Model):
	_inherit = 'account.fiscal.position'

	list_name_id = fields.Many2one(
		comodel_name='account.fiscal.position.list.name',
		string = 'Fiscal Regime')
