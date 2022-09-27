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


files = glob.glob("data\\*.csv")
all_dfs = {}
for file in files:
    print(file)
    df = pd.read_csv(file)
    df["to_delete"] = 0
    asset = os.path.basename(file).replace(".csv", "")
    df = clean_df(df, 2)
    clean = df.loc[df["to_delete"] == 0]
    plt.cla()
    plt.close()
    plt.suptitle("Asset. " + asset + " Total Errors. " + str(len(df.loc[df["to_delete"] == 1])))
    #plt.plot(df["block"], df["price"], label="With errors")
    plt.plot(clean["block"], clean["price"], label="Clean", color="green")
    plt.savefig("results\\" + asset + ".jpg")