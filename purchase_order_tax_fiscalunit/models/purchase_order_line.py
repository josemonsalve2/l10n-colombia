# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _compute_tax_id(self):
        super(PurchaseOrderLine, self)._compute_tax_id()
        order_id = False

        for line in self:
            if line.order_id != order_id:
                remove_tax_groups_ids = line.order_id.check_base_to_overcome()
                order_id = line.order_id

            line.recalculate_taxes(remove_tax_groups_ids, line.taxes_id)

        return True

    @api.multi
    def _recompute_tax_id(self):
        order_id = False
        remove_tax_groups_ids = False
        taxes = False

        for line in self:
            old_taxes = line.taxes_id
            fpos = (line.order_id.fiscal_position_id
                or line.order_id.partner_id.property_account_position_id)
            # If company_id is set, always filter taxes by the company
            taxes =  line.product_id.supplier_taxes_id.filtered(
                lambda r: not line.company_id or r.company_id == line.company_id)
            taxes = fpos.map_tax(
                taxes,
                line.product_id,
                line.order_id.partner_id) if fpos else taxes
            line.taxes_id = taxes | old_taxes

        for line in self:
            if line.order_id != order_id:
                remove_tax_groups_ids = line.order_id.check_base_to_overcome()
                order_id = line.order_id
        
            taxes = line.taxes_id
            line.recalculate_taxes(remove_tax_groups_ids, taxes)

        return True

    @api.multi
    def recalculate_taxes(self, remove_tax_groups_ids, taxes):
        """Updates taxes on all order lines"""
        self.ensure_one()
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
            self.taxes_id = [(6, 0, set(taxes_ids))]

        return True
