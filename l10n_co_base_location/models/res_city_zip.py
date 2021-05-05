# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCityZip(models.Model):
    _inherit = "res.city.zip"
    phone_prefix = fields.Char(string='Phone Prefix',
                               related='city_id.phone_prefix')
    code = fields.Char(string='City Code',
                       size=64,
                       related='city_id.code',
                       help="The official code for the city")
