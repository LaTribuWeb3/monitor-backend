import itertools
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import copy
import utils


def get_dy(x, y, dx):
    return y - x * y / (x + dx)


def get_dBTC(x_flare, y_flare, x_usd, y_usd, flare_in, usd_in):
    return get_dy(x_flare, y_flare, flare_in) + get_dy(x_usd, y_usd, usd_in)


def find_btc_liquidation_size(x_flare, y_flare, x_usd, y_usd, btc_in, flare_in, usd_in):
    min_btc = 0
    max_btc = btc_in
    curr_btc_in = max_btc  # be optimistic
    while True:
        curr_flare_in = flare_in * curr_btc_in / btc_in
        curr_usd_in = usd_in * curr_btc_in / btc_in

        out_btc = get_dBTC(x_flare, y_flare, x_usd, y_usd, curr_flare_in, curr_usd_in)
        if out_btc < curr_btc_in:
            max_btc = curr_btc_in
        else:
            min_btc = curr_btc_in

        if min_btc > 0 and (max_btc / min_btc < 1.01):
            obj = {"btc": min_btc, "usd": usd_in * min_btc / btc_in, "flare": flare_in * min_btc / btc_in}

            # print(get_dBTC(x_flare, y_flare, x_usd, y_usd, obj["flare"], obj["usd"]))
            return obj

        curr_btc_in = (min_btc + max_btc) / 2


def usd_liquidation_size_with_flare(safe_ratio, curr_price, usd_collateral, btc_debt, liquidation_bonus,
                                    usd_liquidation_ratio, flare_collateral, flare_price):
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

    burned_btc = min(btc_debt * (safe_ratio - usd_curr_ratio) / (safe_ratio - (1 + liquidation_bonus)), btc_debt)
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
                          min_cr, safe_cr, usd_collateral_ratio,
                          usd_dl_x, usd_dl_y, flr_dl_x, flr_dl_y,
                          flr_dl_recovery, usd_dl_recovery):
    liquidation_incentive = 0.1
    initial_debt_volume_for_simulation = debt_volume
    initial_flr_collateral_volume_for_simulation = flr_collateral_volume
    initial_usd_collateral_volume_for_simulation = usd_collateral_volume
    initial_usd_dl_x = usd_dl_x
    initial_usd_dl_y = usd_dl_y
    initial_flr_dl_x = flr_dl_x
    initial_flr_dl_y = flr_dl_y

    try:
        flr_liquidation_table = []
        usd_liquidation_table = []
        time_series_report = []
        data = pd.read_csv(date_file_name)
        file = crete_price_trajectory(data, usd_std, flr_std)

        state = 0
        min_ucr = float('inf')
        debt_volume /= file[0]["usd_price"]
        initial_adjust_dept_volume_for_simulation = debt_volume
        total_liquidations = 0
        for row in file:

            # recover flare_x_y
            while len(flr_liquidation_table) > flr_dl_recovery:
                first_flr_liquidation_table = flr_liquidation_table.pop(0)
                if first_flr_liquidation_table > 0:
                    flr_from_pump = get_dy(flr_dl_y, flr_dl_x, first_flr_liquidation_table)
                    flr_dl_x -= flr_from_pump
                    flr_dl_y += first_flr_liquidation_table

            # recover usd_x_y
            while len(usd_liquidation_table) > usd_dl_recovery:
                first_usd_liquidation_table = usd_liquidation_table.pop(0)
                usd_from_pump = get_dy(usd_dl_y, usd_dl_x, first_usd_liquidation_table)
                usd_dl_x -= usd_from_pump
                usd_dl_y += first_usd_liquidation_table

            row_btc_usd_price = row["usd_price"]
            row_flr_btc_price = row["flare_price"]
            row_flr_usd_price = row_flr_btc_price * row_btc_usd_price
            ONE = 1
            ucr = usd_collateral_volume / (debt_volume * row_btc_usd_price)
            min_ucr = min(min_ucr, ucr)
            open_liquidation = 0
            burned_btc_volume = 0
            if ucr <= min_cr or (state == 1 and ucr <= safe_cr):
                state = 1
                l_size = usd_liquidation_size_with_flare(safe_cr, row_btc_usd_price, usd_collateral_volume, debt_volume,
                                                         liquidation_incentive,
                                                         usd_collateral_ratio, flr_collateral_volume, row_flr_usd_price)
                burned_btc_volume = l_size["burned_btc"]
                usd_liquidation_volume = l_size["usd_liquidation"]
                flr_liquidation_volume = l_size["flr_liquidation"]

                obj = find_btc_liquidation_size(flr_dl_x / row_flr_usd_price, flr_dl_y / row_btc_usd_price,
                                                usd_dl_x / ONE, usd_dl_y / row_btc_usd_price,
                                                burned_btc_volume, flr_liquidation_volume, usd_liquidation_volume)

                usd_liquidation_volume = obj["usd"]
                flr_liquidation_volume = obj["flare"]
                burned_btc_volume = obj["btc"]
                btc_from_flr_dump = get_dy(flr_dl_x, flr_dl_y, flr_liquidation_volume / row_flr_usd_price)
                btc_from_usd_dump = get_dy(usd_dl_x, usd_dl_y, usd_liquidation_volume / ONE)

                flr_liquidation_table.append(btc_from_flr_dump)
                usd_liquidation_table.append(btc_from_usd_dump)

                if burned_btc_volume > debt_volume:
                    print(safe_cr, row_btc_usd_price, usd_liquidation_volume, debt_volume, 0.1, usd_collateral_ratio)
                    print(burned_btc_volume, debt_volume)
                    print("XXXX")
                    exit()

                flr_dl_x += flr_liquidation_volume
                flr_dl_y -= btc_from_flr_dump

                usd_dl_x += usd_liquidation_volume
                usd_dl_y -= btc_from_usd_dump

                usd_collateral_volume -= usd_liquidation_volume
                flr_collateral_volume -= flr_liquidation_volume
                total_liquidations += burned_btc_volume
                debt_volume -= burned_btc_volume

            else:
                flr_liquidation_table.append(0)
                usd_liquidation_table.append(0)

                state = 0

            report_row = {"simulation_file_name": simulation_file_name,
                          "timestamp": row["timestamp_x"],
                          "simulation_initial_debt_volume": initial_adjust_dept_volume_for_simulation,
                          "usd_price": row_btc_usd_price,
                          "flare_price": row_flr_usd_price,
                          "debt_volume": debt_volume,
                          "usd_collateral_volume": usd_collateral_volume,
                          "flare_collateral_volume": flr_collateral_volume,
                          "flare_dl_x": flr_dl_x,
                          "flare_dl_y": flr_dl_y,
                          "usd_dl_x": usd_dl_x,
                          "usd_dl_y": usd_dl_y,
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
                                                                    f"UsdDlX-{initial_usd_dl_x}+" \
                                                                    f"UsdDlY-{initial_usd_dl_y}+" \
                                                                    f"UsdDlRecovery-{usd_dl_recovery}+" \
                                                                    f"FlareDlX-{initial_flr_dl_x}+" \
                                                                    f"FlareDlY-{initial_flr_dl_y}+" \
                                                                    f"FlareDlRecovery-{flr_dl_recovery}" \
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
        x6 = ax2.plot(report_df["timestamp"],
                      report_df["open_liquidation"] / report_df["simulation_initial_debt_volume"],
                      label="OpenLiquidations")
        x7 = ax2.plot(report_df["timestamp"],
                      report_df["total_liquidations"] / report_df["simulation_initial_debt_volume"],
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
                "usd_dl_x": initial_usd_dl_x,
                "usd_dl_y": initial_usd_dl_y,
                "usd_dl_recovery": usd_dl_recovery,
                "flare_dl_x": initial_flr_dl_x,
                "flare_dl_y": initial_flr_dl_y,
                "flare_dl_recovery": flr_dl_recovery,
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
                "usd_dl_x": initial_usd_dl_x,
                "usd_dl_y": initial_usd_dl_y,
                "usd_dl_recovery": usd_dl_recovery,
                "flare_dl_x": initial_flr_dl_x,
                "flare_dl_y": initial_flr_dl_y,
                "flare_dl_recovery": flr_dl_recovery,
                "safe_cr": safe_cr,
                "usd_collateral_ratio": usd_collateral_ratio,
                "min_cr": -100}


def run_simulation(c, simulation_file_name):
    summary_report = []
    for r in itertools.product(c["usd_std"], c["flare_std"],
                               c["debt_volume"], c["usd_volume"], c["flare_volume"],
                               c["usd_d_l"], c["usd_d_l_recovery"],
                               c["flare_d_l"], c["flare_d_l_recovery"],
                               c["min_cr"], c["safe_cr"], c["usd_collateral_ratio"],
                               c["usd_dl_x"], c["usd_dl_y"],
                               c["flare_dl_x"], c["flare_dl_y"],
                               c["usd_dl_recovery"], c["flare_dl_recovery"]):
        print(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13])
        report = run_single_simulation(simulation_file_name, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                                       r[8], r[9], r[10], r[11], r[12], r[13])
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

    "usd_dl_x": [1000],
    "usd_dl_y": [1000],
    "usd_dl_recovery": [30],
    "flare_dl_x": [1000],
    "flare_dl_y": [1000],
    "flare_dl_recovery": [30],

    "flare_d_l_recovery": [30, 60, 120],
    "min_cr": [1.2],
    "safe_cr": [1.4],
    "usd_collateral_ratio": [0.7, 0.8, 0.9, 1]}

SITE_ID = "2023-5-9-12-60"
simulation_file_name = "c:\\dev\\monitor-backend_for_badger\\simulations\\data_worst_day\\data_unified_2020_03_ETHUSDT.csv"
run_simulation(c, simulation_file_name)
utils.publish_results("flare\\" + SITE_ID)
