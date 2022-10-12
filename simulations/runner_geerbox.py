import compound_parser
import base_runner
import json
import utils
import datetime
import time
import pandas as pd
import glob
import os
import copy
import shutil


def create_simulation_config():
    print("create_simulation_config")
    f1 = open(
        "webserver" + os.path.sep + SITE_ID + os.path.sep + "usd_volume_for_slippage.json")
    jj1 = json.load(f1)

    f2 = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json")
    jj2 = json.load(f2)

    data = {"json_time": time.time()}
    missed_assets = []
    for collateral_to_simulate in assets_to_simulate:

        if collateral_to_simulate not in jj1 or debt not in jj1[collateral_to_simulate]:
            missed_assets.append(collateral_to_simulate)
            print(collateral_to_simulate, debt, "Is Missing in usd_volume_for_slippage json")
            continue

        if collateral_to_simulate not in jj2 or debt not in jj2[collateral_to_simulate]:
            missed_assets.append(collateral_to_simulate)
            print(collateral_to_simulate, debt, "Is Missing in assets_std_ratio json")
            continue

        if collateral_to_simulate not in inv_names:
            missed_assets.append(collateral_to_simulate)
            print(collateral_to_simulate, "Is Missing in data json")
            continue

        key = collateral_to_simulate + "-" + debt
        new_c = copy.deepcopy(c)
        std_ratio = jj2[collateral_to_simulate][debt]
        slippage = jj1[collateral_to_simulate][debt]["volume"] / ETH_PRICE
        li = float(liquidation_incentive[inv_names[collateral_to_simulate]])
        li = li if li < 1 else li - 1
        new_c["liquidation_incentives"] = [li]
        new_c["series_std_ratio"] = std_ratio
        new_c["volume_for_slippage_10_percentss"] = [slippage]
        current_debt = users_data["DEBT_" + debt].sum()
        # max_debt = borrow_caps[inv_names[debt]] * 5
        # step_size = (max_debt - current_debt) / 30
        # new_c["collaterals"] = [int((current_debt + step_size * i) / ETH_PRICE) for i in range(30)]
        # new_c["collaterals"].append(borrow_caps[inv_names[debt_to_simulate]] / ETH_PRICE)
        new_c["current_debt"] = current_debt / ETH_PRICE
        data[key] = copy.deepcopy(new_c)
        print(key, "Added")
        print(key, "Added")

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "simulation_configs.json", "w")
    json.dump(data, fp)
    fp.close()
    return missed_assets


def create_usd_volumes_for_slippage():
    file = slippage_files_folder + os.path.sep + debt + "_pool_usd_volume_for_slippage.json"
    shutil.copyfile(file, 'webserver' + os.path.sep + SITE_ID + os.path.sep + 'usd_volume_for_slippage.json')


def create_csv_files():
    pd.options.mode.chained_assignment = None  # default='warn'
    total_days = 30
    csv_path = "C:\\dev\\monitor-backend\\gearbox\\"
    csv_tokens = {}
    market_tokens = []
    files = glob.glob(csv_path + "*.csv")
    for file in files:
        token = os.path.basename(file).replace("-USDC.csv", '')
        token = str(token)
        csv_tokens[token] = file

    file = open(lending_platform_json_file)
    data = json.load(file)
    for market in data["names"]:
        market = str(data["names"][market])
        market_tokens.append(market)
    valids = []
    for market_token in market_tokens:
        if market_token not in csv_tokens:
            print("Market Token", market_token, "is missing")
            continue
        valids.append(str(market_token))
        df = pd.read_csv(csv_tokens[market_token])
        rows_for_minute = len(df) / (total_days * 24 * 60)
        df = df.iloc[::int(rows_for_minute), :]
        df.reset_index(drop=True, inplace=True)
        df["timestamp_x"] = datetime.datetime.now()
        df["ask_price"] = df[" price"]
        df["bid_price"] = df[" price"]
        df = df[["timestamp_x", "bid_price", "ask_price"]]
        l = len(df)
        rows_for_month = int(l / total_days) * 30
        index = 0
        for i in download_dates:
            df1 = df.iloc[index * rows_for_month:(index + 1) * rows_for_month]
            df1.reset_index(drop=True, inplace=True)
            start_date = datetime.datetime(int(i[1]), int(i[0]), 1).timestamp()
            df1["timestamp_x"] = (start_date + df1.index * 60) * (1000 * 1000)
            df1 = df1.replace(to_replace=0, method='ffill')
            csv_file_name = "data_gearbox\\data_unified_" + i[1] + "_" + i[0] + "_" + market_token + "USDT" + ".csv"
            df1.to_csv(csv_file_name, index=False)
            print("Market Token", market_token, "Completed")
            index += 1

    print(valids)
    return valids


def create_assets_std_ratio_information():
    print("create_assets_std_ratio_information")
    data = {"json_time": time.time()}
    markets_data = {}
    for asset in assets_to_simulate:
        if asset != "USDC":
            df = pd.DataFrame()
            for date in download_dates:
                file_name = "data_gearbox" + os.path.sep + "data_unified_" + str(date[1]) + "_" + str(
                    date[0]) + "_" + asset + "USDT.csv"
                d = pd.read_csv(file_name)
                if len(df) == 0:
                    df = d
                else:
                    df = pd.concat([df, d], ignore_index=True, sort=False)
            markets_data[asset] = df.sort_values("timestamp_x")
            markets_data[asset] = markets_data[asset][["timestamp_x", "ask_price", "bid_price"]]

    for collateral in assets_to_simulate:
        if collateral != "USDC":
            data[collateral] = {}
            if collateral != debt:
                std = utils.calc_series_std_ratio("WETH", "USDC", collateral, debt, markets_data)
                data[collateral][debt] = std

    fp = open("webserver" + os.path.sep + SITE_ID + os.path.sep + "assets_std_ratio.json", "w")
    json.dump(data, fp)
    fp.close()


SITE_ID = "3"
ETH_PRICE = 1600
total_jobs = 5
lending_platform_json_file = "C:\dev\monitor-backend\gearbox\data_20221010.json"
slippage_files_folder = "C:\dev\monitor-backend\gearbox"
download_dates = [("09", "2022")]
# create_csv_files()
# exit()
# assets_to_simulate = [
#      'DAI', 'WETH', 'stETH', 'WBTC', 'USDT', 'sUSD', 'FRAX', 'GUSD', 'LUSD', 'steCRV', 'cvxsteCRV', '3Crv', 'cvx3Crv',
#      'FRAX3CRV-f', 'LUSD3CRV-f', 'cvxLUSD3CRV-f', 'crvPlain3andSUSD', 'cvxcrvPlain3andSUSD', 'gusd3CRV', 'cvxgusd3CRV',
#      'yvDAI', 'yvUSDC', 'yvWETH', 'yvWBTC', 'yvCurve-stETH', 'yvCurve-FRAX', 'stkcvxLUSD3CRV-f', 'stkcvxgusd3CRV',
#      'stkcvxcrvPlain3andSUSD', 'stkcvx3Crv', 'stkcvxsteCRV']

#assets_to_simulate = ['DAI', 'FRAX', 'WETH']

assets_to_simulate = create_csv_files()

debt = "DAI"  # ['WETH', 'WBTC', 'DAI', 'USDC', 'stETH']

c = {
    "series_std_ratio": 0,
    'volume_for_slippage_10_percentss': [],
    'trade_every': 1800,
    "collaterals": [1_000_000 / ETH_PRICE, 5_000_000 / ETH_PRICE, 10_000_000 / ETH_PRICE,
                    25_000_000 / ETH_PRICE, 50_000_000 / ETH_PRICE,
                    100_000_000 / ETH_PRICE, 250_000_000 / ETH_PRICE, 500 / ETH_PRICE],
    'liquidation_incentives': [],
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [0],
    "l_factors": [0.25, 0.5, 1, 1.5, 2]
}
l_factors = [0.25, 0.5, 1, 1.5, 2]

if __name__ == '__main__':
    SITE_ID = utils.get_site_id(SITE_ID)
    file = open(lending_platform_json_file)
    data = json.load(file)
    fast_mode = False
    cp_parser = compound_parser.CompoundParser()
    users_data, assets_liquidation_data, \
    last_update_time, names, inv_names, decimals, collateral_factors, borrow_caps, collateral_caps, prices, \
    underlying, inv_underlying, liquidation_incentive, orig_user_data, totalAssetCollateral, totalAssetBorrow = cp_parser.parse(
        data, False)

    create_usd_volumes_for_slippage()
    create_assets_std_ratio_information()
    missed_assets = create_simulation_config()
    base_runner.create_simulation_results(SITE_ID, ETH_PRICE, total_jobs, collateral_factors, inv_names, False,
                                          fast_mode)
    base_runner.create_risk_params(SITE_ID, ETH_PRICE, total_jobs, l_factors, False)

    valid_assets_to_simulation = copy.deepcopy(assets_to_simulate)
    print("Missed Simulations", missed_assets)
    for ma in missed_assets:
        if ma in valid_assets_to_simulation:
            valid_assets_to_simulation.remove(ma)

    base_runner.create_current_simulation_risk(SITE_ID, ETH_PRICE, users_data, valid_assets_to_simulation,
                                               {a:a for a in assets_to_simulate},
                                               collateral_factors, inv_names, liquidation_incentive, total_jobs, False)

    print("Simulation Ended")
