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
print_time_series = False
liquidation_df = None
skip = False
calc_pnl = False


runs = [{"name": "NEARX-USDC", "series_std_ratio": 1.74, "volume_for_slippage_10_percentss": [14_000 / ETH_PRICE],
         "collaterals": [1100_000 / ETH_PRICE, 1200_000 / ETH_PRICE, 1300_000 / ETH_PRICE, 1400_000 / ETH_PRICE, 1500_000 / ETH_PRICE,
                         600_000 / ETH_PRICE, 700_000 / ETH_PRICE, 800_000 / ETH_PRICE, 900_000 / ETH_PRICE, 1000_000 / ETH_PRICE]},
        {"name": "NEARX-ETH", "series_std_ratio": 1.18, "volume_for_slippage_10_percentss": [14_000 / ETH_PRICE],
         "collaterals": [1100_000 / ETH_PRICE, 1200_000 / ETH_PRICE, 1300_000 / ETH_PRICE, 1400_000 / ETH_PRICE, 1500_000 / ETH_PRICE,
                         600_000 / ETH_PRICE, 700_000 / ETH_PRICE, 800_000 / ETH_PRICE, 900_000 / ETH_PRICE, 1000_000 / ETH_PRICE]},
        {"name": "NEARX-WBTC", "series_std_ratio": 1.27, "volume_for_slippage_10_percentss": [14_000 / ETH_PRICE],
         "collaterals": [1100_000 / ETH_PRICE, 1200_000 / ETH_PRICE, 1300_000 / ETH_PRICE, 1400_000 / ETH_PRICE, 1500_000 / ETH_PRICE,
                         600_000 / ETH_PRICE, 700_000 / ETH_PRICE, 800_000 / ETH_PRICE, 900_000 / ETH_PRICE, 1000_000 / ETH_PRICE]}]

for run in runs:
    config = copy.deepcopy(c)
    for key in run:
        config[key] = run[key]
    name = run["name"]
    run_simulation(name, "data_worst\\data_unified_2020_01_ETHUSDT.csv", config)
    run_simulation(name, "data_worst\\data_unified_2021_02_ETHUSDT.csv", config)
    run_simulation(name, "data_worst\\data_unified_2020_03_ETHUSDT.csv", config)
    sr = stability_report.stability_report()
    sr.ETH_PRICE = ETH_PRICE
    sr.plot_for_html(output_folder, name, print_time_series, 0)

