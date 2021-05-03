# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Uom(models.Model):
    _inherit = 'uom.uom'

    product_uom_code_id = fields.Many2one(comodel_name='uom.uom.code',
                                          string='Unit of Measure Code')
