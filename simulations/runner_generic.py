import base_runner
import utils
import os
import json
import time
import copy


def create_simulation_config(SITE_ID, c, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names):
    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "simulation_configs.json", "w")
    print("create_simulation_config")

    f2 = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json")
    jj2 = json.load(f2)
    data = {"json_time": time.time()}
    now_time = time.time()
    for base_to_simulation in assets_to_simulate:
        key = base_to_simulation + "-" + quote_to_simulate
        new_c = copy.deepcopy(c)
        std_ratio = jj2[assets_aliases[base_to_simulation]][quote_to_simulate]
        li = float(liquidation_incentive[inv_names[base_to_simulation]])
        li = li if li < 1 else li - 1
        new_c["liquidation_incentives"] = [li]
        new_c["series_std_ratio"] = std_ratio
        new_c["json_time"] = now_time

        data[key] = new_c
    json.dump(data, fp)


print_time_series = True
fast_mode = False
ETH_PRICE = 1600
total_jobs = 6
assets_to_simulate = ["ETH"]
quote_to_simulate = "BTC"

l_factors = [0.25, 0.5, 1, 1.5, 2]

collateral = 50_000_000 / ETH_PRICE
collaterals = [collateral]
slippages = [collateral / 10]

c = {
    "series_std_ratio": 1,
    'volume_for_slippage_10_percentss': slippages,
    'trade_every': 1800,
    "collaterals": collaterals,
    'liquidation_incentives': [0.1],
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [0],
    "l_factors": [0.5],
    "collateral_factor": 0,
    "delays_in_minutes": [0, 5, 10, 20, 30, 40, 50, 60]
}

inv_names = {}
liquidation_incentive = {}
inv_underlying = {}
underlying = {}
decimals = {}
assets_aliases = {}
collateral_factors = {}

for a in assets_to_simulate:
    inv_names[a] = a
    liquidation_incentive[a] = 1
    inv_underlying[a] = a
    underlying[a] = a
    decimals[a] = 0
    assets_aliases[a] = a
    collateral_factors[a] = 1

SITE_ID = "badger"
SITE_ID = utils.get_site_id(SITE_ID)

base_runner.create_assets_std_ratio_information(SITE_ID, ["ETH", "BTC"],
                                                [("09", "2022"), ("10", "2022"), ("11", "2022")])

create_simulation_config(SITE_ID, c, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names)
base_runner.create_simulation_results(SITE_ID, ETH_PRICE, total_jobs, collateral_factors, inv_names, print_time_series, fast_mode)
base_runner.create_risk_params(SITE_ID, ETH_PRICE, total_jobs, l_factors, print_time_series)