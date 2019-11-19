# -*- coding: utf-8 -*-
# Copyright 2018 Dominic Krimmer
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    technical_key = fields.Char(string="Technical Key")
