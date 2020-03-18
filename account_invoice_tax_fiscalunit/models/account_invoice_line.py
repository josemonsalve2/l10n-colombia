# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_compare


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def recompute_tax_id(self):
        invoice_id = False
        remove_tax_groups_ids = False
        taxes = False

        for line in self:
            old_taxes = line.invoice_line_tax_ids
            fpos = (line.invoice_id.fiscal_position_id
                    or line.invoice_id.partner_id.property_account_position_id)

            if line.invoice_id.type in ('out_invoice', 'out_refund'):
                taxes = line.product_id.taxes_id or line.account_id.tax_ids
            else:
                taxes = line.product_id.supplier_taxes_id or line.account_id.tax_ids

            # Keep only taxes of the company
            line_company_id = line.company_id or self.env.user.company_id
            taxes = taxes.filtered(
                lambda r, company_id=line_company_id: r.company_id == company_id)
            taxes = fpos.map_tax(
                taxes,
                line.product_id,
                line.invoice_id.partner_id) if fpos else taxes
            line.invoice_line_tax_ids = taxes | old_taxes

        for line in self:
            if line.invoice_id != invoice_id:
                remove_tax_groups_ids = line.invoice_id.check_base_to_overcome()
                invoice_id = line.invoice_id

            taxes = line.invoice_line_tax_ids
            line.recalculate_taxes(remove_tax_groups_ids, taxes)
            incl_tax = taxes.filtered(
                lambda tax: tax not in line.invoice_line_tax_ids and tax.price_include)

            if incl_tax:
                line.recompute_fix_price(taxes, line.invoice_line_tax_ids)

        return True

    def recompute_fix_price(self, taxes, fp_taxes):
        fix_price = self.env['account.tax']._fix_tax_included_price

        if self.invoice_id.type in ('in_invoice', 'in_refund'):
            prec = self.env['decimal.precision'].precision_get('Product Price')

            if (not self.price_unit
                    or float_compare(
                        self.price_unit,
                        self.product_id.standard_price,
                        precision_digits=prec) == 0):
                self.update({
                    'price_unit': fix_price(self.product_id.standard_price, taxes, fp_taxes)})
                self._set_currency()
        else:
            self.update({'price_unit': fix_price(self.product_id.lst_price, taxes, fp_taxes)})
            self._set_currency()

        return True

    def recalculate_taxes(self, remove_tax_groups_ids, taxes):
        """Updates taxes on all invoice lines"""
        taxes_ids = taxes.ids

        for tax in taxes:
            remove_tax_parent = False

            if tax.amount_type == 'group':
                children_taxes_ids = [i.id for i in tax.children_tax_ids]

                for children_tax in tax.children_tax_ids:
                    for tax_group_id in remove_tax_groups_ids:
                        if children_tax.tax_group_id == tax_group_id:
                            children_taxes_ids.remove(children_tax.id)
                            remove_tax_parent = True
                            break

                if children_taxes_ids and remove_tax_parent:
                    taxes_ids += children_taxes_ids
                elif children_taxes_ids and not remove_tax_parent:
                    for children_tax_id in children_taxes_ids:
                        if children_tax_id in taxes_ids:
                            taxes_ids.remove(children_tax_id)

            for tax_group_id in remove_tax_groups_ids:
                if tax.tax_group_id == tax_group_id or remove_tax_parent:
                    if tax.id in taxes_ids:
                        taxes_ids.remove(tax.id)

        if set(taxes.ids) != set(taxes_ids):
            self.update({'invoice_line_tax_ids': [(6, 0, set(taxes_ids))]})

        return True
