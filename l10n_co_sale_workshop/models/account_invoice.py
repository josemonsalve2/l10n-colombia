# -*- coding: utf-8 -*-
# Copyright 2018 Joan Marín <Github@joanodoo>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    vehicle_id = fields.Many2one(
        string='Plate',
        comodel_name='fleet.vehicle',
        help='Vehicle plate associated with the order')

    service_card = fields.Char(string='Service Card',
                               size=64,
                               help='Internal Work Order')

    control_number = fields.Char(string='Control Number', size=64)
