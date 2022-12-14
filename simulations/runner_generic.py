import stability_report
import copy


def run_simulation(name, file_name, config):
    sr = stability_report.stability_report()
    sr.ETH_PRICE = ETH_PRICE
    sr.run_simulation(output_folder, file_name, name, config, print_time_series, liquidation_df, skip, calc_pnl)


ETH_PRICE = 1600
c = {
    "series_std_ratio": 1,
    'volume_for_slippage_10_percentss': [],
    'trade_every': 1800,
    "collaterals": [],
    'liquidation_incentives': [0.1],
    "stability_pool_initial_balances": [0],
    'share_institutionals': [0],
    'recovery_halflife_retails': [0],
    "price_recovery_times": [0],
    "l_factors": [0.25, 0.5, 1, 1.5, 2],
    "collateral_factor": 0
}
output_folder = "results\\sim1"
print_time_series = True
liquidation_df = None
skip = False
calc_pnl = False

runs = [{"name": "XXX-YYY1", "series_std_ratio": 1.5,
         "volume_for_slippage_10_percentss": [100_000 / ETH_PRICE, 1_000_000 / ETH_PRICE],
         "collaterals": [5_000_000 / ETH_PRICE, 50_000_000 / ETH_PRICE]},
        {"name": "XXX-YYY2", "series_std_ratio": 1,
         "volume_for_slippage_10_percentss": [100_000 / ETH_PRICE, 1_000_000 / ETH_PRICE],
         "collaterals": [5_000_000 / ETH_PRICE, 50_000_000 / ETH_PRICE]},
        {"name": "XXX-YYY3", "series_std_ratio": 0.5,
         "volume_for_slippage_10_percentss": [100_000 / ETH_PRICE, 1_000_000 / ETH_PRICE],
         "collaterals": [5_000_000 / ETH_PRICE, 50_000_000 / ETH_PRICE]}
        ]

assets = ["ADA","COPI","WRT","Min","MELD","iUSD","INDY","HOSKY","C3"]

for run in runs:
    config = copy.deepcopy(c)
    for key in run:
        config[key] = run[key]
    name = run["name"]
    # run_simulation(name, "data_worst\\data_unified_2020_01_ETHUSDT.csv", config)
    # run_simulation(name, "data_worst\\data_unified_2021_02_ETHUSDT.csv", config)
    run_simulation(name, "data_worst\\data_unified_2020_03_ETHUSDT.csv", config)
    sr = stability_report.stability_report()
    sr.ETH_PRICE = ETH_PRICE
    sr.plot_for_html(output_folder, name, print_time_series, 0)
