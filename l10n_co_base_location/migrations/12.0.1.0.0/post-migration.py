# Copyright 2021 Alejandro Olano <Github@alejo-code>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):

    openupgrade.logged_query(
        env.cr, """
        UPDATE res_city rbz
		SET code = rc.code
        FROM res_better_zip rc
        WHERE rc.id = rbz.id""")

    openupgrade.logged_query(
        env.cr, """
        UPDATE res_city rbz
		SET phone_prefix = rc.phone_prefix
        FROM res_better_zip rc
        WHERE rc.id = rbz.id""")
