import ccxt


class CCXTClient:

    def __init__(self):
        pass

    def get_price(self, exchange, base, quote):
        if base == "WBTC":
            base = "BTC"
        if base == "WNEAR" or base == "STNEAR":
            base = "NEAR"

        client = getattr(ccxt, exchange)()
        ob = client.fetch_order_book(base + "/" + quote)
        return (ob["bids"][0][0] + ob["asks"][0][0]) * 0.5

