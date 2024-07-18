# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE uom_code rbz
		SET name = rc.name
        FROM product_uom_code rc
        WHERE rc.id = rbz.id""",
    )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE uom_code rbz
		SET code = rc.code
        FROM product_uom_code rc
        WHERE rc.id = rbz.id""",
    )
