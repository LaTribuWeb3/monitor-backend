const Web3 = require("web3")
const web3 = new Web3("https://arb1.arbitrum.io/rpc")
const Addresses = require("./Addresses.js")
const fs = require('fs')
const assert = require('assert')
const { timeStamp } = require("console")

function toBN(n) {
    return web3.utils.toBN(n)
}

function fromWei(n) {
    return web3.utils.fromWei(n)
}

async function readPairEventsSushi(token0, token1, startBlock, endBlock, fileName) {
    //const factory = new web3.eth.Contract(Addresses.uniswapFactoryAbi, Addresses.uniswapFactoryAddress)
    const pairAddress = Addresses.dpxWethArbitrumPair

    assert(token0 === Addresses.wethArbitrum, "unsuppoted sushi pair")
    assert(token1 === Addresses.dpxArbitrum, "unsuppoted sushi pair")    

    //console.log("pair address 2", pairAddress)
    const pair = new web3.eth.Contract(Addresses.uniswapV2PairAbi, pairAddress)
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

        console.log({e}, blockNumber, ",",
                    token0.toLowerCase() == firstToken.toLowerCase() ? amount0 : amount1, ",",
                    token1.toLowerCase() == secondToken.toLowerCase() ? amount1 : amount0, ",",
                    price)

        const string = 
            blockNumber.toString() + "," +
            (token0.toLowerCase() == firstToken.toLowerCase() ? amount0 : amount1) + "," +
            (token1.toLowerCase() == secondToken.toLowerCase() ? amount1 : amount0) + "," +
            price.toString() + "\n"

        fs.appendFileSync(fileName, string)                    
/*
                    if(blockNumber == 14099122 || blockNumber === 14098253) {
                        console.log({e})
                    }                   
                    if(blockNumber == 14099122) sd*/
        //console.log({e})
    }
}

async function readPairEventsUniV3(token0, token1, fee, startBlock, endBlock, fileName) {
    const factory = new web3.eth.Contract(Addresses.uniswapFactoryV3Abi, Addresses.uniswapFactoryV3Address)
    const pairAddress = await factory.methods.getPool(token0, token1, fee/*10000*/).call()
    //console.log("pair address 2", pairAddress)
    const pair = new web3.eth.Contract(Addresses.uniswapV3PairAbi, pairAddress)
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
        let amount0 = Number(fromWei(toBN(e.returnValues.amount0)))
        const blockNumber = e.blockNumber

        let amount1 = Number(fromWei(toBN(e.returnValues.amount1)))

        if(amount0 < 0) amount0 = amount0 * -1
        if(amount1 < 0) amount1 = amount1 * -1

        const price = token0.toLowerCase() == firstToken.toLowerCase() ? amount0 / amount1 : amount1 / amount0

        console.log(blockNumber, ",",
                    token0.toLowerCase() == firstToken.toLowerCase() ? amount0 : amount1, ",",
                    token1.toLowerCase() == secondToken.toLowerCase() ? amount1 : amount0, ",",
                    price)


        const string = blockNumber.toString() + "," +
                (token0.toLowerCase() == firstToken.toLowerCase() ? amount0 : amount1) + "," +
                (token1.toLowerCase() == secondToken.toLowerCase() ? amount1 : amount0) + "," +
                price.toString() + "\n"
        
                fs.appendFileSync(fileName, string)                     
/*
                    if(blockNumber == 14099122 || blockNumber === 14098253) {
                        console.log({e})
                    }                   
                    if(blockNumber == 14099122) sd*/
        //console.log({e})
    }
}

async function getHistoricalData(token0, token1, isSushi, fee, numMonths, outputFileName) {
    const step = 10000
    const currentBlock = await web3.eth.getBlockNumber()
    const endBlock = currentBlock

    const xMonthsAgo = Math.floor(+new Date() / 1000) - numMonths * 30 * 24 * 60 * 60    
    const startBlock = await findBlockInTheDessert(xMonthsAgo, 0, endBlock)

    console.log("block number, qty 0, qty1, price")
    fs.writeFileSync(outputFileName, "block number, qty 0, qty1, price")
    fs.appendFileSync(outputFileName, "\n")     

    for(let i = startBlock ; i < endBlock ; i += step) {
        const realStart = i
        let realEnd = realStart + step - 1
        if(realEnd > endBlock) realEnd = endBlock

        //console.log(realStart, realEnd)
        if(isSushi) await readPairEventsSushi(token0, token1, realStart, realEnd, outputFileName)
        else await readPairEventsUniV3(token0, token1, fee, startBlock, endBlock, outputFileName)
    }
}



async function getCSVHistoricalData(token0, token1, isSushi, fee, numMonths, outputFileName) {
    const rawFileName = outputFileName + "_" + ".draft"
    await getHistoricalData(token0, token1, isSushi, fee, numMonths, rawFileName)
    const allFileContents = fs.readFileSync(rawFileName, 'utf-8');
    console.log({allFileContents})

    let lastData = [0xFFFFFFFF, "", "", ""]
    fs.writeFileSync(outputFileName, "block number, qty 0, qty1, price")
    fs.appendFileSync(outputFileName, "\n")  
    allFileContents.split(/\r?\n/).forEach(line =>  {
        //console.log(`Line from file: ${line}`);
    
        const split = line.split(",")
        const block = Number(split[0])
        const x = split[1]
        const y = split[2]
        const price = split[3]
        console.log({block}, {x}, {y}, {price});
    
        for(let i = lastData[0] ; i < block ; i++) {
            const string = 
                i.toString() + "," + lastData[1].toString() + "," + lastData[2].toString() + "," + lastData[3].toString() 
            fs.appendFileSync(outputFileName, string + "\n")
        }
    
        lastData = split
        lastData[0] = block
    })
}

async function findBlockInTheDessert(targetTimestamp, startBlock, endBlock) {
    console.log(startBlock, endBlock)
    if(startBlock + 1 >= endBlock) {
        console.log("block found", startBlock)
        return startBlock
    }

    const pivotBlock = parseInt(endBlock - (endBlock - startBlock) / 2)
    console.log({pivotBlock})

    const pivotTimestamp = Number((await web3.eth.getBlock(pivotBlock)).timestamp)

    console.log({pivotTimestamp}, {targetTimestamp})

    if(pivotTimestamp > targetTimestamp) return findBlockInTheDessert(targetTimestamp, startBlock, pivotBlock)
    else return findBlockInTheDessert(targetTimestamp, pivotBlock, endBlock)
}

async function test() {
    const threeMonthsAgo = Math.floor(+new Date() / 1000) - 3 * 30 * 24 * 60 * 60
    const startBlock = 0
    const endBlock = Number(await web3.eth.getBlockNumber())

    await findBlockInTheDessert(threeMonthsAgo, startBlock, endBlock)
}
//test()

getCSVHistoricalData(Addresses.wethArbitrum, Addresses.dpxArbitrum, true, 0, 3, "orisushi")
//getCSVHistoricalData(Addresses.wethArbitrum, Addresses.gmxArbitrum, false, 10000, 3, "oriv3")
