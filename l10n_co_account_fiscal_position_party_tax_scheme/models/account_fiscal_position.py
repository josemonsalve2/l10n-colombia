# Copyright 2021 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    listname = fields.Selection(
        selection=[
            ("48", "Responsable del impuesto sobre las ventas - IVA"),
            ("49", "No responsable de IVA"),
        ],
        string="Fiscal Regime",
        default=False,
    )
    tax_level_code_ids = fields.Many2many(
        comodel_name="account.fiscal.position.tax.level.code",
        relation="account_fiscal_position_tax_level_code_rel",
        column1="account_fiscal_position_id",
        column2="tax_level_code_id",
        string="Fiscal Responsibilities (TaxLevelCode)",
    )
    party_tax_scheme_id = fields.Many2one(
        comodel_name="account.fiscal.position.party.tax.scheme",
        string="Fiscal Responsibilities (PartyTaxScheme)",
    )
