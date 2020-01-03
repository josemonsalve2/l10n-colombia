# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
	_inherit = 'account.fiscal.position'

	tax_level_code_ids = fields.Many2many(
		'account.fiscal.position.tax.level.code',
		relation = 'account_fiscal_position_tax_level_code_rel',
        column1 = 'account_fiscal_position_id',
        column2 = 'tax_level_code_id',
		string='Fiscal Responsibilities (TaxLevelCode)')
	tax_scheme_id = fields.Many2one(
		comodel_name='account.fiscal.position.tax.scheme',
		string='Fiscal Responsibility (TaxScheme)')
