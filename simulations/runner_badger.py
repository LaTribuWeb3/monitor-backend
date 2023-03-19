import base_runner
import utils
import os
import json
import time
import copy
import curve_lion


def create_simulation_config(SITE_ID, c, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names):
    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "simulation_configs.json", "w")
    print("create_simulation_config")

    f2 = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json")
    jj2 = json.load(f2)
    data = {"json_time": time.time()}
    now_time = time.time()

    for base_to_simulation in assets_to_simulate:
        for volume_for_slippage_10_percents in c["volume_for_slippage_10_percentss"]:
            key = base_to_simulation + "-" + quote_to_simulate + "*" + str(volume_for_slippage_10_percents)
            new_c = copy.deepcopy(c)
            std_ratio = jj2[assets_aliases[base_to_simulation]][quote_to_simulate]
            li = float(liquidation_incentive[inv_names[base_to_simulation]])
            li = li if li < 1 else li - 1
            new_c["liquidation_incentives"] = [li]
            new_c["series_std_ratio"] = std_ratio
            new_c["json_time"] = now_time
            new_c["volume_for_slippage_10_percentss"] = [volume_for_slippage_10_percents]

            data[key] = new_c
    json.dump(data, fp)


fast_mode = False
print_time_series = True
ETH_PRICE = 1600
total_jobs = 12
assets_to_simulate = ["ETH"]
quote_to_simulate = "BTC"

inv_names = {}
liquidation_incentive = {}
inv_underlying = {}
underlying = {}
decimals = {}
assets_aliases = {}
collateral_factors = {}

c = {
    "series_std_ratio": 1,
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [0],
    'liquidation_incentives': [0.1],
    "collateral_factor": 0,
    'trade_every': 1800,
    "const_crs": [0],
    "collaterals": [50_000_000 / ETH_PRICE],
    "min_crs": [0, 1.03, 1.05],
    'volume_for_slippage_10_percentss': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
    "l_factors": [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
    "box_initial_balances": [0.1, 0.25, 0.5, 0.75, 1],
    "box_recovery_halflifes": [0.001, 0.5, 1, 2, 4, 5]
}

for a in assets_to_simulate:
    inv_names[a] = a
    liquidation_incentive[a] = 1
    inv_underlying[a] = a
    underlying[a] = a
    decimals[a] = 0
    assets_aliases[a] = a
    collateral_factors[a] = 1

if fast_mode:
    c["collaterals"][0] /= 50

SITE_ID = "badger"
SITE_ID = utils.get_site_id(SITE_ID)

base_runner.create_assets_std_ratio_information(SITE_ID, ["ETH", "BTC"],[("09", "2022"), ("10", "2022"), ("11", "2022")])

create_simulation_config(SITE_ID, c, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names)
base_runner.create_simulation_results(SITE_ID, ETH_PRICE, total_jobs, collateral_factors, inv_names, print_time_series,
                                      fast_mode)
