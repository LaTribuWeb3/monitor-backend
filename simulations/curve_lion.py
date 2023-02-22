import matplotlib.pyplot as plt
import random
random.seed(3)

class curve_lion:

    def __init__(self, A, ebtc_balance, wbtc_balance, liquidation_incentive, eth_volume_for_slippage, eth_slippage, recovery_halflife):
        self.A = A
        self.initail_ebtc_balance = ebtc_balance
        self.initial_wbtc_balance = wbtc_balance
        self.ebtc_balance = ebtc_balance
        self.wbtc_balance = wbtc_balance
        self.ebtc_index = 0
        self.wbtc_index = 1
        self.liquidation_incentive = liquidation_incentive
        self.recovery_halflife = recovery_halflife
        self.eth_volume_for_slippage = eth_volume_for_slippage
        self.eth_slippage = eth_slippage

    def get_y(self, i, j, x, _xp, N_COINS, A):
        # x in the input is converted to the same price/precision
        assert (i != j) and (i >= 0) and (j >= 0) and (i < N_COINS) and (j < N_COINS)

        D = self.get_D(_xp, N_COINS, A)
        c = D
        S_ = 0
        Ann = A * N_COINS

        _x = 0
        for _i in range(N_COINS):
            if _i == i:
                _x = x
            elif _i != j:
                _x = _xp[_i]
            else:
                continue
            S_ += _x
            c = c * D / (_x * N_COINS)
        c = c * D / (Ann * N_COINS)
        b = S_ + D / Ann  # - D
        y_prev = 0
        y = D
        for _i in range(255):
            y_prev = y
            y = (y * y + c) / (2 * y + b - D)
            # Equality with the precision of 1
            if y > y_prev:
                if y - y_prev <= 1:
                    break
            else:
                if y_prev - y <= 1:
                    break

        return _xp[j] - y

    def do_tick(self):

        missing_wbtc_balance = self.wbtc_balance - self.initial_wbtc_balance
        next_missing_wbtc_balance = missing_wbtc_balance * pow(0.5, 1 / (self.recovery_halflife * 24 * 60))
        current_recovery_volume_retail = missing_wbtc_balance - next_missing_wbtc_balance
        recovery_volume_wbtc = min(current_recovery_volume_retail, missing_wbtc_balance)

        # get return
        self.ebtc_balance += self.get_return(self.wbtc_index,self.ebtc_index, recovery_volume_wbtc,
                                             [self.ebtc_balance, self.wbtc_balance])
        self.wbtc_balance -= recovery_volume_wbtc

    def get_return(self, i, j, x, balances):
        return self.get_y(i, j, x + balances[i], balances, len(balances), self.A)

    def get_D(self, xp, N_COINS, A):
        S = 0
        for _x in xp:
            S += _x
        if S == 0:
            return 0

        Dprev = 0
        D = S
        Ann = A * N_COINS
        for _i in range(255):
            D_P = D
            for _x in xp:
                D_P = D_P * D / (_x * N_COINS + 1)  # +1 is to prevent /0
            Dprev = D
            D = (Ann * S + D_P * N_COINS) * D / ((Ann - 1) * D + (N_COINS + 1) * D_P)
            # Equality with the precision of 1
            if D > Dprev:
                if D - Dprev <= 1:
                    break
            else:
                if Dprev - D <= 1:
                    break
        return D

    def get_price(self, ebtc_balance, wbtc_balance):
        qty = 1e8
        # wbtc => ebtc
        return qty / self.get_return(self.wbtc_index, self.ebtc_index, qty, [ebtc_balance, wbtc_balance])

    def get_buy_sell_qty(self, liquidation_size_in_ebtc, update_balance):
        max_price = 1 + self.liquidation_incentive
        upper_bound = liquidation_size_in_ebtc * 2
        lower_bound = 0
        wbtc_sell_qty = 0
        ebtc_return_qty = 0
        while (upper_bound - lower_bound > 2):
            wbtc_sell_qty = (upper_bound + lower_bound) / 2
            ebtc_return_qty = self.get_return(self.wbtc_index, self.ebtc_index, wbtc_sell_qty,
                                              [self.ebtc_balance, self.wbtc_balance])
            new_price = self.get_price(self.ebtc_balance - ebtc_return_qty, self.wbtc_balance + wbtc_sell_qty)
            # adjust to slippage
            effective_slippage = self.eth_slippage * wbtc_sell_qty / self.eth_volume_for_slippage
            new_price = new_price * (1 + effective_slippage)

            if (new_price > max_price) or (ebtc_return_qty > liquidation_size_in_ebtc):
                upper_bound = (wbtc_sell_qty + upper_bound) / 2
            else:
                lower_bound = (wbtc_sell_qty + lower_bound) / 2
            #print(new_price, upper_bound / 1e14, lower_bound / 1e14, wbtc_sell_qty / 1e14, "M", effective_slippage)

        if update_balance:
            self.wbtc_balance += wbtc_sell_qty
            self.ebtc_balance -= ebtc_return_qty
        return ebtc_return_qty


A = 200
initial_balance = 1_000_000e8
liquidation_incentive = 0.1
slippage_for_volume = (100000e8, 0.1)
trade_volume = 100_000e8
recovery_halflife = 1

cl = curve_lion(200, initial_balance, initial_balance, liquidation_incentive, slippage_for_volume[0],
                slippage_for_volume[1], recovery_halflife)

#cl.get_buy_sell_qty(trade_volume / 3, True)
x = []
y = []

for i in range(24 * 60 * 10 * 10):
    cl.do_tick()
    price = cl.get_price(cl.ebtc_balance, cl.wbtc_balance)
    x.append(i)
    y.append(price)
    if i % random.randint(900, 1100) == 0:
        qty = ((i * 7) % 77) * trade_volume
        cl.get_buy_sell_qty(qty, True)

plt.plot(x, y)
plt.show()