import glob

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import  sys
#,ts,price,ebtc_balance,wbtc_balance,curve_price,liquidation_volume,open_liquidations_count,total_lquidations_checked,total_lquidations_vlosed,before_tick_wbtc_balance,before_tick_ebtc_balance,after_tick_wbtc_balance,after_tick_ebtc_balance,open_liquidations,trade_volume,max_drop,pnl

ETH_PRICE = 1600
BTC_TO_ETH = 16
dir_name = sys.argv[1]
file_name = "*unified_2020_03_*"

# dir_name = "c:\dev\\monitor-backend\simulations\\simulation_results\\badger\\2023-3-16-14-40\\"
# file_name = "data_worst_data_unified_2020_03_ETHUSDT.csv_ETH-BTC_stability_report.csv"

files = glob.glob(dir_name + file_name)
for file in files:
    print(file)
    df1 = pd.read_csv(file)
    volume = 50_000_000


    for index, row in df1.iterrows():
        if row["const_cr"] != 0 or row["min_cr"] > 0 :
            print("Skipped", row["const_cr"], row["min_cr"])
            continue
        plt.cla()
        plt.close()
        volume = row["volume_for_slippage_10_percents"] * ETH_PRICE
        file_name = f"bib-{round(row['box_initial_balance'], 2)}+brh-{row['box_recovery_halflife']}+vfs-{round(row['volume_for_slippage_10_percents'] * ETH_PRICE / row['collateral'], 2)}+clf-{row['collateral_liquidation_factor']}"
        title = f"Max Drop: {round(row['max_drop'],2)} Liquidation Score: {round(row['open_volume_score'],2)}"

        df = pd.read_csv(dir_name + row["simulation_name"] + ".csv")
        df["price1"] = df["price"] / df["price"].max()
        df["liquidation_volume"] = df["liquidation_volume"].rolling(30).sum()
        df["market_volume"] = volume * (1.1 - df["curve_price"]) / 0.1
        fig, ax1 = plt.subplots()
        fig.set_size_inches(12.5, 8.5)
        ax2 = ax1.twinx()
        x1 = ax1.plot(df["ts"], df["price1"], 'r-', label="ETH/BTC price")
        x2 = ax1.plot(df["ts"], df["curve_price"],  "g-", label="curve_price")
        ax1.set_ylim([0, 1.2])
        ax1.set_yticks(np.arange(0, 1.2, 0.1))

        x3 = ax2.plot(df["ts"], (df["ebtc_balance"] * ETH_PRICE) / 1_000_000, 'm-',
                  label="ebtc balance")
        x4 = ax2.plot(df["ts"], (df["open_liquidations"] * ETH_PRICE) / 1_000_000, 'y-', label="open_liquidations")
        x5 = ax2.plot(df["ts"], (df["liquidation_volume"] * ETH_PRICE) / 1_000_000, 'b-', label="liquidation_volume")
        x6 = ax2.plot(df["ts"], df["market_volume"] / 1_000_000, 'k-', label="market_volume")

        lns = x1 + x2 + x3 + x4 + x5 + x6
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)

        ax1.set_label('Time')
        plt.title(title)
        print(file_name)
        plt.savefig("results/" + file_name + ".jpg")
        #plt.show()
