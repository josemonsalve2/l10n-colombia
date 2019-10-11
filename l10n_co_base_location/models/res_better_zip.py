# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin> 
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResBetterZip(models.Model):
    _inherit = "res.better.zip"
    
    phone_prefix = fields.Char('Phone Prefix')
