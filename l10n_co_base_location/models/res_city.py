# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"
    phone_prefix = fields.Char(string="Phone Prefix")
    code = fields.Char(
        string="City Code", size=64, help="The official code for the city"
    )
