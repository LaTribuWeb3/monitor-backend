import json
import time
import os
import glob
import numpy as np
import pandas as pd
import compound_parser
import base_runner
import copy
import kyber_prices
import utils
import sys
import shutil


def create_dex_information():
    print("create_dex_information")
    data = {"json_time": time.time()}
    for market in assets_to_simulate:
        data[market] = {"count": 0, "total": 0, "avg": 0, "med": 0,
                        "top_10": 0,
                        "top_5": 0, "top_1": 0, "users": []}

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "dex_liquidity.json", "w")
    json.dump(data, fp)

def create_simulation_config(SITE_ID, c, ETH_PRICE, assets_to_simulate, assets_aliases, liquidation_incentive,
                             inv_names):
    def roundUp(x):
        x = max(x, 1_000_000)
        x = int((x + 1e6 - 1) / 1e6) * 1e6
        if x == 0:
            print(x)
            exit()
        return x

    print("create_simulation_config")
    f1 = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "usd_volume_for_slippage.json")
    jj1 = json.load(f1)

    f2 = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json")
    jj2 = json.load(f2)
    data = {"json_time": time.time()}
    now_time = time.time()
    for base_to_simulation in assets_to_simulate:
        for quote_to_simulation in jj1[base_to_simulation]:
            if assets_aliases[base_to_simulation] != assets_aliases[quote_to_simulation]:
                key = base_to_simulation + "-" + quote_to_simulation
                new_c = copy.deepcopy(c)
                if assets_aliases[base_to_simulation] in jj2 and \
                        assets_aliases[quote_to_simulation] in jj2[assets_aliases[base_to_simulation]]:
                    std_ratio = jj2[assets_aliases[base_to_simulation]][assets_aliases[quote_to_simulation]]
                else:
                    std_ratio = jj2[assets_aliases[quote_to_simulation]][assets_aliases[base_to_simulation]]

                slippage = jj1[base_to_simulation][quote_to_simulation]["volume"] / ETH_PRICE
                li = float(liquidation_incentive[inv_names[base_to_simulation]])
                li = li if li < 1 else li - 1
                new_c["liquidation_incentives"] = [li]
                new_c["series_std_ratio"] = std_ratio
                new_c["volume_for_slippage_10_percentss"] = [slippage]
                new_c["json_time"] = now_time

                max_collateral = collateral_caps[inv_names[base_to_simulation]]
                max_debt = borrow_caps[inv_names[quote_to_simulation]]

                cc = [0.25 * max_collateral, 0.5 * max_collateral, 0.75 * max_collateral, 1 * max_collateral,
                      1.25 * max_collateral, 1.5 * max_collateral, 1.75 * max_collateral, 2 * max_collateral]

                dd = [0.25 * max_debt, 0.5 * max_debt, 0.75 * max_debt, 1 * max_debt, 1.25 * max_debt,
                      1.5 * max_debt, 1.75 * max_debt, 2 * max_debt]

                for c1 in cc:
                    c1 = roundUp(c1)
                    c1 = c1 / ETH_PRICE
                    c1 = int(c1)
                    if c1 not in new_c["collaterals"]:
                        new_c["collaterals"].append(c1)
                    for d1 in dd:
                        d1 = roundUp(d1)
                        d1 = d1 / ETH_PRICE
                        d1 = int(d1)
                        if d1 < c1 and d1 not in new_c["collaterals"]:
                            new_c["collaterals"].append(d1)

                current_collateral = 0
                current_debt = 0

                for index, row in users_data.iterrows():
                    current_debt += float(row["DEBT_" + base_to_simulation])
                    current_collateral += float(row["COLLATERAL_" + base_to_simulation])

                new_c["collaterals"].append(roundUp(current_debt) / ETH_PRICE)
                new_c["collaterals"].append(roundUp(current_collateral) / ETH_PRICE)

                if 0 in new_c["collaterals"]:
                    print(new_c)
                new_c["current_debt"] = current_debt / ETH_PRICE
                data[key] = new_c

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "simulation_configs.json", "w")
    json.dump(data, fp)


ETH_PRICE = 1600

lending_platform_json_file = ".." + os.path.sep + "agave" + os.path.sep + "0x5E15d5E33d318dCEd84Bfe3F4EACe07909bE6d9c_data.json"
oracle_json_file = ""
assets_to_simulate = ['USDC', 'WXDAI', 'LINK', 'GNO', 'WBTC', 'WETH', 'FOX']
assets_aliases = {'USDC': 'USDC', 'WXDAI': 'DAI', 'LINK': 'LINK', 'GNO': 'GNO', 'WBTC': 'BTC', 'WETH': 'ETH',
                  'FOX': 'FOX'}

c = {
    "series_std_ratio": 0,
    'volume_for_slippage_10_percentss': [],
    'trade_every': 1800,
    "collaterals": [],
    'liquidation_incentives': [],
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [0],
    "l_factors": [0.25, 0.5, 1, 1.5, 2]
}

print_time_series = False
total_jobs = 5
platform_prefix = ""
SITE_ID = "4"
chain_id = "og"
l_factors = [0.25, 0.5, 1, 1.5, 2]

if __name__ == '__main__':
    fast_mode = len(sys.argv) > 1
    print("FAST MODE", fast_mode)

    SITE_ID = utils.get_site_id(SITE_ID)
    file = open(lending_platform_json_file)
    data = json.load(file)

    if os.path.exists(oracle_json_file):
        file = open(oracle_json_file)
        oracle = json.load(file)
        data["prices"] = copy.deepcopy(oracle["prices"])

    cp_parser = compound_parser.CompoundParser()
    users_data, assets_liquidation_data, \
    last_update_time, names, inv_names, decimals, collateral_factors, borrow_caps, collateral_caps, prices, \
    underlying, inv_underlying, liquidation_incentive, orig_user_data, totalAssetCollateral, totalAssetBorrow = cp_parser.parse(
        data)

    users_data["nl_user_collateral"] = 0
    users_data["nl_user_debt"] = 0

    for base_to_simulation in assets_to_simulate:
        users_data["NL_COLLATERAL_" + base_to_simulation] = users_data["NO_CF_COLLATERAL_" + base_to_simulation]
        users_data["NL_DEBT_" + base_to_simulation] = users_data["DEBT_" + base_to_simulation]
        users_data["MIN_" + base_to_simulation] = users_data[
            ["NO_CF_COLLATERAL_" + base_to_simulation, "DEBT_" + base_to_simulation]].min(axis=1)

        users_data["NL_COLLATERAL_" + base_to_simulation] -= users_data["MIN_" + base_to_simulation]
        users_data["NL_DEBT_" + base_to_simulation] -= users_data["MIN_" + base_to_simulation]
        users_data["nl_user_collateral"] += users_data["NL_COLLATERAL_" + base_to_simulation]
        users_data["nl_user_debt"] += users_data["NL_DEBT_" + base_to_simulation]

    kp = kyber_prices.KyberPrices("100", inv_names, underlying, decimals)

    base_runner.create_overview(SITE_ID, users_data, totalAssetCollateral, totalAssetBorrow)
    base_runner.create_lending_platform_current_information(SITE_ID, last_update_time, names, inv_names, decimals,
                                                            prices, collateral_factors, collateral_caps, borrow_caps,
                                                            underlying)
    base_runner.create_account_information(SITE_ID, users_data, totalAssetCollateral, totalAssetBorrow, inv_names,
                                           assets_liquidation_data)
    base_runner.create_oracle_information(SITE_ID, prices, chain_id, names, assets_aliases, kp.get_price)
    create_dex_information()
    base_runner.create_whale_accounts_information(SITE_ID, users_data, assets_to_simulate)
    base_runner.create_open_liquidations_information(SITE_ID, users_data, assets_to_simulate)

    base_runner.create_usd_volumes_for_slippage(SITE_ID, chain_id, inv_names, liquidation_incentive, kp.get_price,
                                                False)

    # src = "webserver" + os.path.sep + "4\\2022-11-13-1-48" + os.path.sep + "usd_volume_for_slippage.json"
    # dst = "webserver" + os.path.sep + SITE_ID + os.path.sep + "usd_volume_for_slippage.json"
    # shutil.copyfile(src, dst)

    base_runner.create_assets_std_ratio_information(SITE_ID, ['DAI', 'USDC', 'LINK', 'GNO', 'BTC', 'ETH', 'FOX'],
                                                    [("04", "2022"), ("05", "2022"), ("06", "2022")])


    create_simulation_config(SITE_ID, c, ETH_PRICE, assets_to_simulate, assets_aliases, liquidation_incentive,
                              inv_names)
    base_runner.create_simulation_results(SITE_ID, ETH_PRICE, total_jobs, collateral_factors, inv_names,
                                          print_time_series, fast_mode)
    base_runner.create_risk_params(SITE_ID, ETH_PRICE, total_jobs, l_factors, print_time_series)
    base_runner.create_current_simulation_risk(SITE_ID, ETH_PRICE, users_data, assets_to_simulate, assets_aliases,
                                               collateral_factors, inv_names, liquidation_incentive, total_jobs, False)
    d1 = utils.get_file_time(oracle_json_file)
    utils.update_time_stamps(SITE_ID, min(last_update_time, d1))
    utils.publish_results(SITE_ID)
