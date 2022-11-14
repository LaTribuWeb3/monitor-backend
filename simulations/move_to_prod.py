import utils
import datetime
import json


def compare_prod_to_last(SITE_ID, name):
    prod_version = utils.get_prod_version(name)
    prod_file = json.loads(utils.get_git_json_file(SITE_ID, prod_version, "usd_volume_for_slippage.json"))
    last_version_name, last_versio_date = utils.get_latest_folder_name(SITE_ID)
    last_file = json.loads(utils.get_git_json_file(SITE_ID, last_version_name, "usd_volume_for_slippage.json"))
    for key1 in prod_file:
        if key1 == "json_time": continue
        for key2 in prod_file[key1]:
            change = 100 * (round( (last_file[key1][key2]["volume"] / prod_file[key1][key2]["volume"]) - 1, 2))
            if abs(change) > 2:
                message = f"{key1} {key2}  Liquidity Change (%) {round(change,2)}"
                print(message)
                #utils.send_telegram_alert(bot_id, chat_id, message)
            #print(key1, key2, "Change", change)


def update_site(SITE_ID, name):
    max_folder_name, max_folder_date = utils.get_latest_folder_name(SITE_ID)
    print(SITE_ID, max_folder_name, datetime.datetime.now() - max_folder_date)
    if update:
        utils.move_to_prod(name, max_folder_name)
        print(SITE_ID, "Git updated")


update = True

# update_site("0", "aurigami")
# update_site("1", "nervos")
# update_site("2", "vesta")
# update_site("gearbox/main", "gearbox")
# update_site("4", "agave")

bot_id = "5789083655:AAH25Cl4ZZ5aGL3PEq0LJlNOvDR8k4a1cK4"
chat_id = "-1001804080202"
message = "Test From Code"

# utils.send_telegram_alert(bot_id, chat_id, message)
# compare_prod_to_last("2", "vesta")

# utils.create_production_accounts_graph("0", "total_collateral", "Aurigami", "auUSDC")
# utils.create_production_accounts_graph("0", "total_debt", "Aurigami", "auUSDC")
#
# utils.create_production_accounts_graph("0", "total_collateral", "Aurigami", "auWBTC")
# utils.create_production_accounts_graph("0", "total_debt", "Aurigami", "auWBTC")
#
# utils.create_production_accounts_graph("0", "total_collateral", "Aurigami")
# utils.create_production_accounts_graph("0", "total_debt", "Aurigami")
#
# utils.create_production_accounts_graph("2", "total_collateral", "Vesta")
# utils.create_production_accounts_graph("2", "total_debt", "Vesta")
#
utils.create_production_slippage_graph("0", "Aurigami")
utils.create_production_slippage_graph("2", "Vesta")


# print(utils.get_latest_folder_name("gearbox/main"))
