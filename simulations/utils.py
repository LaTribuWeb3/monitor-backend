import glob
import numpy as np
import copy
import pandas as pd
import requests
import time
import compound_parser
import datetime
import json
import matplotlib.pyplot as plt
from pathlib import Path
import os
from github import Github
import matplotlib.dates as mdates
import prettytable as pt
import math
import private_config


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

    print("30M Rolling STD Ratio", round(test_rolling_std / source_rolling_std,2))
    print("STD Ratio", round(test_std / source_std,2))
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


def convert_liquitiy_json_to_slippage(file):
    new_file = {}
    for j in file:
        for x in j["slippage"]:
            if x == 'json_time':
                new_file[x] = j["slippage"][x]
            else:
                if x in new_file:
                    for y in j["slippage"][x]:
                        new_file[x][y] = j["slippage"][x][y]
                else:
                    new_file[x] = j["slippage"][x]
    return new_file


def get_formatted_number_clean(volume):
    if volume >= 1e9:
        return str(round(volume / 1e9, 2)) + 'B'
    elif volume >= 1e6:
        return str(round(volume / 1e6, 2)) + 'M'
    elif volume >= 1e3:
        return str(round(volume / 1e3, 2)) + 'K'


def convert_tokens_json_to_oracle(file):
    new_file = {}
    for j in file:
        symbol = j["symbol"]
        new_file[symbol] = {}
        new_file[symbol]["oracle"] = float(j["priceUSD18Decimals"]) / pow(10, 18)
        new_file[symbol]["cex_price"] = float(j["cexPriceUSD18Decimals"]) / pow(10, 18)
        new_file[symbol]["dex_price"] = float(j["dexPriceUSD18Decimals"]) / pow(10, 18)
    return new_file


def send_telegram_table(bot_id, chat_id, headers, rows):
    table = pt.PrettyTable(headers)

    for row in rows:
        table.add_row(row)

    # send the message as markdown
    send_telegram_alert(bot_id, chat_id, f'```{table}```', is_markdown=True)


def compare_to_prod_and_send_alerts(old_alerts, data_time, name, base_SITE_ID, current_SITE_ID, client_chat_id,
                                    slippage_threshold=5,
                                    send_alerts=False, new_json=False, send_table=False,
                                    ignore_gb_redundant_tokens=False):
    print("comparing to prod", name)
    prod_version = get_prod_version(name)
    print(prod_version)
    if new_json:
        prod_file = convert_liquitiy_json_to_slippage(
            json.loads(get_git_json_file(base_SITE_ID, prod_version, "liquidity.json")))
        file = json.load(open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "liquidity.json"))
        last_file = convert_liquitiy_json_to_slippage(file)
    else:
        prod_file = json.loads(get_git_json_file(base_SITE_ID, prod_version, "usd_volume_for_slippage.json"))
        file = open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "usd_volume_for_slippage.json")
        last_file = json.load(file)

    time_from_now = datetime.datetime.now().timestamp() - data_time
    time_from_now /= 60
    time_from_now = str(round(time_from_now, 2)) + " Minutes (from last update)"

    time_from_prod = last_file["json_time"] - prod_file["json_time"]
    time_from_prod /= (60 * 60)
    time_from_prod = str(round(time_from_prod, 2)) + " Hours (from publication)"

    time_alert = time_from_now + "\n" + time_from_prod

    liquidityAlerts = []

    alert_sent = False
    if send_alerts:
        msg = "-------------------------------------------------"
        if send_table:
            msg += "\n"
            msg += f'Liquidity check for {name}\n'
            msg += time_alert
        send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, msg)
    for key1 in prod_file:
        if key1 == "json_time": continue

        if ignore_gb_redundant_tokens:
            if len(key1) > 3:  # this is checked to avoid ignoring CVX token but only the ones like 'cvxcrvFRAX'
                # ignore stk... cvx... yv... tokens from gearbox as they share the same liquidity as their underlying
                if str(key1).startswith('stk') or str(key1).startswith('cvx') or str(key1).startswith('yv'):
                    print('Ignoring', key1)
                    continue
        for key2 in prod_file[key1]:
            print(key1, key2)

            last_volume = last_file[key1][key2]["volume"]
            prod_volume = prod_file[key1][key2]["volume"]
            change = 100 * (round((last_volume / prod_volume) - 1, 2))
            if abs(change) > slippage_threshold:
                # last_volume = "{:,}".format(round(last_volume, 0))
                # prod_volume = "{:,}".format(round(prod_volume, 0))
                message = f"{name} " \
                          f"\n{time_alert}" \
                          f"\n{key1}.{key2}" \
                          f"\nLiquidity Change by {round(change, 2)}% " \
                          f"\nCurrent Volume: {last_volume}" \
                          f"\nLast Simulation Volume: {prod_volume}"
                print(message)
                alert_sent = True
                if send_alerts:
                    if send_table:
                        alert = {'market': key1, 'debt': key2, 'change': round(change, 2), 'last': last_volume,
                                 'prod': prod_volume}
                        liquidityAlerts.append(alert)
                    else:
                        print("Sending To TG")
                        send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, message)

                    if client_chat_id != "" and change < 0:
                        message_key = f'{name}.slippage.{key1}.{key2}'
                        last_value = 0 if message_key not in old_alerts else old_alerts[message_key]
                        if message_key not in old_alerts or abs(old_alerts[message_key]) * 1.1 < abs(change) \
                                or np.sign(old_alerts[message_key]) != np.sign(change):
                            print("Sensing To TG to client", message_key)
                            send_telegram_alert(private_config.risk_dao_bot, client_chat_id,
                                                message + "\nLast value:" + str(round(last_value, 2)))
                            if message_key not in old_alerts:
                                old_alerts[message_key] = 0
                            old_alerts[message_key] = change

    ############ SEND LIQUIDITY MESSAGE AS TABLE #############
    maxRowPerMsg = 40
    if send_alerts and send_table and len(liquidityAlerts) > 0:
        liquidityAlerts.sort(key=lambda x: abs(x['change']), reverse=True)
        alreadyAddedTokens = []
        rows = []
        for alert in liquidityAlerts:
            if alert['market'] not in alreadyAddedTokens:
                alreadyAddedTokens.append(alert['market'])
                change = alert['change']
                lastVolumeClean = get_formatted_number_clean(alert['last'])
                prodVolumeClean = get_formatted_number_clean(alert['prod'])
                rows.append([alert['market'], f'{change}%', lastVolumeClean, prodVolumeClean])
        if len(rows) > maxRowPerMsg:
            callCount = math.ceil(len(rows) / maxRowPerMsg)
            for cpt in range(callCount):
                start = cpt * maxRowPerMsg
                stop = (cpt + 1) * maxRowPerMsg
                send_telegram_table(private_config.risk_dao_bot, private_config.risk_dao_channel,
                                    ['Token', 'Change', 'Last ($)', 'Prod ($)'], rows[start:stop])

            # split
        else:
            send_telegram_table(private_config.risk_dao_bot, private_config.risk_dao_channel,
                                ['Token', 'Change', 'Last ($)', 'Prod ($)'], rows)
    ############ END SEND LIQUIDITY MESSAGE AS TABLE #############

    if not alert_sent:
        message = f"{name}" \
                  f"\n{time_alert}" \
                  f"\nSlippage is fine."
        print(message)
        if send_alerts:
            print("Sending To TG")
            send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, message)
    elif ignore_gb_redundant_tokens:
        send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel,
                            'Please note that stkcvx*, cvx* and yearn-vault tokens have been ignored as they share the same liquidity as their underlying')

    alert_sent = False
    dexAlerts = []
    cexAlerts = []

    if new_json:
        oracle_file = open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "token.json")
        oracle_file = json.load(oracle_file)
        oracle_file = convert_tokens_json_to_oracle(oracle_file)
    else:
        oracle_file = open("webserver" + os.path.sep + current_SITE_ID + os.path.sep + "oracles.json")
        oracle_file = json.load(oracle_file)

    for market in oracle_file:
        if market == "json_time": continue
        cex = float(oracle_file[market]["cex_price"])
        oracle = float(oracle_file[market]["oracle"])
        dex = float(oracle_file[market]["dex_price"])
        diff = (100 * ((oracle / dex) - 1))
        if abs(diff) > 3 and oracle > 0:
            message = f"{name}" \
                      f"\n{time_alert}" \
                      f"\n{market}" \
                      f"\nOracle<>Dex Price is off by: {round(diff, 2)}%" \
                      f"\nOracle Price: {oracle} " \
                      f"\nDex Price: {dex}"
            print(message)
            alert_sent = True
            if send_alerts:
                if send_table:
                    newDexAlert = {'market': market, 'oracle': oracle, 'dex': dex, 'diff': round(diff, 2)}
                    dexAlerts.append(newDexAlert)
                else:
                    print("Sending To TG")
                    send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, message)
                if client_chat_id != "":
                    message_key = f'{name}.oracle.dex.diff.{market}'
                    last_value = 0 if message_key not in old_alerts else old_alerts[message_key]
                    if message_key not in old_alerts or abs(old_alerts[message_key]) * 1.1 < abs(diff) \
                            or np.sign(old_alerts[message_key]) != np.sign(diff):
                        print("Sensing To TG to client", message_key)
                        send_telegram_alert(private_config.risk_dao_bot, client_chat_id,
                                            message + "\nLast value:" + str(round(last_value, 2)))
                        if message_key not in old_alerts:
                            old_alerts[message_key] = 0
                        old_alerts[message_key] = diff

        if cex > 0 and oracle > 0:
            diff = (100 * ((oracle / cex) - 1))
            if abs(diff) > 3:
                message = f"{name}" \
                          f"\n{time_alert}" \
                          f"\n{market} " \
                          f"\nOracle<>Cex Price is off by: {round(diff, 2)}%" \
                          f"\nOracle Price: {oracle} " \
                          f"\nCex Price: {cex}"
                print(message)
                alert_sent = True
                if send_alerts:
                    if send_table:
                        newCexAlert = {'market': market, 'oracle': oracle, 'cex': cex, 'diff': round(diff, 2)}
                        cexAlerts.append(newCexAlert)
                    else:
                        print("Sending To TG")
                        send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, message)

                    if client_chat_id != "":
                        message_key = f'{name}.oracle.cex.diff.{market}'
                        last_value = 0 if message_key not in old_alerts else old_alerts[message_key]
                        if message_key not in old_alerts or abs(old_alerts[message_key]) * 1.1 < abs(diff) \
                                or np.sign(old_alerts[message_key]) != np.sign(diff):
                            print("Sensing To TG to client", message_key)
                            send_telegram_alert(private_config.risk_dao_bot, client_chat_id,
                                                message + "\nLast value:" + str(round(last_value, 2)))
                            if message_key not in old_alerts:
                                old_alerts[message_key] = 0
                            old_alerts[message_key] = diff

    if send_alerts and send_table and len(dexAlerts) > 0:
        msg = "-------------------------------------------------"
        msg += "\n"
        msg += f'Oracle check for {name}\n'
        msg += time_alert
        send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, msg)

    if send_alerts and send_table and len(dexAlerts) > 0:
        dexAlerts.sort(key=lambda x: abs(x['diff']))
        rowsDex = []
        for alert in dexAlerts:
            diff = alert['diff']
            rowsDex.append([alert['market'], alert['oracle'], alert['dex'], f'{diff}%'])

        send_telegram_table(private_config.risk_dao_bot, private_config.risk_dao_channel,
                            ['Market', 'Oracle', 'Dex', 'Diff'], rowsDex)

    if send_alerts and send_table and len(cexAlerts) > 0:
        cexAlerts.sort(key=lambda x: abs(x['diff']), reverse=True)
        rowsCex = []
        for alert in cexAlerts:
            diff = alert['diff']
            rowsCex.append([alert['market'], alert['oracle'], alert['cex'], f'{diff}%'])

        send_telegram_table(private_config.risk_dao_bot, private_config.risk_dao_channel,
                            ['Market', 'Oracle', 'Cex', 'Diff'], rowsCex)

    if not alert_sent:
        message = f"{name}" \
                  f"\n{time_alert}" \
                  f"\nOracle is fine."
        print(message)
        if send_alerts:
            print("Sending To TG")
            send_telegram_alert(private_config.risk_dao_bot, private_config.risk_dao_channel, message)

    return old_alerts


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


def publish_results(SITE_ID, target=None):
    print("publish_results")
    if private_config.git_token == "":
        print("Git Upload Failed. no Token")
        exit()

    if target is None:
        target = SITE_ID
    target = target.replace('\\', '/')
    gh = Github(login_or_token=private_config.git_token, base_url='https://api.github.com', timeout= 60)
    repo_name = "Risk-DAO/simulation-results"
    repo = gh.get_repo(repo_name)
    files = glob.glob("webserver" + os.path.sep + SITE_ID + os.path.sep + "*.json")
    print(files)
    for f in files:
        file = open(f)
        git_file = target + "/" + os.path.basename(f)
        print(git_file)
        sha = None
        try:
            oldFile = repo.get_contents(git_file)
            sha = oldFile.sha
        except Exception as e:
            print(e)
        
        if(sha != None):
            print('will update old file: ', oldFile)
            repo.update_file(git_file, 'Commit Comments', file.read(), sha)

        else:
            print('will create new file: ', git_file)
            repo.create_file(git_file, "Commit Comments", file.read())

lastTGCallDate = None


def send_telegram_alert(bot_id, chat_id, message):
    url = f'https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={chat_id}&text={message}'
    print(url)
    requests.get(url)


def send_telegram_alert1(bot_id, chat_id, message, is_markdown=False):
    callData = {
        "chat_id": chat_id,
        "text": message,
    }

    if is_markdown:
        callData['parse_mode'] = 'MarkdownV2'
    callDataJson = json.dumps(callData)

    global lastTGCallDate
    if lastTGCallDate == None:
        lastTGCallDate = datetime.datetime.now()

    # print('lastTGCallDate', lastTGCallDate)
    url = f'https://api.telegram.org/bot{bot_id}/sendMessage'
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    now = datetime.datetime.now()
    secToWait = 3 - (now - lastTGCallDate).total_seconds()  # wait 3 seconds between each calls
    if secToWait > 0:
        print('Sleeping', secToWait, 'seconds before calling telegram')
        time.sleep(secToWait)

    mustResend = True
    cptSleep = 1
    while mustResend:
        mustResend = False
        lastTGCallDate = datetime.datetime.now()
        # print('new lastTGCallDate', lastTGCallDate)
        tgResponse = requests.post(url, data=callDataJson, headers=headers)
        if tgResponse.status_code < 400:
            mustResend = False
        elif tgResponse.status_code == 429:
            mustResend = True
            print('Sleeping', cptSleep, 'seconds before re calling tg')
            time.sleep(cptSleep)
            cptSleep += cptSleep  # exponential backoff
        else:
            print('error when sending tg alert', tgResponse.status_code, tgResponse.reason)


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
            else:
                print(base, quote, "is out!!!")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()

    fig = plt.gcf()
    fig.set_size_inches(16.5, 8.5)

    plt.title(lending_name)
    plt.suptitle("Slippage")

    plt.legend(loc="lower left")
    plt.savefig("results\\" + lending_name + ".slippage.jpg")
