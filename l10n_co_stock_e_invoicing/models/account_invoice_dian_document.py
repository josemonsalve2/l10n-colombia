# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.exceptions import UserError


class AccountInvoiceDianDocument(models.Model):
    _inherit = "account.invoice.dian.document"

    def _get_xml_values(self, ClTec):
        msg1 = _("The export bill must have an incoterm DIAN established.")
        msg2 = _("'%s', must have a brand established.")
        msg3 = _("'%s', must have a ref of manufacturer established.")
        res = super(AccountInvoiceDianDocument, self)._get_xml_values(ClTec)

        if self.invoice_id.invoice_type_code == '02':
            if not self.invoice_id.incoterms_id and not self.invoice_id.incoterms_id.is_einvoicing:
                raise UserError(msg1)
            else:
                res['DeliveryTerms'] = {
                    'LossRiskResponsibilityCode': self.invoice_id.incoterms_id.code,
                    'LossRisk': self.invoice_id.incoterms_id.name}

            for invoice_line in self.invoice_id.invoice_line_ids:
                if not invoice_line.product_id.product_brand_id:
                    raise UserError(msg2 % invoice_line.name)

                if not invoice_line.product_id.manufacturer_pref:
                    raise UserError(msg3 % invoice_line.name)

        return res
