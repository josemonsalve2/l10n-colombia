# Copyright 2021 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPositionPartyTaxScheme(models.Model):
    _name = "account.fiscal.position.party.tax.scheme"
    _description = "Fiscal Responsibilities (PartyTaxScheme)"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
