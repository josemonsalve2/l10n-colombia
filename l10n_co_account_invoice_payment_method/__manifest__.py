# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Formas y medios de pago para la localizacion Colombiana",
    "version": "17.0.1.0.0",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Alejandro Olano Github@alejo-code, "
    "Juan Camilo Zuluaga Serna Github@camilozuluaga, "
    "Joan Marín Github@JoanMarin",
    "category": "Localization",
    "license": "AGPL-3",
    "summary": "Este módulo tiene las formas y medios de pago identificados "
    "por la DIAN para la localizacion Colombiana",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_payment_method_data.xml",
        "data/account_payment_method_code_data.xml",
        "views/account_payment_method_views.xml",
        "views/account_payment_method_code_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
