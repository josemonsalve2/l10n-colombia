# Copyright 2018-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(
        env.cr,
        {
            "product_uom": [
                ("product_uom_code_id", "uom_code_id"),
            ]
        },
    )
    openupgrade.remove_tables_fks(env.cr, ["product_uom_code"])
