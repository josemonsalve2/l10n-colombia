# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
	"name": "Conceptos de corrección para facturas rectificativas "
			"para la localizacion Colombiana",
	"version": "10.0.1.0.0",
	"website": "https://github.com/odooloco/l10n-colombia",
	"author": "Juan Camilo Zuluaga Serna Github@camilozuluaga, "
              "Joan Marín Github@JoanMarin",
	"category": "Localization",
	"summary": "Este módulo tiene los conceptos de corrección para facturas "
			   "rectificativas identificados por la DIAN para la localizacion Colombiana",
	"depends": [
		"account"
	],
	"data": [
		"security/ir.model.access.csv",
		"data/account_invoice_discrepancy_response_code_data.xml",
		"views/account_invoice_discrepancy_response_code_views.xml",
		"views/account_invoice_views.xml",
	],
	"installable": True,
}
