# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
	_inherit = 'account.fiscal.position'

	person_type = fields.Selection(
        [("1", "Juridical Person and assimilated"), ("2", "Natural Person and assimilated")],
        string="Person Type")
