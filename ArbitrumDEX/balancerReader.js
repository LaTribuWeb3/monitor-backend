const Web3 = require("web3")
const web3Arbitrum = new Web3("https://arb1.arbitrum.io/rpc")
const web3Eth = new Web3("https://rpc.ankr.com/eth")
const Addresses = require("./Addresses.js")
const fs = require('fs')
const assert = require('assert')

function toBN(n) {
    return Web3.utils.toBN(n)
}

function fromWei(n) {
    return Web3.utils.fromWei(n)
}

async function retry(fn, params, retries = 0) {
    try {
        const res = await  fn(...params)
        if(retries){
            console.log(`retry success after ${retries} retries`)
        } else {
            console.log(`success on first try`)
        }
        return res
    } catch (e) {
        console.error(e)
        retries++
        console.log(`retry #${retries}`)
        await new Promise(resolve => setTimeout(resolve, 1000 * 5 * retries))
        return retry(fn, params, retries)
    }
}

async function getPastEvents(contract, key, fromBlock, toBlock, filter = {}) {
    const fn = (...args) => contract.getPastEvents(...args)
    //const filter = {tokenIn : [Addresses.daiAddress], tokenOut : [Addresses.ohmAddress]}
    const events = await retry(fn, [key, {filter, fromBlock, toBlock}])
    return events
}

async function readPairEventsBalancer(token0, token1, startBlock, endBlock, fileName, web3) {

    //console.log("pair address 2", pairAddress)
    const vault = new web3.eth.Contract(Addresses.balancerVaultAbi, Addresses.balancerVault)
    //console.log("pair address 3", pairAddress)
    //console.log(endBlock - startBlock)

    const fees = {} // mapping from id to fees

    console.log({startBlock}, {endBlock})    
    const eventsDaiToOHM = await getPastEvents(vault, "Swap", startBlock, endBlock, {tokenIn : [Addresses.daiAddress], tokenOut : [Addresses.ohmAddress]})
    const eventsOHMToDai = await getPastEvents(vault, "Swap", startBlock, endBlock, {tokenOut : [Addresses.daiAddress], tokenIn : [Addresses.ohmAddress]})

    const allEvents = eventsDaiToOHM.concat(eventsOHMToDai)
    const events = allEvents.sort((a,b) => a.blockNumber - b.blockNumber)

    //console.log(events/*[0].returnValues*/, {startBlock}, {endBlock})


    //console.log({events})

    for(const e of events) {
        const amount0 = Number(fromWei(toBN(e.returnValues.amountIn)))
        const blockNumber = e.blockNumber

        let amount1 = Number(fromWei(toBN(e.returnValues.amountOut)))

        const poolId = e.returnValues.poolId
        if(!(poolId in fees)) {
            const getPoolResult = await vault.methods.getPool(poolId).call()
            console.log({getPoolResult})
            const poolAddress = getPoolResult["0"]
            console.log(poolAddress)
            const poolContract = new web3.eth.Contract(Addresses.balancerPoolAbi, poolAddress)
            fees[poolId] = Number(fromWei(await poolContract.methods.getSwapFeePercentage().call()))
        }

        // adjust out amount according to fees
        const adjustedOutAmount = amount1 / (1 - fees[poolId])
        console.log({amount1}, {adjustedOutAmount})
        amount1 = adjustedOutAmount

        const firstToken = e.returnValues.tokenIn
        const secondToken = e.returnValues.tokenOut 

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


async function getHistoricalData(token0, token1, isSushi, fee, numMonths, outputFileName, web3) {
    const step = (await web3.eth.getChainId()) === 42161 ? 10000 : 1000
    console.log({step})
    const currentBlock = await web3.eth.getBlockNumber()
    const endBlock = currentBlock

    const xMonthsAgo = Math.floor(+new Date() / 1000) - numMonths * 30 * 24 * 60 * 60    
    const startBlock = await findBlockInTheDessert(web3, xMonthsAgo, 0, endBlock)

    console.log("block number, qty 0, qty1, price")
    fs.writeFileSync(outputFileName, "block number, qty 0, qty1, price")
    fs.appendFileSync(outputFileName, "\n")     

    for(let i = startBlock ; i < endBlock ; i += step) {
        const realStart = i
        let realEnd = realStart + step - 1
        if(realEnd > endBlock) realEnd = endBlock

        //console.log(realStart, realEnd)
        await readPairEventsBalancer(token0, token1, realStart, realEnd, outputFileName, web3)
    }
}



async function getCSVHistoricalData(token0, token1, isSushi, fee, numMonths, outputFileName, web3) {
    const rawFileName = outputFileName + "_" + ".draft"
    await getHistoricalData(token0, token1, isSushi, fee, numMonths, rawFileName, web3)
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

async function findBlockInTheDessert(web3, targetTimestamp, startBlock, endBlock) {
    console.log(startBlock, endBlock)
    if(startBlock + 1 >= endBlock) {
        console.log("block found", startBlock)
        return startBlock
    }

    const pivotBlock = parseInt(endBlock - (endBlock - startBlock) / 2)
    console.log({pivotBlock})

    const pivotTimestamp = Number((await web3.eth.getBlock(pivotBlock)).timestamp)

    console.log({pivotTimestamp}, {targetTimestamp})

    if(pivotTimestamp > targetTimestamp) return findBlockInTheDessert(web3, targetTimestamp, startBlock, pivotBlock)
    else return findBlockInTheDessert(web3, targetTimestamp, pivotBlock, endBlock)
}


async function slow() {
    const fn = (...args) => getCSVHistoricalData(...args)

    await retry(fn, [Addresses.daiAddress, Addresses.ohmAddress, true, 0, 3, "ohm-dai-mainnet.csv", web3Eth])
}

slow()