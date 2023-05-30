import itertools
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import copy
import utils
import unibox
import traceback


def usd_liquidation_size_with_flare(safe_ratio, curr_price, usd_collateral, btc_debt, liquidation_bonus,
                                    usd_liquidation_ratio, flare_collateral, flare_price, flare_safe_ratio):
    usd_curr_ratio = usd_collateral / (btc_debt * curr_price)
    flare_curr_ratio = flare_collateral * flare_price / (btc_debt * curr_price)
    # print("xxx", curr_ratio)

    usd_ratio = usd_liquidation_ratio
    if usd_ratio > usd_curr_ratio:
        usd_ratio = usd_curr_ratio

    flare_ratio = 1 + liquidation_bonus - usd_ratio
    if flare_ratio > flare_curr_ratio:
        flare_ratio = flare_curr_ratio
        usd_ratio = min(1 + liquidation_bonus - flare_ratio, usd_curr_ratio)

    # print(flare_ratio, flare_curr_ratio)

    burned_btc_1 = min(btc_debt * (safe_ratio - usd_curr_ratio) / (safe_ratio - (1 + liquidation_bonus)), btc_debt)
    burned_btc_2 = min(btc_debt * (flare_safe_ratio - flare_curr_ratio) / (flare_safe_ratio - (1 + liquidation_bonus)),
                       btc_debt)
    burned_btc = max(burned_btc_1, burned_btc_2)

    usd_liquidation_size = burned_btc * usd_ratio * curr_price
    flare_liquidation_size = burned_btc * curr_price * flare_ratio / flare_price

    return {"usd_liquidation": usd_liquidation_size, "burned_btc": burned_btc,
            "flare_liquidation": flare_liquidation_size}


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
                    "btc_usd_price": (1 / row["btc_usd_price"]),
                    "flare_btc_price": row["flare_btc_price"],
                    "flare_usd_price": row["flare_btc_price"] * (1 / row["btc_usd_price"])})
    return arr


def crete_price_trajectory(data, btc_std, flare_std):
    data1 = adjust_series_price(copy.deepcopy(data), btc_std)
    data1["btc_usd_price"] = data1["adjust_price"]
    data2 = adjust_series_price(copy.deepcopy(data), flare_std)
    data1["flare_btc_price"] = data2["adjust_price"]

    dai_eth_array = convert_to_array(data1)
    return dai_eth_array


def create_liquidation_df(collateral_volume, debt_volume, min_cr):
    return pd.DataFrame()


def run_single_simulation(date_file_name,
                          btc_usd_std, flr_btc_std,
                          debt_volume, min_usd_cr, safe_usd_cr, usd_collateral_ratio,
                          usd_dl_x, flr_dl_x,
                          flr_dl_recovery, usd_dl_recovery,
                          min_flare_cr, safe_flare_cr):

    initial_usd_dl_x =  usd_dl_x
    initial_flr_dl_x = flr_dl_x
    initial_safe_flare_cr = safe_flare_cr
    initial_safe_usd_cr = safe_usd_cr

    safe_flare_cr += min_flare_cr
    safe_usd_cr += min_usd_cr
    usd_dl_x *= debt_volume
    flr_dl_x *= debt_volume
    flr_collateral_volume = safe_flare_cr * debt_volume
    usd_collateral_volume = safe_usd_cr * debt_volume

    uni_box = unibox.unibox(usd_dl_x, flr_dl_x)


    liquidation_incentive = 0.1
    initial_debt_volume_for_simulation = debt_volume
    initial_flr_collateral_volume_for_simulation = flr_collateral_volume
    initial_usd_collateral_volume_for_simulation = usd_collateral_volume
    min_usd_ucr = float('inf')
    min_flr_ucr = float('inf')

    try:
        flr_liquidation_table = []
        usd_liquidation_table = []
        time_series_report = []
        data = pd.read_csv(date_file_name)
        file = crete_price_trajectory(data, btc_usd_std, flr_btc_std)
        state = 0
        debt_volume /= file[0]["btc_usd_price"]
        flr_collateral_volume /= file[0]["flare_usd_price"]
        initial_adjust_dept_volume_for_simulation = debt_volume
        total_liquidations = 0
        total_flare_liquidation = 0
        total_usd_liquidation = 0
        for row in file:
            row_btc_usd_price = row["btc_usd_price"]
            row_flare_btc_price = row["flare_btc_price"]
            row_flare_usd_price = row["flare_usd_price"]
            uni_box.update_prices(row_flare_usd_price, row_btc_usd_price)
            while len(flr_liquidation_table) > flr_dl_recovery:
                first_flr_liquidation_table = flr_liquidation_table.pop(0)
                #print("FLARE", first_flr_liquidation_table)
                uni_box.recover_flare_liquidity(first_flr_liquidation_table)

            # recover usd_x_y
            while len(usd_liquidation_table) > usd_dl_recovery:
                first_usd_liquidation_table = usd_liquidation_table.pop(0)
                #print("USD", first_usd_liquidation_table)
                uni_box.recover_usd_liquidity(first_usd_liquidation_table)

            usd_ucr = usd_collateral_volume / (debt_volume * row_btc_usd_price)
            flr_ucr = (flr_collateral_volume * row_flare_usd_price) / (debt_volume * row_btc_usd_price)

            min_usd_ucr = min(min_usd_ucr, usd_ucr)
            min_flr_ucr = min(min_flr_ucr, flr_ucr)
            open_liquidation = 0

            if (usd_ucr <= min_usd_cr
                    or flr_ucr <= min_flare_cr
                    or (state == 1 and (usd_ucr <= safe_usd_cr or flr_ucr <= safe_flare_cr))):
                state = 1
                # print(safe_usd_cr, row_btc_usd_price, usd_collateral_volume, debt_volume,
                #       liquidation_incentive,
                #       usd_collateral_ratio, flr_collateral_volume,
                #       row_flare_usd_price, safe_flare_cr)

                l_size = usd_liquidation_size_with_flare(safe_usd_cr, row_btc_usd_price, usd_collateral_volume,
                                                         debt_volume,
                                                         liquidation_incentive,
                                                         usd_collateral_ratio, flr_collateral_volume,
                                                         row_flare_usd_price, safe_flare_cr)
                # print(l_size)

                burned_btc_volume = l_size["burned_btc"]
                usd_liquidation_volume = l_size["usd_liquidation"]
                flr_liquidation_volume = l_size["flare_liquidation"]
                open_liquidation = burned_btc_volume
                # print(burned_btc_volume, flr_liquidation_volume, usd_liquidation_volume)
                obj = uni_box.find_btc_liquidation_size(burned_btc_volume, flr_liquidation_volume,
                                                        usd_liquidation_volume)
                usd_liquidation_volume = obj["usd"]
                flr_liquidation_volume = obj["flare"]
                burned_btc_volume = obj["btc"]

                btc_returned1 = uni_box.dump_usd_to_btc(usd_liquidation_volume)
                usd_liquidation_table.append(btc_returned1)
                btc_returned2 = uni_box.dump_flare_to_btc(flr_liquidation_volume)
                flr_liquidation_table.append(btc_returned2)
                # print(btc_returned1, btc_returned2)

                if burned_btc_volume > debt_volume:
                    print(burned_btc_volume, debt_volume)
                    print("XXXX")
                    exit()

                usd_collateral_volume -= usd_liquidation_volume
                flr_collateral_volume -= flr_liquidation_volume
                total_liquidations += burned_btc_volume
                total_flare_liquidation += flr_liquidation_volume
                total_usd_liquidation += usd_liquidation_volume

                debt_volume -= burned_btc_volume
            else:
                flr_liquidation_table.append(0)
                usd_liquidation_table.append(0)

                state = 0
            uni_usd = uni_box.get_usd_xy()
            uni_flare = uni_box.get_flare_xy()
            report_row = {"simulation_file_name": simulation_file_name,
                          "timestamp": row["timestamp_x"],
                          "simulation_initial_debt_volume": initial_adjust_dept_volume_for_simulation,
                          "btc_usd_price": row_btc_usd_price,
                          "flare_btc_price": row_flare_btc_price,
                          "flare_usd_price": row_flare_usd_price,
                          "debt_volume": debt_volume,
                          "usd_collateral_volume": usd_collateral_volume,
                          "flare_collateral_volume": flr_collateral_volume,
                          "uniswap_btc_usd_price_deviation": (uni_usd["usd"] / uni_usd["btc"]) - 1,
                          "uniswap_flare_btc_price_deviation": (uni_flare["flare"] / uni_flare["btc"]) - 1,
                          "total_flare_liquidation": total_flare_liquidation,
                          "total_usd_liquidation": total_usd_liquidation,
                          "total_liquidations": total_liquidations,
                          "open_liquidation": open_liquidation,
                          "usd_ucr": usd_ucr,
                          "flare_ucr": flr_ucr,
                          "min_flare_ucr": min_flr_ucr,
                          "min_usd_ucr": min_usd_ucr}

            time_series_report.append(report_row)

        time_series_report_name = f"webserver\\flare\\" + SITE_ID + "\\" \
                                                                    f"BtcStd-{btc_usd_std}+" \
                                                                    f"FlrStd-{flr_btc_std}+" \
                                                                    f"MinUsdCr-{min_usd_cr}+" \
                                                                    f"SafeUsdCr-{intial_safe_usd_cr}+" \
                                                                    f"MinFlrCr-{min_flare_cr}+" \
                                                                    f"SafeFlrCr-{intial_safe_flare_cr}+" \
                                                                    f"UsdCr-{usd_collateral_ratio}+" \
                                                                    f"UsdDlX-{initial_usd_dl_x}+" \
                                                                    f"UsdRec-{usd_dl_recovery}+" \
                                                                    f"FlrDlX-{initial_flr_dl_x}+" \
                                                                    f"FlrRec-{flr_dl_recovery}"

        report_df = pd.DataFrame(time_series_report)
        #report_df.to_csv(time_series_report_name + ".csv")
        plt.cla()
        plt.close()
        fig, ax1 = plt.subplots()
        fig.set_size_inches(12.5, 8.5)
        ax2 = ax1.twinx()

        plt.suptitle("Min USD CR: " + str(round(min_usd_ucr, 2)))
        plt.title("Min Flare CR: " + str(round(min_flr_ucr, 2)))
        x1 = ax1.plot(report_df["timestamp"], report_df["btc_usd_price"] / report_df["btc_usd_price"].max(), 'b-',
                      label="Btc Usd Price")
        x2 = ax1.plot(report_df["timestamp"], report_df["flare_btc_price"] / report_df["flare_btc_price"].max(), 'g-',
                      label="Flare Btc Price")
        x3 = ax2.plot(report_df["timestamp"], report_df["usd_ucr"], 'r-', label="Usd CR")
        x4 = ax2.plot(report_df["timestamp"], report_df["flare_ucr"], 'c-', label="Flare CR")
        x5 = ax2.plot(report_df["timestamp"], report_df["debt_volume"] / report_df["simulation_initial_debt_volume"],
                      'm-', label="DebtVolume")
        x6 = ax2.plot(report_df["timestamp"],
                      report_df["usd_collateral_volume"] / pow(report_df["simulation_initial_debt_volume"], 2), 'y-',
                      label="UsdCollateralVolume")
        x7 = ax2.plot(report_df["timestamp"],
                      report_df["flare_collateral_volume"] / pow(report_df["simulation_initial_debt_volume"], 2), 'b-',
                      label="FlareCollateralVolume")
        x8 = ax2.plot(report_df["timestamp"],
                      report_df["open_liquidation"] / report_df["simulation_initial_debt_volume"],
                      label="OpenLiquidations")
        x9 = ax2.plot(report_df["timestamp"],
                      report_df["total_liquidations"] / report_df["simulation_initial_debt_volume"],
                      label="TotalLiquidations")

        lns = x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        plt.savefig(time_series_report_name + ".jpg")
        # print("min usd ucr", min_usd_ucr)
        # print("min flare ucr", min_flr_ucr)

    except Exception as e:
        min_usd_ucr = -100
        min_flare_ucr = -100
        print(traceback.format_exc())
        print("Exception!!!!!")
        exit()

    finally:
        return {"btc_usd_std": btc_usd_std,
                "flr_btc_std": flr_btc_std,
                "debt_volume": initial_debt_volume_for_simulation,
                "usd_collateral_volume": initial_usd_collateral_volume_for_simulation,
                "flare_collateral_volume": initial_flr_collateral_volume_for_simulation,
                "usd_dl_x": initial_usd_dl_x,
                "usd_dl_recovery": usd_dl_recovery,
                "flare_dl_x": initial_flr_dl_x,
                "flare_dl_recovery": flr_dl_recovery,
                "min_usd_cr": safe_usd_cr,
                "min_flare_cr": safe_flare_cr,
                "safe_usd_cr": safe_usd_cr,
                "safe_flare_cr": safe_flare_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_usd_ucr": min_usd_ucr,
                "min_flare_ucr": min_flr_ucr}


def run_simulation(c, simulation_file_name):
    summary_report = []
    all = itertools.product(c["btc_usd_std"], c["flare_btc_std"],
                               c["debt_volume"], c["min_usd_cr"], c["safe_usd_cr"],
                               c["usd_collateral_ratio"], c["usd_dl_x"], c["flare_dl_x"],
                               c["usd_dl_recovery"], c["flare_dl_recovery"],
                               c["min_flare_cr"], c["safe_flare_cr"])
    myprod2 = copy.deepcopy(all)
    all_runs = len(list(myprod2))
    print("Total Runs", all_runs)
    indx = 0
    for r in all:
        #print(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11])
        report = run_single_simulation(simulation_file_name, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                                       r[8], r[9], r[10], r[11])
        summary_report.append(report)
        indx += 1
        print(indx / all_runs)
    pd.DataFrame(summary_report).to_csv("summary.csv")


ETH_PRICE = 1600
initial_dept_volume = 100_000_000
c = {
    "btc_usd_std": [0.7],
    "flare_btc_std": [0.5],
    "debt_volume": [initial_dept_volume],
    "usd_dl_x": [0.1, 0.2, 0.3],
    "usd_dl_recovery": [30, 60, 90],
    "flare_dl_x": [0.1, 0.2, 0.3],
    "flare_dl_recovery": [30, 60, 90],
    "min_usd_cr": [1.2, 1.3, 1.4],
    "safe_usd_cr": [0.2, 0.3, 0.4],
    "min_flare_cr": [1.5, 1.7, 2.0],
    "safe_flare_cr": [0.1, 0.5, 1.0],
    "usd_collateral_ratio": [1]}

SITE_ID = "2023-5-30-0-1"
simulation_file_name = "c:\\dev\\monitor-backend\\simulations\\data_worst_day\\data_unified_2020_03_ETHUSDT.csv"
run_simulation(c, simulation_file_name)
# utils.publish_results("flare\\" + SITE_ID, None, True)
