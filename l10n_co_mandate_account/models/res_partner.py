# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResPartner(models.Model):
	_inherit = "res.partner"

	is_mandante = fields.Boolean(
        string="Is Mandante?",
        default=False)
