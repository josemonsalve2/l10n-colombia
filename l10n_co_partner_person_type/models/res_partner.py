# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    person_type = fields.Selection(
        selection=[("1", "Juridical Person"), ("2", "Natural Person")],
        string="Person Type",
        help="""This field is in sync with the 'Company Type' field.
        This field is used for the Colombian localization to transmit this information to DIAN.""",
    )

    @api.onchange("person_type")
    def onchange_person_type(self):
        if self.person_type == "1":
            self.company_type = "company"
        elif self.person_type == "2":
            self.company_type = "person"

    @api.onchange("company_type")
    def onchange_company_type(self):
        if self.company_type == "company":
            self.person_type = "1"
        elif self.company_type == "person":
            self.person_type = "2"
