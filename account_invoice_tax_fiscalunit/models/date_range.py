# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import odoo.addons.decimal_precision as dp

class DateRange(models.Model):
    _inherit = 'date.range'

    fiscalunit = fields.Float(
    	string = 'Fiscal Unit', 
    	help = 'Value of Fiscal Unit as the Colombian UVT',
    	digits = dp.get_precision('Fiscal Unit'))
