# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    dian_type = fields.Selection(
        string='DIAN Type',
        related='sequence_id.dian_type',
        store=False)
    technical_key = fields.Char(string="Technical Key")
