# Copyright 2019 Joan Marín <Github@Diegoivanc>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    commercial_name = fields.Char(string="Commercial Name")
    fax = fields.Char(string="Fax")

    @api.depends(
        "is_company",
        "name",
        "parent_id.name",
        "type",
        "company_name",
        "commercial_name",
    )
    def _compute_display_name(self):
        return super()._compute_display_name()
