# Copyright 2018 Joan Marín <Github@JoanMarin>
# Copyright 2018 Guillermo Montoya <Github@guillermm>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    isic_id = fields.Many2many(
        string="Economic Activity (ISIC)",
        relation="res_partner_isic_rel",
        comodel_name="res.partner.isic",
        domain=[("type", "!=", "view")],
        help="Uniform international industrial code (ISIC)",
        ondelete="cascade",
    )
