import utils
import datetime
import json


def update_site(SITE_ID, name):
    max_folder_name, max_folder_date = utils.get_latest_folder_name(SITE_ID)
    print(SITE_ID, max_folder_name, datetime.datetime.now() - max_folder_date)
    if update:
        utils.move_to_prod(name, max_folder_name)
        print(SITE_ID, "Git updated")

update = True
#update_site("0", "aurigami")
update_site("1", "nervos")
update_site("2", "vesta")
update_site("gearbox/main", "gearbox")
update_site("4", "agave")

# utils.move_to_prod("aurigami", '2022-12-14-14-54')

# utils.create_production_accounts_graph("0", "total_collateral", "Aurigami")
# utils.create_production_accounts_graph("0", "total_debt", "Aurigami")
#
# utils.create_production_accounts_graph("2", "total_collateral", "Vesta")
# utils.create_production_accounts_graph("2", "total_debt", "Vesta")
#
# utils.create_production_slippage_graph("0", "Aurigami")
# utils.create_production_slippage_graph("2", "Vesta")
