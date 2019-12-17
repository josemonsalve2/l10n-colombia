# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Colombian E-Invoicing",
    "category": "Financial",
    "version": "10.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@joanmarin",
    "website": "http://www.exaap.com",
    "license": "AGPL-3",
    "summary": "Colombian E-Invoicing",
    "depends": [
        "l10n_co_account_fiscal_position_party_tax_scheme",
        "l10n_co_account_invoice_discrepancy_response",
        "l10n_co_account_invoice_payment_mean",
        "l10n_co_account_tax_group_type",
        "l10n_co_base_location",
        "l10n_co_partner_person_type",
        "l10n_co_partner_vat",
        "l10n_co_sequence_resolution",
        "account_invoice_refund_link",
        "base_iso3166",
    ],
    'external_dependencies': {
        'python': [
            'validators',
            'OpenSSL',
            'xades',
        ],
    },
    "data": [
        'security/ir.model.access.csv',
        "views/account_invoice_views.xml",
        "views/account_invoice_dian_document_views.xml",
        "views/ir_sequence_views.xml",
        "views/res_company_views.xml",
        "views/account_tax_group_views.xml"
    ],
    "installable": True,
}
