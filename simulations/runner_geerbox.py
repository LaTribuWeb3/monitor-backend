import compound_parser
import base_runner
import copy
import kyber_prices
import json

lending_platform_json_file = "C:\dev\monitor-backend\gearbox\data.json"

if __name__ == '__main__':
    # while True:
    file = open(lending_platform_json_file)
    data = json.load(file)

    cp_parser = compound_parser.CompoundParser()
    users_data, assets_liquidation_data, \
    last_update_time, names, inv_names, decimals, collateral_factors, borrow_caps, collateral_caps, prices, \
    underlying, inv_underlying, liquidation_incentive, orig_user_data, totalAssetCollateral, totalAssetBorrow = cp_parser.parse(
        data, False)

    for p in prices:
        print(names[p], prices[p])

