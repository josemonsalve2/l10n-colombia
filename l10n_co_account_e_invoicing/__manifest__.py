# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Colombian Account E-Invoicing",
    "category": "E-Invoicing",
    "version": "10.0.1.0.0",
    "author": "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@JoanMarin",
    "website": "https://github.com/odooloco/l10n-colombia",
    "license": "AGPL-3",
    "summary": "Colombian Account E-Invoicing",
    "depends": [
        "l10n_co_account_fiscal_position_party_tax_scheme",
        "l10n_co_account_invoice_discrepancy_response",
        "l10n_co_account_invoice_payment_mean",
        "l10n_co_account_tax_group_type",
        "l10n_co_base_location",
        "l10n_co_partner_isic",
        "l10n_co_partner_person_type",
        "l10n_co_product_uom",
        "l10n_co_sequence_resolution",
        "account_invoice_refund_link",
        "account_fiscal_year",
        "partner_coc",
        "partner_commercial_name",
        "product_brand",
        "product_manufacturer",
        "sale",
    ],
    'external_dependencies': {
        'python': [
            'OpenSSL',
            'xades',
        ],
    },
    "data": [
        'security/ir.model.access.csv',
        'data/ir_module_category_data.xml',
        'data/res_groups_data.xml',
        'data/product_scheme_data.xml',
        'data/ir_cron_data.xml',
        "views/account_invoice_views.xml",
        "views/account_invoice_dian_document_views.xml",
        "views/account_tax_group_views.xml",
        "views/date_range_views.xml",
        "views/ir_sequence_views.xml",
        "views/product_template_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "report/account_invoice_mail_template.xml",
        "report/account_invoice_report_template.xml",
    ],
    "installable": True,
}
