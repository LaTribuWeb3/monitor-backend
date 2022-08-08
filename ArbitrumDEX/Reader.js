const Web3 = require("web3")
const web3 = new Web3("https://mainnet.infura.io/v3/516f946979bc4fa187edcdc164e0bac0")
const Sushi = require("./Sushi.js")

function toBN(n) {
    return web3.utils.toBN(n)
}

function fromWei(n) {
    return web3.utils.fromWei(n)
}

function getLPTokenValue(price, k) {
    // x*y = k
    // x/y = price
    // value = x + y
    // x = y * price
    // price * y^2 = k
    // y = sqrt(k/price)
    // x = k / sqrt(k/price)
    // x + y = sqrt(k/price) + k / sqrt(k/price)
    
    const y = Math.sqrt(k/price)
    const x = k / y

    return x + y * price
}

async function getK(token0, token1, startBlock) {
    const factory = new web3.eth.Contract(Sushi.uniswapFactoryAbi, Sushi.uniswapFactoryAddress)
    const pairAddress = await factory.methods.getPair(token0, token1).call()
    console.log("pair address", pairAddress)
    const pair = new web3.eth.Contract(Sushi.uniswapV2PairAbi, pairAddress)
    const reserves = await pair.methods.getReserves().call(startBlock)
    const r0 = Number(fromWei(reserves._reserve0))
    const r1 = Number(fromWei(reserves._reserve1))

    const k = r0 * r1

    const totalSupply = Number(fromWei(await pair.methods.totalSupply().call(startBlock)))

    console.log(r0, r1, totalSupply)

    return k / (totalSupply ** 2)
}

async function readPairEvents(token0, token1, startBlock, endBlock, k) {
    const factory = new web3.eth.Contract(Sushi.uniswapFactoryAbi, Sushi.uniswapFactoryAddress)
    const pairAddress = await factory.methods.getPair(token0, token1).call()
    //console.log("pair address 2", pairAddress)
    const pair = new web3.eth.Contract(Sushi.uniswapV2PairAbi, pairAddress)
    const firstToken = await pair.methods.token0().call()
    const secondToken = await pair.methods.token1().call()
    //console.log("pair address 3", pairAddress)
    //console.log(endBlock - startBlock)
    const events = await pair.getPastEvents("Swap",
        {
            fromBlock: startBlock,
            toBlock: endBlock
        }
    )

    //console.log({events})

    for(const e of events) {
        const amount0 = fromWei(toBN(e.returnValues.amount0In).add(toBN(e.returnValues.amount0Out)))
        const blockNumber = e.blockNumber

        const amount1 = fromWei(toBN(e.returnValues.amount1In).add(toBN(e.returnValues.amount1Out)))

        const price = token0.toLowerCase() == firstToken.toLowerCase() ? amount0 / amount1 : amount1 / amount0

        console.log(blockNumber, ",",
                    token0.toLowerCase() == firstToken.toLowerCase() ? amount0 : amount1, ",",
                    token1.toLowerCase() == secondToken.toLowerCase() ? amount1 : amount0, ",",
                    price, ",", getLPTokenValue(price, k))
/*
                    if(blockNumber == 14099122 || blockNumber === 14098253) {
                        console.log({e})
                    }                   
                    if(blockNumber == 14099122) sd*/
        //console.log({e})
    }
}

async function getHistoricalData(token0, token1, numMonths) {
    const step = 10000
    const monthBlock = 172800
    const currentBlock = await web3.eth.getBlockNumber()
    const endBlock = currentBlock
    const startBlock = endBlock - monthBlock * numMonths

    const k = await getK(token0, token1, startBlock)

    console.log("block number, qty 0, qty1, price, lp price")

    for(let i = startBlock ; i < endBlock ; i += step) {
        const realStart = i
        let realEnd = realStart + step - 1
        if(realEnd > endBlock) realEnd = endBlock

        //console.log(realStart, realEnd)

        await readPairEvents(token0, token1, realStart, realEnd, k)

    }
}




//getHistoricalData(Sushi.wethAddress, Sushi.ohmAddress, 3)
getHistoricalData(Sushi.wethAddress, Sushi.daiAddress, 6)
/*
const fs = require('fs');

const allFileContents = fs.readFileSync('ohm_3_month.csv', 'utf-8');

let lastData = [0xFFFFFFFF, "", "", "", ""]
console.log("block number, qty 0, qty1, price, lp price")
allFileContents.split(/\r?\n/).forEach(line =>  {
    //console.log(`Line from file: ${line}`);

    const split = line.split(" , ")
    const block = Number(split[0])
    const x = split[1]
    const y = split[2]
    const spellPrice = split[3]
    const lpPrice = split[4]
    //console.log({block}, {x}, {y}, {spellPrice}, {lpPrice});

    for(let i = lastData[0] ; i < block ; i++) {
        console.log(i, " , ", lastData[1], " , ", lastData[2], " , ", lastData[3], " , ", lastData[4])
    }

    lastData = split
    lastData[0] = block
});
*/