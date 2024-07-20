# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Responsabilidades Fiscales para la localizacion Colombiana",
    "version": "17.0.1.0.0",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Juan Camilo Zuluaga Serna Github@camilozuluaga, "
    "Joan Marín Github@JoanMarin, "
    "Alejandro Olano Github@alejo-code",
    "category": "Localization",
    "summary": "Este módulo tiene las responsabilidades fiscales identificados "
    "por la DIAN para la localizacion Colombiana",
    "depends": [
        "l10n_co_account_tax_group_type",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_fiscal_position_party_tax_scheme_data.xml",
        "data/account_fiscal_position_tax_level_code_data.xml",
        "views/account_fiscal_position_party_tax_scheme_views.xml",
        "views/account_fiscal_position_tax_level_code_views.xml",
        "views/account_fiscal_position_views.xml",
    ],
    "installable": True,
}
