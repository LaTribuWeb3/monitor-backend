import itertools
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import copy
import utils


def calc_liquidation_size(safe_ratio, curr_price, usd_collateral, btc_debt, liquidation_bonus,
                          usd_portion_in_liquidation):
    try:
        curr_ratio = usd_collateral / (btc_debt * curr_price)

        # currently, rekt beyond repair
        if (curr_ratio <= (1 + liquidation_bonus)):
            return {"usd_liquidation": 0, "burned_btc": 0, "derrivative": 0}

        liquidation_size = (usd_collateral - safe_ratio * btc_debt * curr_price) / (
                    usd_portion_in_liquidation - safe_ratio / (1 + liquidation_bonus))

        burned_btc = liquidation_size / (curr_price * (1 + liquidation_bonus))
        usd_liquidation_size = liquidation_size * usd_portion_in_liquidation

        if burned_btc > btc_debt:
            usd_liquidation_size *= btc_debt / burned_btc
            burned_btc = btc_debt
        if usd_liquidation_size > usd_collateral:
            burned_btc *= usd_collateral / usd_liquidation_size
            usd_liquidation_size = usd_collateral

        derrivative = -(safe_ratio * btc_debt * curr_price - usd_collateral) / (
                    (safe_ratio / (1 + liquidation_bonus) - usd_portion_in_liquidation) ** 2)

        return {"usd_liquidation": usd_liquidation_size, "burned_btc": burned_btc, "derrivative": derrivative}
    except Exception as e:
        print("ERROR", e)
        print(safe_ratio, curr_price, usd_collateral, btc_debt, liquidation_bonus, usd_portion_in_liquidation)
        exit()

def adjust_series_price(df, factor):
    last_price = 0
    last_adjusted_price = 0
    for index, row in df.iterrows():
        price = (row["ask_price"] + row["bid_price"]) * 0.5
        if last_price != 0:
            price_change = ((price / last_price) - 1) * float(factor)
            adjust_price = last_adjusted_price + last_adjusted_price * price_change
        else:
            adjust_price = price

        df.at[index, "price"] = price
        df.at[index, "adjust_price"] = adjust_price
        last_adjusted_price = adjust_price
        last_price = price
    return copy.deepcopy(df)


def convert_to_array(dai_eth):
    arr = []
    for index, row in dai_eth.iterrows():
        arr.append({"timestamp_x": row["timestamp_x"],
                    "usd_price": (1 / row["adjust_price"]),
                    "flare_price": (1 / row["flare_price"])})
    return arr


def crete_price_trajectory(data, btc_std, flare_std):
    data1 = adjust_series_price(data, btc_std)
    data2 = adjust_series_price(data, flare_std)
    data1["flare_price"] = data2["adjust_price"]

    dai_eth_array = convert_to_array(data1)
    return dai_eth_array


def create_liquidation_df(collateral_volume, debt_volume, min_cr):
    return pd.DataFrame()


def run_single_simulation(date_file_name,
                          usd_std, flr_std,
                          debt_volume, usd_collateral_volume, flr_collateral_volume,
                          usd_d_l, usd_d_l_recovery,
                          flr_d_l, flr_d_l_recovery,
                          min_cr, safe_cr, usd_collateral_ratio):

    initial_debt_volume_for_simulation = debt_volume
    initial_flr_collateral_volume_for_simulation = flr_collateral_volume
    initial_usd_collateral_volume_for_simulation = usd_collateral_volume

    initial_usd_dex_liquidity_volume_for_simulation = usd_d_l
    initial_flr_dex_liquidity_volume_for_simulation = flr_d_l

    try:

        usd_liquidity_table = []
        flr_liquidity_table = []
        time_series_report = []
        data = pd.read_csv(date_file_name)
        # liquidation_df = create_liquidation_df(collateral_volume, debt_volume, min_cr)
        file = crete_price_trajectory(data, usd_std, flr_std)

        state = 0
        min_ucr = float('inf')

        debt_volume /= file[0]["usd_price"]
        usd_d_l /= file[0]["usd_price"]
        flr_d_l /= file[0]["flare_volume"]

        initial_adjust_dept_volume_for_simulation = debt_volume
        total_liquidations = 0
        for row in file:
            row_price = row["adjust_price"]
            ucr = usd_collateral_volume / (debt_volume * row_price)
            min_ucr = min(min_ucr, ucr)
            available_usd_d_l = usd_d_l - sum(usd_liquidity_table)
            available_flr_d_l = flr_d_l - sum(flr_liquidity_table)
            open_liquidation = 0
            burned_btc_volume = 0
            if ucr <= min_cr or (state == 1 and ucr <= safe_cr):
                state = 1
                l_size = calc_liquidation_size(safe_cr, row_price, usd_collateral_volume, debt_volume, 0.1,
                                               usd_collateral_ratio) # NEED TO BE REPLACED
                burned_btc_volume = l_size["burned_btc"]
                usd_liquidation_volume = l_size["usd_liquidation"]
                flr_liquidation_volume = l_size["flr_liquidation"]

                if burned_btc_volume > debt_volume:
                    print(safe_cr, row_price, usd_liquidation_volume, debt_volume, 0.1, usd_collateral_ratio)
                    print(burned_btc_volume, debt_volume)
                    print("XXXX")
                    exit()

                if burned_btc_volume * usd_collateral_ratio > available_usd_d_l:
                    open_liquidation = burned_btc_volume * usd_collateral_ratio - available_usd_d_l
                    usd_liquidation_volume *= (available_usd_d_l / burned_btc_volume)
                    burned_btc_volume = available_usd_d_l / usd_collateral_ratio

                usd_collateral_volume -= usd_liquidation_volume
                flr_collateral_volume -= flr_liquidation_volume
                total_liquidations += burned_btc_volume
                debt_volume -= burned_btc_volume
                usd_liquidity_table.append(burned_btc_volume * usd_collateral_ratio)
                flr_liquidity_table.append(burned_btc_volume * (1 - usd_collateral_ratio))

            else:
                usd_liquidity_table.append(0)
                flr_liquidity_table.append(0)
                state = 0

            # print(ucr, collateral_volume, debt_volume, available_d_l)
            usd_liquidity_table_size = len(usd_liquidity_table)
            if usd_liquidity_table_size > usd_d_l_recovery:
                usd_liquidity_table = usd_liquidity_table[usd_liquidity_table_size:]

            flr_liquidity_table_size = len(flr_liquidity_table)
            if flr_liquidity_table_size > flr_d_l_recovery:
                flr_liquidity_table = flr_liquidity_table[flr_liquidity_table_size:]


            report_row = {"simulation_file_name": simulation_file_name,
                          "timestamp": row["timestamp_x"],
                          "simulation_initial_debt_volume": initial_adjust_dept_volume_for_simulation,
                          "price": row_price,
                          "debt_volume": debt_volume,
                          "usd_collateral_volume": usd_collateral_volume,
                          "flr_collateral_volume": flr_collateral_volume,
                          "usd_trade_volume": burned_btc_volume * usd_collateral_ratio,
                          "flr_trade_volume": burned_btc_volume * (1 - usd_collateral_ratio),
                          "available_usd_d_l": available_usd_d_l,
                          "available_flr_d_l": available_flr_d_l,
                          "total_liquidations": total_liquidations,
                          "open_liquidation": open_liquidation,
                          "ucr": ucr,
                          "min_ucr": min_ucr}

            time_series_report.append(report_row)

        time_series_report_name = f"webserver\\flare\\" + SITE_ID + "\\" \
                                                                    f"UsdStd-{usd_std}+" \
                                                                    f"FlareStd-{flr_std}+" \
                                                                    f"DebtVolume-{round(initial_debt_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"UsdCollateralVolume-{round(initial_usd_collateral_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"FlareCollateralVolume-{round(initial_flr_collateral_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"UsdDexLiquidity-{round(initial_usd_dex_liquidity_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"FlareDexLiquidity-{round(initial_flr_dex_liquidity_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"UsdDexLiquidityRecovery-{usd_d_l_recovery}+" \
                                                                    f"FlareDexLiquidityRecovery-{flr_d_l_recovery}+" \
                                                                    f"MinCr-{min_cr}+" \
                                                                    f"SafeCr-{safe_cr}+" \
                                                                    f"UsdCollateralRatio-{usd_collateral_ratio}"

        report_df = pd.DataFrame(time_series_report)
        # report_df.to_csv(time_series_report_name + ".csv")
        plt.cla()
        plt.close()
        fig, ax1 = plt.subplots()
        fig.set_size_inches(12.5, 8.5)
        ax2 = ax1.twinx()

        plt.suptitle("Min CR: " + str(round(min_ucr, 2)))
        x1 = ax1.plot(report_df["timestamp"], report_df["price"] / report_df["price"].max(), 'r-', label="Price")
        x2 = ax2.plot(report_df["timestamp"], report_df["ucr"], label="CR")
        x3 = ax2.plot(report_df["timestamp"], report_df["debt_volume"] / report_df["simulation_initial_debt_volume"],
                      label="DebtVolume")
        x4 = ax2.plot(report_df["timestamp"],
                      report_df["usd_collateral_volume"] / pow(report_df["simulation_initial_debt_volume"], 2),
                      label="UsdCollateralVolume")
        x5 = ax2.plot(report_df["timestamp"],
                      report_df["flr_collateral_volume"] / pow(report_df["simulation_initial_debt_volume"], 2),
                      label="FlareCollateralVolume")
        x6 = ax2.plot(report_df["timestamp"], report_df["open_liquidation"] / report_df["simulation_initial_debt_volume"],
                      label="OpenLiquidations")
        x7 = ax2.plot(report_df["timestamp"], report_df["total_liquidations"] / report_df["simulation_initial_debt_volume"],
                      label="TotalLiquidations")

        lns = x1 + x2 + x3 + x4 + x5 + x6 + x7
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        plt.savefig(time_series_report_name + ".jpg")
        print("min_ucr", min_ucr)

        return {"usd_std": usd_std,
                "flr_std": flr_std,
                "debt_volume": initial_debt_volume_for_simulation,
                "usd_collateral_volume": initial_usd_collateral_volume_for_simulation,
                "flare_collateral_volume": initial_flr_collateral_volume_for_simulation,
                "usd_d_l": initial_usd_dex_liquidity_volume_for_simulation,
                "usd_d_l_recovery": usd_d_l_recovery,
                "flare_d_l": initial_flr_dex_liquidity_volume_for_simulation,
                "flare_d_l_recovery": flr_d_l_recovery,
                "safe_cr": safe_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_cr": min_cr}

    except Exception as e:
        print(traceback.format_exc())
        return {"usd_std": usd_std,
                "flr_std": flr_std,
                "debt_volume": initial_debt_volume_for_simulation,
                "usd_collateral_volume": initial_usd_collateral_volume_for_simulation,
                "flare_collateral_volume": initial_flr_collateral_volume_for_simulation,
                "usd_d_l": initial_usd_dex_liquidity_volume_for_simulation,
                "usd_d_l_recovery": usd_d_l_recovery,
                "flare_d_l": initial_flr_dex_liquidity_volume_for_simulation,
                "flare_d_l_recovery": flr_d_l_recovery,
                "safe_cr": safe_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_cr": -100}


def run_simulation(c, simulation_file_name):
    summary_report = []
    for r in itertools.product(c["usd_std"],c["flare_std"],
                               c["debt_volume"], c["usd_volume"], c["flare_volume"],
                               c["usd_d_l"], c["usd_d_l_recovery"],
                               c["flare_d_l"], c["flare_d_l_recovery"],
                               c["min_cr"], c["safe_cr"], c["usd_collateral_ratio"]):
        print(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11])
        report = run_single_simulation(simulation_file_name, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11])
        summary_report.append(report)
    pd.DataFrame(summary_report).to_csv("summary.csv")


ETH_PRICE = 1600
initial_dept_volume = 100_000_000
c = {
    "usd_std": [0.7],
    "flare_std": [0.7],

    "debt_volume": [initial_dept_volume],
    "usd_volume": [initial_dept_volume * 1.2, initial_dept_volume * 1.3, initial_dept_volume * 1.4,
                   initial_dept_volume * 1.5],
    "flare_volume": [0],

    "usd_d_l": [initial_dept_volume * 0.01, initial_dept_volume * 0.02,
            initial_dept_volume * 0.03, initial_dept_volume * 0.04,
            initial_dept_volume * 0.05, initial_dept_volume * 0.06,
            initial_dept_volume * 0.07, initial_dept_volume * 0.08,
            initial_dept_volume * 0.09, initial_dept_volume * 0.10],
    "usd_d_l_recovery": [30, 60, 120],
    "flare_d_l": [initial_dept_volume * 0.01, initial_dept_volume * 0.02,
                initial_dept_volume * 0.03, initial_dept_volume * 0.04,
                initial_dept_volume * 0.05, initial_dept_volume * 0.06,
                initial_dept_volume * 0.07, initial_dept_volume * 0.08,
                initial_dept_volume * 0.09, initial_dept_volume * 0.10],
    "flare_d_l_recovery": [30, 60, 120],
    "min_cr": [1.2],
    "safe_cr": [1.4],
    "usd_collateral_ratio": [0.7, 0.8, 0.9, 1]}

SITE_ID = "2023-5-9-12-50"
simulation_file_name = "c:\\dev\\monitor-backend_for_badger\\simulations\\data_worst_day\\data_unified_2020_03_ETHUSDT.csv"
run_simulation(c, simulation_file_name)
utils.publish_results("flare\\" + SITE_ID)