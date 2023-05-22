import itertools
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import copy
import utils


def calc_liquidation_size(safe_ratio, curr_price, usd_collateral, btc_debt, liquidation_bonus,
                          usd_portion_in_liquidation):
    #flare_volume, flare_price, flare_recovery,
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
        arr.append({"timestamp_x": row["timestamp_x"], "adjust_price": (1 / row["adjust_price"]) * 3000})
    return arr


def crete_price_trajectory(data, std):
    data1 = adjust_series_price(data, std)
    dai_eth_array = convert_to_array(data1)
    return dai_eth_array


def create_liquidation_df(collateral_volume, debt_volume, min_cr):
    return pd.DataFrame()


def run_single_simulation(date_file_name, std, collateral_volume, debt_volume, flare_volume,
                          d_l, d_l_recovery, min_cr, safe_cr, usd_collateral_ratio):

    initial_dept_volume_for_simulation = debt_volume
    initial_flare_volume_for_simulation = flare_volume
    initial_collateral_volume_for_simulation = collateral_volume
    initial_dex_liquidity_volume_for_simulation = d_l

    try:

        liquidity_table = []
        time_series_report = []
        data = pd.read_csv(date_file_name)
        # liquidation_df = create_liquidation_df(collateral_volume, debt_volume, min_cr)
        file = crete_price_trajectory(data, std)

        state = 0
        min_ucr = float('inf')

        debt_volume /= file[0]["adjust_price"]
        d_l /= file[0]["adjust_price"]

        initial_adjust_dept_volume_for_simulation = debt_volume
        total_liquidations = 0
        for row in file:
            row_price = row["adjust_price"]
            ucr = collateral_volume / (debt_volume * row_price)
            min_ucr = min(min_ucr, ucr)
            available_d_l = d_l - sum(liquidity_table)
            open_liquidation = 0
            btc_volume = 0
            if ucr <= min_cr or (state == 1 and ucr <= safe_cr):
                state = 1
                l_size = calc_liquidation_size(safe_cr, row_price, collateral_volume, debt_volume, 0.1,
                                               usd_collateral_ratio)
                btc_volume = l_size["burned_btc"]
                if btc_volume > debt_volume:
                    print(safe_cr, row_price, collateral_volume, debt_volume, 0.1, usd_collateral_ratio)
                    print(btc_volume, debt_volume)
                    print("XXXX")
                    exit()
                usd_volume = l_size["usd_liquidation"]
                if btc_volume * usd_collateral_ratio > available_d_l:
                    open_liquidation = btc_volume * usd_collateral_ratio - available_d_l
                    usd_volume *= (available_d_l / btc_volume)
                    btc_volume = available_d_l / usd_collateral_ratio

                collateral_volume -= usd_volume
                total_liquidations += btc_volume
                debt_volume -= btc_volume
                liquidity_table.append(btc_volume * usd_collateral_ratio)
            else:
                liquidity_table.append(0)
                state = 0

            # print(ucr, collateral_volume, debt_volume, available_d_l)
            liquidity_table_size = len(liquidity_table)
            if liquidity_table_size > d_l_recovery:
                liquidity_table = liquidity_table[liquidity_table_size:]

            report_row = {"simulation_file_name": simulation_file_name,
                          "timestamp": row["timestamp_x"],
                          "simulation_initial_debt_volume": initial_adjust_dept_volume_for_simulation,
                          "price": row_price,
                          "collateral_volume": collateral_volume,
                          "trade_volume": btc_volume * usd_collateral_ratio,
                          "debt_volume": debt_volume,
                          "available_d_l": available_d_l,
                          "total_liquidations": total_liquidations,
                          "open_liquidation": open_liquidation,
                          "ucr": ucr,
                          "min_ucr": min_ucr}

            time_series_report.append(report_row)

        time_series_report_name = f"webserver\\flare\\" + SITE_ID + "\\" \
                                                                    f"Std-{std}+" \
                                                                    f"CollateralVolume-{round(initial_collateral_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"DebtVolume-{round(initial_dept_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"FlareVolume-{round(initial_flare_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"DexLiquidity-{round(initial_dex_liquidity_volume_for_simulation / initial_dept_volume, 2)}+" \
                                                                    f"DexLiquidityRecovery-{d_l_recovery}+" \
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
                      report_df["collateral_volume"] / pow(report_df["simulation_initial_debt_volume"], 2),
                      label="CollateralVolume")
        x5 = ax2.plot(report_df["timestamp"], report_df["open_liquidation"] / report_df["simulation_initial_debt_volume"],
                      label="OpenLiquidations")
        x6 = ax2.plot(report_df["timestamp"], report_df["total_liquidations"] / report_df["simulation_initial_debt_volume"],
                      label="TotalLiquidations")
        # x7 = ax2.plot(report_df["timestamp"], report_df["available_d_l"] / report_df["available_d_l"].max(),
        #               label="AvailableDexLiquidity")

        lns = x1 + x2 + x3 + x4 + x5 + x6# + x7
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        plt.savefig(time_series_report_name + ".jpg")
        print("min_ucr", min_ucr)

        return {"td": std,
                "collateral_volume": initial_collateral_volume_for_simulation,
                "debt_volume": initial_dept_volume_for_simulation,
                "flare_volume": initial_flare_volume_for_simulation,
                "d_l": initial_dex_liquidity_volume_for_simulation,
                "d_l_recovery": d_l_recovery,
                "safe_cr": safe_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_cr": min_cr}

    except Exception as e:
        print(traceback.format_exc())
        return {"td": std,
                "collateral_volume": initial_collateral_volume_for_simulation,
                "debt_volume": initial_dept_volume_for_simulation,
                "flare_volume": initial_flare_volume_for_simulation,
                "d_l": initial_dex_liquidity_volume_for_simulation,
                "d_l_recovery": d_l_recovery,
                "safe_cr": safe_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_cr": -100}


def run_simulation(c, simulation_file_name):
    summary_report = []
    for r in itertools.product(c["std"], c["collateral_volume"], c["debt_volume"], c["flare_volume"],
                               c["d_l"], c["d_l_recovery"], c["min_cr"], c["safe_cr"], c["usd_collateral_ratio"]):
        print(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8])
        report = run_single_simulation(simulation_file_name, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8])
        summary_report.append(report)
    pd.DataFrame(summary_report).to_csv("summary.csv")


ETH_PRICE = 1600
initial_dept_volume = 100_000_000
c = {
    "std": [0.7],
    "debt_volume": [initial_dept_volume],
    "collateral_volume": [initial_dept_volume * 1.2, initial_dept_volume * 1.3, initial_dept_volume * 1.4,
                          initial_dept_volume * 1.5],
    "flare_volume": [0],
    "d_l": [initial_dept_volume * 0.01, initial_dept_volume * 0.02,
            initial_dept_volume * 0.03, initial_dept_volume * 0.04,
            initial_dept_volume * 0.05, initial_dept_volume * 0.06,
            initial_dept_volume * 0.07, initial_dept_volume * 0.08,
            initial_dept_volume * 0.09, initial_dept_volume * 0.10],
    "d_l_recovery": [30, 60, 120],
    "min_cr": [1.2],
    "safe_cr": [1.4],
    "usd_collateral_ratio": [0.7, 0.8, 0.9, 1]}

SITE_ID = "2023-5-9-12-60"
simulation_file_name = "c:\\dev\\monitor-backend_for_badger\\simulations\\data_worst_day\\data_unified_2020_03_ETHUSDT.csv"
run_simulation(c, simulation_file_name)
utils.publish_results("flare\\" + SITE_ID)
