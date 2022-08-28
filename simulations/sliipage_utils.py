
def get_usd_volume_for_slippage(base, quote, slippage, asset_usdc_price, get_price_function):
    print(base, quote)

    base_price = get_price_function(base, quote, 1000 / asset_usdc_price[base])
    max_price_volume = 1000
    min_price_volume = 1000 * 1000 * 1000
    avg_slippage = 0

    while True:
        if min_price_volume - max_price_volume < 1000:
            v = (min_price_volume + max_price_volume) / 2
            print("Volume:", int(v), "Slippage", round(avg_slippage, 2))
            return v

        avg_volume = (min_price_volume + max_price_volume) / 2
        price = get_price_function(base, quote, avg_volume / asset_usdc_price[base])
        avg_slippage = price / base_price
        print("min_price_volume", round(min_price_volume), "max_price_volume", round(max_price_volume),
              "Volume", round(avg_volume), "Slippage", round(avg_slippage, 3), "Target", slippage, "Price", price)

        if avg_slippage > slippage:
            min_price_volume = avg_volume
        else:
            max_price_volume = avg_volume


def get_usd_volumes_for_slippage(chain_id, inv_names, liquidation_incentive, get_price_function, only_usdt=False):
    base = ""
    asset_usdc_price = {}

    if chain_id == "aurora":
        asset_usdc_price = {"auUSDC": 1}
    elif chain_id == "arbitrum":
        asset_usdc_price = {"VST": 1}

    for quote in inv_names:
        if chain_id == "aurora":
            if quote == "auUSDC":
                continue
            base = "auUSDC"
        elif chain_id == "arbitrum":
            if quote == "VST":
                continue
            base = "VST"
        elif chain_id == "yokaiswap":
            if quote == "USDC":
                asset_usdc_price[quote] = 1
                continue
            base = "USDC"

        price_in_base = get_price_function(base, quote, 1000)
        asset_usdc_price[quote] = price_in_base

    print(asset_usdc_price)
    all_prices = {}
    for base in inv_names:
        for quote in inv_names:
            if base == quote or quote == "VST" or (only_usdt and base != "VST"):
                continue
            if base not in all_prices:
                all_prices[base] = {}
            if not only_usdt:
                lic = float(liquidation_incentive[inv_names[base]])
            else:
                lic = float(liquidation_incentive[inv_names[quote]])
            print(base, quote)
            volume = get_usd_volume_for_slippage(base, quote, lic if lic >= 1 else 1 + lic, asset_usdc_price, get_price_function)
            all_prices[base][quote] = volume

    return all_prices
