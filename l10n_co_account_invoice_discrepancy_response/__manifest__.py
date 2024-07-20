# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Conceptos de corrección para facturas rectificativas "
    "para la localizacion Colombiana",
    "version": "12.0.1.0.0",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Alejandro Olano Github@alejo-code, "
    "Juan Camilo Zuluaga Serna Github@camilozuluaga, "
    "Joan Marín Github@JoanMarin, ",
    "category": "Localization",
    "summary": "Este módulo tiene los conceptos de corrección para facturas "
    "rectificativas identificados por la DIAN para la localizacion Colombiana",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_invoice_discrepancy_response_code_data.xml",
        "wizards/account_invoice_debit_note.xml",
        "wizards/account_invoice_refund.xml",
        "views/account_invoice_discrepancy_response_code_views.xml",
        "views/account_invoice_views.xml",
        "views/account_journal_views.xml",
    ],
    "installable": True,
}
