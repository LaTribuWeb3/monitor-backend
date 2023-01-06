import datetime
import shutil
import glob
import compound_parser
import stability_report
import numpy as np
import utils
import time
import pandas as pd
import os
import json
import aggregator
import sliipage_utils
import traceback
import copy
import base_runner
import sys

def prepare_date_file():
    files = glob.glob("..\\meld\\history-src\\*.*")
    for file in files:
        df = pd.read_csv(file)
        price_field_name = [x for x in df.columns if "price" in x][0]
        new_df = []
        last_block_number = df["Block number"].min()
        last_timestamp_x = 0
        last_bid_price = 0
        last_ask_price = 0

        for index, row in df.iterrows():
            while row["Block number"] > last_block_number:
                new_row = {}
                new_row["timestamp_x"] = last_timestamp_x
                new_row["Block number"] = last_block_number
                new_row["bid_price"] = last_bid_price
                new_row["ask_price"] = last_ask_price
                new_df.append(new_row)
                last_block_number += 1

            last_timestamp_x = row["timestamp"]
            last_bid_price = row[price_field_name]
            last_ask_price = row[price_field_name]

        df = pd.DataFrame(new_df)
        print(os.path.basename(file), datetime.date.fromtimestamp(df["timestamp_x"].min()),
              datetime.date.fromtimestamp(df["timestamp_x"].max()))
        df.to_csv("data" + os.path.sep + "data_unified_" + os.path.basename(file).split("-")[0] + "ADA.csv")


def calc_series_std_ratio(base, quote, source):
    print(base, quote)
    if base == "ADA":
        test = pd.read_csv("data" + os.path.sep + "data_unified_" + quote + "ADA.csv")
        test["price"] = 1 / ((test["bid_price"] + test["ask_price"]) * 0.5)
    elif quote == "ADA":
        test = pd.read_csv("data" + os.path.sep + "data_unified_" + base + "ADA.csv")
        test["price"] = (test["bid_price"] + test["ask_price"]) * 0.5
    else:
        test1 = pd.read_csv("data" + os.path.sep + "data_unified_" + base + "ADA.csv")
        test1["price"] = (test1["bid_price"] + test1["ask_price"]) * 0.5

        test2 = pd.read_csv("data" + os.path.sep + "data_unified_" + quote + "ADA.csv")
        test2["price"] = (test2["bid_price"] + test2["ask_price"]) * 0.5
        test = test1.merge(test2, how='inner', left_on=['Block number'], right_on=['Block number'])
        print(len(test1), len(test2), len(test))
        test["price"] = test["price_x"] / test["price_y"]

    source_rolling_std = np.average(
        source["price"].rolling(5 * 30).std().dropna() / source["price"].rolling(5 * 30).mean().dropna())

    test_rolling_std = np.average(
        test["price"].rolling(5 * 30).std().dropna() / test["price"].rolling(5 * 30).mean().dropna())

    source_std = np.std(source["price"]) / np.average(source["price"])
    test_std = np.std(test["price"]) / np.average(test["price"])

    print("source_avg", np.average(source["price"]))
    print("source_min", np.min(source["price"]))
    print("source_std", source_std)
    print("source_rolling_std", source_rolling_std)

    print("test_avg", np.average(test["price"]))
    print("test_min", np.min(test["price"]))
    print("test_std", test_std)
    print("test_rolling_std", test_rolling_std)

    print("30M Rolling STD Ratio", round(test_rolling_std / source_rolling_std, 2))
    print("STD Ratio", round(test_std / source_std, 2))
    print()
    return test_rolling_std / source_rolling_std


def create_assets_std_ratio_information(SITE_ID, assets):
    print("create_assets_std_ratio_information")
    data = {"json_time": time.time()}
    dates = ["2022_09", "2022_10", "2022_11"]
    df1 = pd.concat((pd.read_csv("data\\data_unified_" + f + "_ETHUSDT.csv") for f in dates), ignore_index=True)
    df1 = df1.sort_values("timestamp_x")
    df1["price"] = (df1["bid_price"] + df1["ask_price"]) * 0.5
    for base in assets:
        for quote in assets:
            if base != quote:
                if base not in data:
                    data[base] = {}
                std = calc_series_std_ratio(base, quote, df1)
                data[base][quote] = std

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json", "w")
    json.dump(data, fp)
    fp.close()

def create_aggregator_file(SITE_ID, assets):
    data = {"json_time": time.time()}
    for asset in assets:
        if asset != "ADA":
            file = pd.read_csv("..\\meld\\" + asset + "-ADA.csv")
            last_row = file.iloc[-1]
            data[asset + "_ADA"] = {}
            data[asset + "_ADA"]["token0"] = last_row["reserve " + asset]
            data[asset + "_ADA"]["token1"] = last_row["reserve ADA"]
            data[asset + "_ADA"]["reserve"] = ""

            data["ADA_" + asset] = {}
            data["ADA_" + asset]["token0"] = last_row["reserve ADA"]
            data["ADA_" + asset]["token1"] = last_row["reserve " + asset]
            data["ADA_" + asset]["reserve"] = ""

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "aggregator.json", "w")
    json.dump(data, fp)
    fp.close()


def get_usd_volumes_for_slippage(inv_names, liquidation_incentive, get_price_function):
    base = "ADA"
    asset_usdc_price = {}
    for quote in inv_names:
        print(base, quote)
        price_in_base = get_price_function(base, quote, 1000)
        print(price_in_base)
        asset_usdc_price[quote] = price_in_base

    print(asset_usdc_price)
    all_prices = {}
    for base in inv_names:
        for quote in inv_names:
            if base == quote:
                continue
            if base not in all_prices:
                all_prices[base] = {}
            lic = float(liquidation_incentive[inv_names[quote]])
            print(base, quote)
            llc = lic if lic >= 1 else 1 + lic
            volume = sliipage_utils.get_usd_volume_for_slippage(base, quote, llc, asset_usdc_price, get_price_function)
            all_prices[base][quote] = {"volume": volume / ADA_TO_USD, "llc": llc}

    return all_prices


def create_usd_volumes_for_slippage(SITE_ID, inv_names, liquidation_incentive, get_price_function):

    try:
        print("create_usd_volumes_for_slippage")
        data = get_usd_volumes_for_slippage(inv_names, liquidation_incentive, get_price_function)
        data["json_time"] = time.time()
        fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "usd_volume_for_slippage.json", "w")
        json.dump(data, fp)
        fp.close()
    except Exception as e:
        traceback.print_exc()
        print(e)


def create_simulation_config(SITE_ID, c, ETH_PRICE, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names):
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
                new_c["collaterals"] = [5_0000 / ETH_PRICE, 10_000 / ETH_PRICE, 20_000 / ETH_PRICE,
                                        30_000 / ETH_PRICE, 40_000 / ETH_PRICE,
                                        50_000 / ETH_PRICE, 60_000 / ETH_PRICE, 70_000 / ETH_PRICE,
                                        80_000 / ETH_PRICE, 90_000 / ETH_PRICE,
                                        100_000 / ETH_PRICE, 250_000 / ETH_PRICE, 500_000 / ETH_PRICE,
                                        750_000 / ETH_PRICE, 1_000_000 / ETH_PRICE, 5_000_000 / ETH_PRICE,
                                        10_000_000 / ETH_PRICE, 15_000_000 / ETH_PRICE, 20_000_000 / ETH_PRICE]

                data[key] = new_c

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "simulation_configs.json", "w")
    json.dump(data, fp)


ETH_PRICE = 1600
ADA_TO_USD = 3
c = {
    "series_std_ratio": 1,
    'volume_for_slippage_10_percentss': [],
    'trade_every': 1800,
    "collaterals": [],
    'liquidation_incentives': [0.1],
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [2],
    "l_factors": [0.25, 0.5, 1, 1.5, 2],
    "collateral_factor": 0
}
l_factors = [0.25, 0.5, 1, 1.5, 2]
if __name__ == '__main__':
    fast_mode = len(sys.argv) > 1
    print("FAST MODE", fast_mode)
    alert_mode = len(sys.argv) > 2
    print("ALERT MODE", alert_mode)
    send_alerts = len(sys.argv) > 3
    print("SEND ALERTS", send_alerts)

    print_time_series = False
    skip = False
    calc_pnl = False
    SITE_ID = "5"
    SITE_ID = utils.get_site_id(SITE_ID)

    assets_to_simulate = ["ADA", "WRT", "MIN", "MELD", "iUSD", "INDY", "HOSKY", "COPI", "C3", "WMT"]
    ETH_PRICE = 1600
    total_jobs = 5
    # inv_names = {}
    # liquidation_incentive = {}
    # inv_underlying = {}
    # underlying = {}
    # decimals = {}
    assets_aliases = {}
    # collateral_factors = {}

    for a in assets_to_simulate:
    #     inv_names[a] = a
    #     liquidation_incentive[a] = 1.1
    #     inv_underlying[a] = a
    #     underlying[a] = a
    #     decimals[a] = 0
        assets_aliases[a] = a
    #     collateral_factors[a] = 1

    # get slippage data from meld directory
    shutil.copyfile("..\\meld\\liquidity\\usd_volume_for_slippage.json",
                     "webserver" + os.path.sep + SITE_ID + os.path.sep + 'usd_volume_for_slippage.json')

    lending_platform_json_file = "..\\meld\\user-data\\data.json"
    file = open(lending_platform_json_file)
    data = json.load(file)
    cp_parser = compound_parser.CompoundParser()
    users_data, assets_liquidation_data, \
    last_update_time, names, inv_names, decimals, collateral_factors, borrow_caps, collateral_caps, prices, \
    underlying, inv_underlying, liquidation_incentive, orig_user_data, totalAssetCollateral, totalAssetBorrow = cp_parser.parse(
        data)

    prepare_date_file()
    create_assets_std_ratio_information(SITE_ID, assets_to_simulate)

    create_simulation_config(SITE_ID, c, ETH_PRICE, assets_to_simulate, assets_aliases, liquidation_incentive, inv_names)
    
    base_runner.create_simulation_results(SITE_ID, ETH_PRICE, total_jobs, collateral_factors, inv_names, print_time_series, fast_mode)
    base_runner.create_risk_params(SITE_ID, ETH_PRICE, total_jobs, l_factors, print_time_series)
    # base_runner.create_current_simulation_risk(SITE_ID, ETH_PRICE, users_data, assets_to_simulate, assets_aliases, collateral_factors, inv_names, liquidation_incentive, total_jobs, False)
    
    base_runner.create_overview(SITE_ID, users_data, totalAssetCollateral, totalAssetBorrow)
    base_runner.create_lending_platform_current_information(SITE_ID, last_update_time, names, inv_names, decimals,
                                                                prices, collateral_factors, collateral_caps, borrow_caps,
                                                                underlying)
    base_runner.create_account_information(SITE_ID, users_data, totalAssetCollateral, totalAssetBorrow, inv_names, assets_liquidation_data, False)
    base_runner.create_whale_accounts_information(SITE_ID, users_data, assets_to_simulate)
    base_runner.create_open_liquidations_information(SITE_ID, users_data, assets_to_simulate)
    #copy riskparams to output
    # files = glob.glob("webserver" + os.path.sep + SITE_ID + os.path.sep + "*.json")
    # print(files)
    # for f in files:
    #     shutil.copyfile(f, ".." + os.path.sep + "meld" + os.path.sep + "simulation-output" + os.path.sep + os.path.basename(f))

    utils.publish_results(SITE_ID, '5/testlt')

