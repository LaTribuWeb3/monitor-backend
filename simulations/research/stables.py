import glob
import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np


def valid_move(last_valid_price, current_price, test_price, max_error):
    last_current_change = (current_price / last_valid_price - 1) * 100
    current_test_change = (test_price / current_price - 1) * 100
    if np.sign(last_current_change) == np.sign(current_test_change):
        return True
    if abs(last_current_change) > max_error * 2 and abs(current_test_change) > max_error * 2:
        return False
    return abs(test_price - current_price) <= abs(test_price - last_valid_price)


def clean_df(df, max_error):
    last_valid_price = df.iloc[0]["price"]
    end_running = False
    max_block = df["block"].max()
    while not end_running:
        end_running = True
        print(df["to_delete"].sum())

        for index, row in df.iterrows():

            if row["to_delete"] == 1: continue
            current_price = row["price"]
            max_price = max(current_price, last_valid_price)
            min_price = min(current_price, last_valid_price)
            err = (max_price / min_price - 1) * 100
            if err > max_error:
                current_block = row["block"]
                test_block = current_block + 2
                if test_block <= max_block:
                    test_price = df.loc[df["block"] >= test_block].iloc[0]["price"]
                    if not valid_move(last_valid_price, current_price, test_price, max_error):
                        df.loc[index, 'to_delete'] = 1
                        end_running = False
                        break
    return df

def calc_trend_resistance(file_name, interval, asset):

    df = pd.read_csv(file_name).sort_values("block")
    df["deal_type"] = "buy"
    df.loc[df["inTokn"] == asset, "deal_type"] = "sell"

    df["deal_asset_volume"] = df["outAmount"]
    df.loc[df["deal_type"] == "sell", "deal_asset_volume"] = df["inAmount"]

    df["deal_asset_in_quote_price"] = df["inAmount"] / df["outAmount"]
    df.loc[df["deal_type"] == "sell", "deal_asset_in_quote_price"] = df["outAmount"] / df["inAmount"]

    df["deal_token"] = df["inTokn"]
    df.loc[df["deal_type"] == "sell", "deal_token"] = df["outToken"]
    # df.to_csv(file_name + '.xxx.csv')
    min_block = df["block"].min()
    max_block = df["block"].max()
    blocks_data = []
    while min_block < max_block:
        start_block = min_block
        end_block = start_block + interval
        block_data = df.loc[(df["block"] >= start_block) & (df["block"] <= end_block)]
        block_data = block_data.reset_index(drop=True)
        if len(block_data) > 0:
            start_price = float(block_data.head(1)["deal_asset_in_quote_price"])
            end_price = float(block_data.tail(1)["deal_asset_in_quote_price"])
            total_buy_volume = block_data.loc[block_data["deal_type"] == "buy"]["deal_asset_volume"].sum()
            total_sell_volume = block_data.loc[block_data["deal_type"] == "sell"]["deal_asset_volume"].sum()
            blocks_data.append({"start_block":start_block, "end_block":end_block,
                                "start_price":start_price, "end_price":end_price,
                                "total_buy_volume":total_buy_volume, "total_sell_volume":total_sell_volume})
            print(start_block, end_block, int(total_buy_volume), int(total_sell_volume), start_price, end_price)
        min_block += interval

    return blocks_data


def calc_trend_resistance1(file_name, interval, asset):
    df = pd.read_csv(file_name).sort_values("block number")
    df["deal_type"] =  "buy"
    df.loc[df[" buy"] == False, "deal_type"] = "sell"
    df["deal_asset_volume"] = df[" qty1"]
    min_block = df["block number"].min()
    max_block = df["block number"].max()
    print(min_block,max_block)
    blocks_data = []
    while min_block < max_block:
        start_block = min_block
        end_block = start_block + interval
        block_data = df.loc[(df["block number"] >= start_block) & (df["block number"] <= end_block)]
        total_buy_volume = block_data.loc[block_data["deal_type"] == "buy"]["deal_asset_volume"].sum()
        total_sell_volume = block_data.loc[block_data["deal_type"] == "sell"]["deal_asset_volume"].sum()
        blocks_data.append({"start_block":start_block, "end_block":end_block, "total_buy_volume":total_buy_volume, "total_sell_volume":total_sell_volume})
        print(start_block, end_block, total_buy_volume, total_sell_volume)
        min_block += interval

    return blocks_data

files = glob.glob("data2\\*")
for file in files:
    asset_name = os.path.basename(file).replace(".csv", "")
    print(file, asset_name)
    blocks_data = calc_trend_resistance(file,5 * 4 * 60, asset_name)
    pd.DataFrame(blocks_data).to_csv(asset_name + ".blocks.csv")

# files = glob.glob("*blocks.csv")
# for file in files:
#     df = pd.read_csv(file)
#     file_data = []
#     total_volume = 0
#     total_buy_volume = 0
#     total_sell_volume = 0
#     for index, row in df.iterrows():
#         buy_volume = row["total_buy_volume"]
#         sell_volume = row["total_sell_volume"]
#         total_buy_volume += buy_volume
#         total_sell_volume += sell_volume
#         total_volume +=  buy_volume + sell_volume
#         if total_volume > 5_000_000:
#             print(0, 0, int(total_buy_volume), int(total_sell_volume))
#             file_data.append(
#                 {"start_block": 0, "end_block": 0, "total_buy_volume": total_buy_volume,
#                  "total_sell_volume": total_sell_volume})
#             total_volume = 0
#             total_buy_volume = 0
#             total_sell_volume = 0
#     pd.DataFrame(file_data) .to_csv(file)

# files = glob.glob("*blocks.csv")
# for file in files:
#     data = pd.read_csv(file)
#     plt.cla()
#     plt.close()
#     data["err"] = abs(data["total_buy_volume"] - data["total_sell_volume"]) / (data["total_buy_volume"] + data["total_sell_volume"])
#     data["weighted_err"] = data["err"] * (data["total_buy_volume"] + data["total_sell_volume"])
#     weighted_err = data["weighted_err"].sum() / (data["total_buy_volume"].sum() + data["total_sell_volume"].sum())
#     plt.suptitle(file + " weighted error." + str(round(weighted_err, 2)))
#     plt.scatter(data.index, (abs(data["total_buy_volume"] - data["total_sell_volume"]))  / (data["total_buy_volume"] + data["total_sell_volume"]))
#     plt.ylim([0,1])
#     plt.savefig(file + ".jpg")


# files = glob.glob("data\\*.csv")
# all_dfs = {}
# for file in files:
#     print(file)
#     df = pd.read_csv(file)
#     df["to_delete"] = 0
#     asset = os.path.basename(file).replace(".csv", "")
#     df = clean_df(df, 2)
#     clean = df.loc[df["to_delete"] == 0]
#     plt.cla()
#     plt.close()
#     plt.suptitle("Asset. " + asset + " Total Errors. " + str(len(df.loc[df["to_delete"] == 1])))
#     #plt.plot(df["block"], df["price"], label="With errors")
#     plt.plot(clean["block"], clean["price"], label="Clean", color="green")
#     plt.savefig("results\\" + asset + ".jpg")


# min_price = block_data["deal_asset_in_quote_price"].min()
# max_price = block_data["deal_asset_in_quote_price"].max()
# min_price_block = int(block_data.loc[block_data["deal_asset_in_quote_price"] == min_price].iloc[0]["block"])
# max_price_block = int(block_data.loc[block_data["deal_asset_in_quote_price"] == max_price].iloc[0]["block"])
# block_trend = ""
# if min_price_block > max_price_block:
#     block_data = block_data.loc[(df["block"] >= max_price_block) & (df["block"] <= min_price_block)]
#     block_trend = "long"
#     start_price = min_price
#     end_price = max_price
# else:
#     block_data = block_data.loc[(df["block"] >= min_price_block) & (df["block"] <= max_price_block)]
#     block_trend = "short"
#     start_price = max_price
#     end_price = min_price
#
# min_to_max = round(100 * ((max_price / min_price) - 1), 2)
# if min_to_max > 2:
