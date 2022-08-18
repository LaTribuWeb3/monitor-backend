import json

def calcDestQty(dx, x, y):
    # (x + dx) * (y-dy) = xy
    # dy = y - xy/(x+dx)

    z = x*y/(x+dx) # toBN(x).mul(toBN(y)).div(toBN(x).add(toBN(dx)))

    return y - z # toBN(y).sub(z)

def arrayRemove(arr, value):
    return arr.remove(value)


def findBestDestQty(srcToken, srcQty, destToken, allTokens, liquidityJson):
    if srcToken ==  destToken:
        return srcQty
    if len(allTokens) == 0:
        return 0


    bestDestQty = 0
    for token in allTokens:
        key = str(srcToken) + "_" + str(token)
        if not key in liquidityJson:
            continue

        x = liquidityJson[key]["token0"]
        y = liquidityJson[key]["token1"]

        dy = calcDestQty(int(srcQty), float(x), float(y))

        newSrcToken = token
        newSrcQty = dy
        newAllToken = allTokens.copy()
        newAllToken.remove(token)

        bestCandidate = findBestDestQty(newSrcToken, newSrcQty, destToken, newAllToken, liquidityJson)
        print(srcToken, key, str(bestCandidate))
        if bestCandidate > bestDestQty:
            bestDestQty = bestCandidate

    return bestDestQty

ETH = "0x9E858A7aAEDf9FDB1026Ab1f77f627be2791e98A"
BNB = "0xBAdb9b25150Ee75bb794198658A4D0448e43E528"
USDC = "0x186181e225dc1Ad85a4A94164232bD261e351C33"
WCKB = "0xC296F806D15e97243A08334256C705bA5C5754CD"
USDT = "0x8E019acb11C7d17c26D334901fA2ac41C1f44d50"
BTC = "0x82455018F2c32943b3f12F4e59D0DA2FAf2257Ef"

ALL = [ETH, BNB, USDC, WCKB, USDT, BTC]

def test():    
    file = open("data.json")
    liquidityJson = json.load(file)

    ethPrice = findBestDestQty(ETH, 1000000000000000000, USDC, ALL, liquidityJson)
    print(ethPrice, ETH, USDC)


test()

