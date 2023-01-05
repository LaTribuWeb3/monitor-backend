import json

class AggregatorPrices:
    def __init__(self, file_name, inv_names, underlying, inv_underlying, decimals, allTokens):
        file_name = file_name
        file = open(file_name)
        self.liquidityJson = json.load(file)
        self.underlying = underlying
        self.decimals = decimals
        self.inv_names = inv_names
        self.inv_underlying = inv_underlying
        self.all_tokens = allTokens
        self.pCKB = "0x7538C85caE4E4673253fFd2568c1F1b48A71558a"
        self.WCKB = "0xC296F806D15e97243A08334256C705bA5C5754CD"

    def calcDestQty(self, dx, x, y):
        # (x + dx) * (y-dy) = xy
        # dy = y - xy/(x+dx)
        z = x * y / (x + dx)  # toBN(x).mul(toBN(y)).div(toBN(x).add(toBN(dx)))
        return y - z  # toBN(y).sub(z)

    def arrayRemove(self, arr, value):
        return arr.remove(value)

    def get_price(self, srcToken, destToken, srcQty):
        # srcToken = srcToken if srcToken !=  "USDT" else "USDC"
        # destToken = destToken if destToken != "USDT" else "USDC"

        srcQty1 = srcQty
        srcToken = self.underlying[self.inv_names[srcToken]]
        destToken = self.underlying[self.inv_names[destToken]]
        if destToken == self.pCKB:
            destToken = self.WCKB
        srcQty = srcQty * 10 ** self.decimals[srcToken]
        if srcToken == self.pCKB:
            srcToken = self.WCKB

        bestDestQty = self.get_price_defi(srcToken, destToken, srcQty, self.all_tokens)
        if destToken == self.WCKB:
            destToken = self.pCKB

        bestDestQty /= 10 ** self.decimals[self.inv_underlying[destToken]]
        price = 0 if bestDestQty == 0 else srcQty1 / bestDestQty
        return price

    def get_price_defi(self, srcToken, destToken, srcQty, allTokens):
        if srcToken == destToken:
            return srcQty
        if len(allTokens) == 0:
            return 0

        bestDestQty = 0
        for token in allTokens:
            key = str(srcToken) + "_" + str(token)
            if not key in self.liquidityJson:
                continue

            x = self.liquidityJson[key]["token0"]
            y = self.liquidityJson[key]["token1"]

            dy = self.calcDestQty(int(srcQty), float(x), float(y))

            newSrcToken = token
            newSrcQty = dy
            newAllToken = allTokens.copy()
            newAllToken.remove(token)

            bestCandidate = self.get_price_defi(newSrcToken, destToken, newSrcQty, newAllToken)
            if bestCandidate > bestDestQty:
                bestDestQty = bestCandidate

        return bestDestQty

