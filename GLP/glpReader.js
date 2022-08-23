const Web3 = require("web3")
const web3Arbitrum = new Web3("https://arb1.arbitrum.io/rpc")
const web3Eth = new Web3("https://rpc.ankr.com/eth")
const Addresses = require("./Addresses.js")
const fs = require('fs')

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

async function getPastEvents(contract, key, fromBlock, toBlock) {
    const fn = (...args) => contract.getPastEvents(...args)
    const events = await retry(fn, [key, {fromBlock, toBlock}])
    return events
}

async function readLiquidityEvents(web3, fileName, startBlock, endBlock) {
    const glpManager = new web3.eth.Contract(Addresses.glpManagerAbi, Addresses.glpManagerAddress)
    
    const step = 1000

    let allEvents = []
    for(let i = startBlock ; i < endBlock ; i += step) {
        const realStart = i
        let realEnd = realStart + step - 1
        if(realEnd > endBlock) realEnd = endBlock

        console.log(i, "/", endBlock)

        const addLiquidityEvents = await getPastEvents(glpManager, "AddLiquidity", realStart, realEnd)
        const removeLiquidityEvents = await getPastEvents(glpManager, "RemoveLiquidity", realStart, realEnd)
        
        allEvents = allEvents.concat(addLiquidityEvents).concat(removeLiquidityEvents)
    }
    
    // sort events
    allEvents.sort(function(a, b) {
        const keyA = Number(a.blockNumber)
        const keyB = Number(b.blockNumber)

        if (keyA < keyB) return -1;
        if (keyA > keyB) return 1;
        return 0;
    })

    fs.writeFileSync(fileName, "block number, aum, glpSupply, price\n")    

    for(const e of allEvents) {
        //console.log({e})
        const blockNumber = e.blockNumber

        const aum = toBN(e.returnValues.aumInUsdg)
        const glpSupply = toBN(e.returnValues.glpSupply)
        const factor = toBN(web3.utils.toWei("1"))
        const price = web3.utils.fromWei(aum.mul(factor).div(glpSupply))

        const string = 
            blockNumber.toString() + "," +
            aum.toString() + "," +
            glpSupply.toString() + "," +
            price.toString() + "\n"

        fs.appendFileSync(fileName, string)
    }
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


async function getGlpStatsToCsv(web3, filename, numMonths) {
    const currentBlock = await web3.eth.getBlockNumber()
    const endBlock = currentBlock

    const xMonthsAgo = Math.floor(+new Date() / 1000) - numMonths * 30 * 24 * 60 * 60    
    const startBlock = await findBlockInTheDessert(web3, xMonthsAgo, 0, endBlock)
    //const startBlock = 16243362

    await readLiquidityEvents(web3Arbitrum, filename + ".draft", startBlock, endBlock)

    const allFileContents = fs.readFileSync(filename + ".draft", 'utf-8');
    console.log({allFileContents})

    const outputFileName = filename

    let lastData = [0xFFFFFFFF, "", "", ""]
    fs.writeFileSync(outputFileName, "block number, aum, glpSupply, price")
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

async function main() {
    const fn = (...args) => getGlpStatsToCsv(...args)
    await retry(fn, [web3Arbitrum, "glp.csv", 3])
}

main()
