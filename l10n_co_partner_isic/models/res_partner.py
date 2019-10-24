# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    isic_id = fields.Many2one(
        string = 'Economic Activity (ISIC)',
        comodel_name = 'res.partner.isic',
        domain = [('type', '!=', 'view')],
        help = 'Uniform international industrial code (ISIC)',
        ondelete = 'cascade')
