import glob
import numpy as np
import copy
import pandas as pd
import requests

import compound_parser
import datetime
import json
import matplotlib.pyplot as plt
from matplotlib import animation
from pathlib import Path
import os
from github import Github
import private_config
import matplotlib.dates as mdates


def get_gmx_price():
    file = open("data\\gmx_price.json")
    gmx_price = json.load(file)
    plt.plot([float(x["aumInUsdg"]) / float(x["glpSupply"]) for x in gmx_price["data"]["glpStats"]])
    plt.show()
    # ts = gmx_price.keys()
    # print(ts)


def calc_series_std_ratio(source_base, source_quote, test_base, test_quote, market_data1):
    print("calc_series_std_ratio", source_base, source_quote, " To", test_base, test_quote)
    market_data = copy.deepcopy(market_data1)
    source = market_data[source_base]
    source["price"] = (source["bid_price"] + source["ask_price"]) * 0.5
    test = None
    if source_quote == test_quote or (source_quote == "USDT" and test_quote == "USDC"):
        test = market_data[test_base]
        test["price"] = (test["bid_price"] + test["ask_price"]) * 0.5
    else:
        test1 = market_data[test_base]
        test1["price"] = (test1["bid_price"] + test1["ask_price"]) * 0.5
        test1["timestamp_x"] /= 1000 * 1000 * 60
        test1["timestamp_x"] = test1["timestamp_x"].astype(int)

        test2 = market_data[test_quote]
        test2["price"] = (test2["bid_price"] + test2["ask_price"]) * 0.5
        test2["timestamp_x"] /= 1000 * 1000 * 60
        test2["timestamp_x"] = test2["timestamp_x"].astype(int)
        test = test1.merge(test2, how='inner', left_on=['timestamp_x'], right_on=['timestamp_x'])
        print(len(test1), len(test2), len(test))
        test["price"] = test["price_x"] / test["price_y"]

    source_rolling_std = np.average(
        source["price"].rolling(5 * 30).std().dropna() / source["price"].rolling(5 * 30).mean().dropna())

    test_rolling_std = np.average(
        test["price"].rolling(5 * 30).std().dropna() / test["price"].rolling(5 * 30).mean().dropna())

    print("source_avg", np.average(source["price"]))
    print("source_min", np.min(source["price"]))
    print("source_std", np.std(source["price"]) / np.average(source["price"]))

    print("test_avg", np.average(test["price"]))
    print("test_min", np.min(test["price"]))
    print("test_std", np.std(test["price"]) / np.average(test["price"]))

    print("30M Rolling STD Ratio", test_rolling_std / source_rolling_std)
    print()
    return test_rolling_std / source_rolling_std


def find_worth_month(name):
    files = glob.glob("simulation_results\\" + name + "\\*.csv")
    xx = ["series_std_ratio", "liquidation_incentive", "price_recovery_time", "volume_for_slippage_10_percents",
          "cycle_trade_volume", "collateral", "recovery_halflife_retail", "share_institutional",
          "stability_pool_initial_balance_ratio", "stability_pool_initial_balance", "collateral_liquidation_factor"]

    results = {}
    for f in files:
        name = f.split(".")[1].split("_")[1]
        df = pd.read_csv(f)
        uniques = df.groupby(xx).size().reset_index().rename(columns={0: 'count'})
        date = f.split("_")[4] + "-" + f.split("_")[5]
        if len(uniques) == 180:
            print(f, len(uniques))
            for index, row in uniques.iterrows():
                batch_df = copy.deepcopy(df)
                name_1 = name
                for x in xx:
                    name_1 += "_" + str(row[x])
                    batch_df = batch_df.loc[batch_df[x] == row[x]]
                max_drop = np.max(batch_df["max_drop"])
                if name_1 not in results or results[name_1]["max_drop"] < max_drop:
                    results[name_1] = {"date": date, "max_drop": max_drop}
    dates = {}
    for r in results:
        d = results[r]["date"]
        if d not in dates:
            dates[d] = 0
        dates[d] += 1
    print(dates)


def find_total_liquidations_for_price_drop(lending_platform_json_file, drop):
    file = open(lending_platform_json_file)
    data = json.load(file)
    cp_parser = compound_parser.CompoundParser()
    users_data, assets_liquidation_data, \
    last_update_time, names, inv_names, decimals, collateral_factors, borrow_caps, collateral_caps, prices, \
    underlying, inv_underlying, liquidation_incentive, orig_user_data, totalAssetCollateral, totalAssetBorrow = cp_parser.parse(
        data)

    report = {}
    for a in assets_liquidation_data:
        price = float(prices[a])
        if "USDT" not in names[a] and "USDC" not in names[a]:
            report[names[a]] = 0
            for asset in assets_liquidation_data[a]:
                for x in assets_liquidation_data[a][asset]:
                    if float(x) < price * (1 - drop):
                        print(names[a], asset, price * (1 - drop), assets_liquidation_data[a][asset][x])
                        report[names[a]] += round(float(assets_liquidation_data[a][asset][x]), 0)
                        break
    print(drop, report)


def find_worst_day():
    files = glob.glob("data\\data_unified_*_ETHUSDT.csv")
    all_df = None
    for file in files:
        df = pd.read_csv(file)
        df["index"] = pd.to_datetime(df["timestamp_x"] / 1_000_000, unit='s')
        all_df = pd.concat(
            [all_df, df.groupby(pd.Grouper(key="index", freq='24h'))["ask_price"].agg(["first", "last"])])
    all_df["drop"] = all_df["last"] / all_df["first"]
    print(all_df.sort_values("drop"))


def copy_day_to_worst_day(date1, date2):
    date1 = datetime.datetime.strptime(date1, '%Y-%m-%d')
    date2 = datetime.datetime.strptime(date2, '%Y-%m-%d')

    file_name = "data\\data_unified_" + str(date1.year) + "_" + str(date1.month).rjust(2, '0') + "_ETHUSDT.csv"
    df = pd.read_csv(file_name)
    df["index"] = pd.to_datetime(df["timestamp_x"] / 1_000_000, unit='s')
    df = df.loc[(df["index"].dt.day == date1.day) | (df["index"].dt.day == date2.day)]
    df.to_csv(file_name.replace("data\\", "data_worst_day\\"))

def get_file_time(file_name):
    print(file_name)
    if not os.path.exists(file_name):
        return float('inf')
    file = open(file_name)
    liquidityJson = json.load(file)
    if not "lastUpdateTime" in liquidityJson:
        return float('inf')
    return liquidityJson["lastUpdateTime"]


def update_time_stamps(SITE_ID, last_update_time):
    print('update_time_stamps')
    path = "webserver" + os.path.sep + SITE_ID + os.path.sep
    files = glob.glob(path + "*.*")
    print(files)
    for file_name in files:
        try:
            file = open(file_name)
            data = json.load(file)
            file.close()
            old_json_time = data["json_time"]
            data["json_time"] = last_update_time
            print(file_name, "old time", int(old_json_time), "new time", int(last_update_time), "diff",
                  int((old_json_time - last_update_time) / 60), "Minutes")
            fp = open(file_name, "w")
            json.dump(data, fp)
            fp.close()
        except Exception as e:
            print(e)


def print_account_information_graph(json_file):
    file = open(json_file)
    data = json.load(file)
    for asset in [x for x in data if x != "json_time"]:
        plt.cla()
        plt.suptitle(asset)
        for quote in data[asset]["graph_data"]:
            xy = data[asset]["graph_data"][quote]
            new_xy = {}
            for x in xy:
                new_xy[float(x)] = float(xy[x])
            new_xy = sorted(new_xy.items())
            plt.plot([x[0] for x in new_xy], [x[1] for x in new_xy], label=asset + "/" + quote)
        plt.show()

def get_site_id(SITE_ID):
    if str(os.path.sep) in SITE_ID:
        SITE_ID = SITE_ID.split(str(os.path.sep))[0]
    n = datetime.datetime.now()
    d = str(n.year) + "-" + str(n.month) + "-" + str(n.day) + "-" + str(n.hour) + "-" + str(n.minute)
    SITE_ID = SITE_ID + os.path.sep + d
    os.makedirs("webserver" + os.path.sep + SITE_ID, exist_ok=True)
    return SITE_ID


def get_latest_folder_name(SITE_ID):
    # print(private_config.git_version_token)
    gh = Github(login_or_token=private_config.git_version_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/simulation-results"
    repo = gh.get_repo(repo_name)
    folders = repo.get_contents("./" + SITE_ID)
    max_folder_date = datetime.datetime(2000, 1, 1, 1, 1)
    max_folder_name = ""

    for folder in folders:
        fields = folder.name.split("-")
        folder_date = datetime.datetime(int(fields[0]), int(fields[1]), int(fields[2]), int(fields[3]), int(fields[4]))
        if max_folder_date < folder_date:
            max_folder_date = folder_date
            max_folder_name = folder.name
    return max_folder_name, max_folder_date


def get_all_sub_folders(path, json_name):
    print(private_config.git_version_token)
    gh = Github(login_or_token=private_config.git_version_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/simulation-results"
    repo = gh.get_repo(repo_name)
    folders = repo.get_contents("./" + path)
    results = {}
    for folder in folders:
        print(folder)
        try:
            contents = repo.get_contents("/" + path + "/" + str(folder.name) + "/" + json_name)
            j = json.loads(contents.decoded_content)
            results[j["json_time"]] = j
        except Exception as e:
            print("Exception in folder", folder.name)

    return results


def compare_to_prod_and_send_alerts(name, base_SITE_ID, current_SITE_ID, bot_id, chat_id, slippage_threshold=5,
                                    send_alerts=False):
    print("comparing to prod", name)
    prod_version = get_prod_version(name)
    print(prod_version)
    prod_file = json.loads(get_git_json_file(base_SITE_ID, prod_version, "usd_volume_for_slippage.json"))
    file = open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "usd_volume_for_slippage.json")
    last_file = json.load(file)
    time_from_prod = last_file["json_time"] - prod_file["json_time"]
    time_from_prod /= (60 * 60)
    time_from_prod = str(round(time_from_prod, 2)) + " Hours (from publication)"

    alert_sent = False
    if send_alerts:
        send_telegram_alert(bot_id, chat_id, "-------------------------------------------------")
    for key1 in prod_file:
        if key1 == "json_time": continue
        for key2 in prod_file[key1]:
            print(key1, key2)
            last_volume = last_file[key1][key2]["volume"]
            prod_volume = prod_file[key1][key2]["volume"]
            change = 100 * (round((last_volume /prod_volume ) - 1, 2))
            if abs(change) > slippage_threshold:
                last_volume = '{:,}'.format(round(last_volume,0))
                prod_volume = '{:,}'.format(round(prod_volume,0))
                message = f"{time_from_prod} {name}.{key1}.{key2}  " \
                          f"\nLiquidity Change by {round(change, 2)}% " \
                          f"\nCurrent Volume: {last_volume}" \
                          f"\nPaper Volume: {prod_volume}"
                print(message)
                alert_sent = True
                if send_alerts:
                    print("Sending To TG")
                    send_telegram_alert(bot_id, chat_id, message)

    if not alert_sent:
        message = f'{time_from_prod} {name} Slippage is fine.'
        print(message)
        if send_alerts:
            print("Sending To TG")
            send_telegram_alert(bot_id, chat_id, message)

    alert_sent = False
    oracle_file = open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "oracles.json")
    oracle_file = json.load(oracle_file)
    for market in oracle_file:
        if market == "json_time": continue
        cex = float(oracle_file[market]["cex_price"])
        oracle = float(oracle_file[market]["oracle"])
        dex = float(oracle_file[market]["dex_price"])
        diff = (100 * ((oracle / dex) - 1))
        if abs(diff) > 3:
            message = f'{time_from_prod} {name}.{market} ' \
                      f'\nOracle<>Dex Price is off by: {round(diff, 2)}' \
                      f'\nOracle Price: {oracle} Dex Price: {dex}'
            print(message)
            alert_sent = True
            if send_alerts:
                print("Sending To TG")
                send_telegram_alert(bot_id, chat_id, message)

        if cex:
            diff = (100 * ((oracle / cex) - 1))
            if abs(diff) > 3:
                message = f'{time_from_prod} {name}.{market} ' \
                          f'\nOracle<>Cex Price is off by: {round(diff, 2)} ' \
                          f'\nOracle Price: {oracle} ' \
                          f'\nCex Price: {cex}'
                print(message)
                alert_sent = True
                if send_alerts:
                    print("Sending To TG")
                    send_telegram_alert(bot_id, chat_id, message)

    if not alert_sent:
        message = f'{time_from_prod} {name} Oracle is fine.'
        print(message)
        if send_alerts:
            print("Sending To TG")
            send_telegram_alert(bot_id, chat_id, message)


def get_prod_version(name):
    gh = Github(login_or_token=private_config.git_version_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/version-control"
    repo = gh.get_repo(repo_name)
    contents = repo.get_contents("/" + name)
    return str(contents.decoded_content).replace('b', '').replace("'", '')


def get_git_json_file(name, key, json_name):
    gh = Github(login_or_token=private_config.git_version_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/simulation-results"
    repo = gh.get_repo(repo_name)
    file_path = name + "/" + key + "/" + json_name
    contents = repo.get_contents(file_path)
    return contents.decoded_content


def move_to_prod(name, key):
    print(private_config.git_version_token)
    gh = Github(login_or_token=private_config.git_version_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/version-control"
    repo = gh.get_repo(repo_name)
    contents = repo.get_contents("/" + name)
    repo.update_file(contents.path, "more tests", key, contents.sha)


def publish_results(SITE_ID):
    print("publish_results")
    if private_config.git_token == "":
        print("Git Upload Failed. no Token")
        exit()

    SITE_ID = SITE_ID.replace('\\', '/')
    gh = Github(login_or_token=private_config.git_token, base_url='https://api.github.com')
    repo_name = "Risk-DAO/simulation-results"
    repo = gh.get_repo(repo_name)
    files = glob.glob("webserver" + os.path.sep + SITE_ID + os.path.sep + "*.json")
    print(files)
    for f in files:
        file = open(f)
        git_file = SITE_ID + "/" + os.path.basename(f)
        print(git_file)
        repo.create_file(git_file, "Commit Comments", file.read())


def send_telegram_alert(bot_id, chat_id, message):
    url = f'https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={chat_id}&text={message}'
    requests.get(url)


def copy_site():
    assets_to_replace = {"auETH": "vETH", "auWBTC": "vrenBTC", "auWNEAR": "vgOHM", "auSTNEAR": "vDPX", "auUSDC": "vGMX",
                         "auUSDT": "vGLP"}
    SITE_ID = "2"
    files = glob.glob("webserver\\0\\*.*")
    for file in files:
        contents = Path(file).read_text()
        for a in assets_to_replace:
            contents = contents.replace(a, assets_to_replace[a])
        with open("webserver\\2\\" + os.path.basename(file), "w") as the_file:
            the_file.write(contents)


def create_price_file(path, pair_name, target_month, decimals=1, eth_usdt_file=None):
    total_days = 90
    df = pd.read_csv(path)
    if eth_usdt_file:
        df1 = pd.read_csv(eth_usdt_file)
        df = pd.merge(df, df1, on="block number")
        df[" price"] = df[" price_x"] / df[" price_y"]
    rows_for_minute = len(df) / (total_days * 24 * 60)
    df = df.iloc[::int(rows_for_minute), :]
    print(df.columns)
    df.reset_index(drop=True, inplace=True)
    df["timestamp_x"] = datetime.datetime.now()
    df["ask_price"] = df[" price"] / decimals
    df["bid_price"] = df[" price"] / decimals
    df = df[["timestamp_x", "bid_price", "ask_price"]]
    l = len(df)
    rows_for_month = int(l / total_days) * 30
    index = 0
    for i in target_month:
        df1 = df.iloc[index * rows_for_month:(index + 1) * rows_for_month]
        df1.reset_index(drop=True, inplace=True)
        start_date = datetime.datetime(int(i[1]), int(i[0]), 1).timestamp()
        df1["timestamp_x"] = (start_date + df1.index * 60) * (1000 * 1000)
        df1.to_csv("data\\data_unified_" + i[1] + "_" + i[0] + "_" + pair_name + ".csv", index=False)
        index += 1


def create_production_accounts_graph(SITE_ID, field_name, lending_name, single_base=None):
    plt.cla()
    plt.close()
    json_name = "accounts.json"
    results = get_all_sub_folders(SITE_ID, json_name)
    xy = {}
    for result in results:
        try:
            x = result
            for base in results[result]:
                if base == "json_time": continue
                if base not in xy:
                    xy[base] = {}

                y = results[result][base][field_name]
                xy[base][x] = y
        except Exception as e:
            print("Error")

    for base in xy:
        if single_base and single_base != base: continue
        xx = [datetime.datetime.fromtimestamp(float(x)) for x in sorted(xy[base])]
        yy = [float(xy[base][x]) for x in sorted(xy[base])]
        y_last = yy[-1]

        if single_base:
            y_last = 1

        if y_last > 0:
            yy = [y / y_last for y in yy]
            plt.scatter(xx, yy, label=base)
            plt.plot(xx, yy, label=base)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()

    fig = plt.gcf()
    fig.set_size_inches(16.5, 8.5)

    plt.title(lending_name)
    plt.suptitle(field_name)
    plt.legend(loc="lower left")
    report_type = "all" if not single_base else single_base
    plt.savefig("results\\" + lending_name + "." + report_type + "." + field_name + ".accounts.jpg")


def create_production_slippage_graph(SITE_ID, lending_name):
    plt.cla()
    plt.close()
    json_name = "usd_volume_for_slippage.json"
    results = get_all_sub_folders(SITE_ID, json_name)
    xy = {}
    for result in results:
        print(result)
        try:
            x = datetime.datetime.fromtimestamp(float(result))
            for base in results[result]:
                if base == "json_time": continue
                for quote in results[result][base]:
                    if base not in xy:
                        xy[base] = {}
                    if quote not in xy[base]:
                        xy[base][quote] = {}
                    y = results[result][base][quote]["volume"]
                    xy[base][quote][x] = y
        except Exception as e:
            print("Error")

    for base in xy:
        for quote in xy[base]:
            xx = [x for x in sorted(xy[base][quote])]
            yy = [float(xy[base][quote][x]) for x in sorted(xy[base][quote])]
            y_last = yy[-1]
            if y_last > 0:
                yy = [y / y_last for y in yy]
                plt.scatter(xx, yy)
                plt.plot(xx, yy, label=base + "-" + quote)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()

    fig = plt.gcf()
    fig.set_size_inches(16.5, 8.5)

    plt.title(lending_name)
    plt.suptitle("Slippage")

    plt.legend(loc="lower left")
    plt.savefig("results\\" + lending_name + ".slippage.jpg")

# create_price_file("..\\monitor-backend\\GLP\\glp.csv", "GLPUSDT",
#                   [("04", "2022"), ("05", "2022"), ("06", "2022")], 1, None)
#
#
# create_price_file("..\\monitor-backend\\ArbitrumDEX\\ohm-dai-mainnet.csv", "OHMUSDT",
#                   [("04", "2022"), ("05", "2022"), ("06", "2022")], 1e9, None)

# create_price_file("..\\monitor-backend\\ArbitrumDEX\\eth-gmx-arbitrum.csv", "GMXUSDT",
#                   [("04", "2022"), ("05", "2022"), ("06", "2022")], 1,
#                   "..\\monitor-backend\\ArbitrumDEX\\eth-dai-arbitrum.csv")
#
# create_price_file("..\\monitor-backend\\ArbitrumDEX\\eth-dpx-arbitrum.csv", "DPXUSDT",
#                   [("04", "2022"), ("05", "2022"), ("06", "2022")], 1,
#                   "..\\monitor-backend\\ArbitrumDEX\\eth-dai-arbitrum.csv")

# lending_platform_json_file = ".." + os.path.sep + "monitor-backend" + os.path.sep + "vesta" + os.path.sep + "data.json"
# chain_id = "arbitrum"
# kp = kyber_prices.KyberPrices(lending_platform_json_file, chain_id)
# print(kp.get_price("VST", "renBTC", 1000))
# compare_to_prod_and_send_alerts("aurigami","0","0\\2022-11-18-20-28", "", "")