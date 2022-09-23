const Web3 = require('web3')
const Addresses = require("./Addresses.js")
const { toBN, toWei, fromWei } = Web3.utils
const fs = require('fs')


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

class CurveParser {
    constructor(tokenName, blockStep, web3) {
        this.tokenName = tokenName
        this.blockStep = blockStep
        this.web3 = web3
        let abi = []
        if(Addresses.stableAddresses[tokenName].event === "TokenExchange") abi = Addresses.threepoolAbi
        else abi = Addresses.metapoolAbi
        this.curve = new web3.eth.Contract(abi, Addresses.stableAddresses[tokenName].curve)

        this.lastUpdateBlock = Addresses.stableAddresses[tokenName].deployment

        this.fileName = tokenName + ".csv"
        fs.writeFileSync(this.fileName, "block,tx,inTokn,inAmount,outToken,outAmount\n")

        this.coinNames = []
        this.coinDecimals = []

        this.threepoolCoinNames = ["DAI", "USDC", "USDT"]
        this.threepoolDecimals = [18, 6, 6]
        this.events = []

        this.susdCoinNames = ["DAI", "USDC", "USDT", "SUSD"]
        this.susdDecimals = [18, 6, 6, 18]
    }

    async initMetapool() {
        const stableAddress = await this.curve.methods.coins(0).call()
        const stableContact = new this.web3.eth.Contract(Addresses.metapoolAbi, stableAddress)
        const decimals = await stableContact.methods.decimals().call()
        const symbol = await stableContact.methods.symbol().call()

        this.coinNames.push(symbol)
        this.coinDecimals.push(decimals)

        this.coinNames = this.coinNames.concat(this.threepoolCoinNames)
        this.coinDecimals = this.coinDecimals.concat(this.threepoolDecimals)
    }

    async init3Pool() {
        this.coinNames = this.threepoolCoinNames
        this.coinDecimals = this.threepoolDecimals
    }

    async init() {
        const fn3Pool = (...args) => this.init3Pool(...args)
        const fnMetaPool = (...args) => this.initMetapool(...args)

        if(["USDT", "USDC", "DAI"].includes(this.tokenName)) await retry(fn3Pool, [])
        else if(this.tokenName === "SUSD") {
            this.coinDecimals = this.susdDecimals
            this.coinNames = this.susdCoinNames 
        }
        else await retry(fnMetaPool, [])
    }

    normalize(amount, decimals) {
        const factor = toBN("10").pow(toBN(18 - decimals))

        //console.log(factor.toString(), {decimals}, amount.toString())

        const norm = toBN(amount.toString()).mul(factor)
        /*
        if(norm.toString() === "266922175685792065767263000000000000") {
            console.log(amount.toString(), decimals)
            console.log(norm.toString(), fromWei(norm), Number(fromWei(norm)))
        }*/

        return Number(fromWei(norm))
    }

    async fetchEvents(onlyOnce = false) {
        try {
            const currBlock = await this.web3.eth.getBlockNumber() - 10
            console.log("fetching events from block", this.lastUpdateBlock, " to block", currBlock)
            const events = await this.getPastEventsInSteps(this.curve, Addresses.stableAddresses[this.tokenName].event, this.lastUpdateBlock, currBlock, {})

            for(const e of events) {
                const block = e.blockNumber
                const txHash = e.transactionHash
                const coinInId = e.returnValues.sold_id
                const coinOutId = e.returnValues.bought_id
                const inAmount = e.returnValues.tokens_sold
                const outAmount = e.returnValues.tokens_bought

                const inName = this.coinNames[coinInId]
                const outName = this.coinNames[coinOutId]

                const normalizedInAmount = this.normalize(inAmount, this.coinDecimals[coinInId])
                const normalizedOutAmount = this.normalize(outAmount, this.coinDecimals[coinOutId])

                /*
                console.log({txHash})
                if(normalizedInAmount === 266922175685792060 || normalizedOutAmount === 266922175685792060) {
                    //console.log({txHash})
                    sd
                }
                //console.log({normalizedInAmount}, {normalizedOutAmount}, txHash)*/
                if(inName !== this.tokenName) {
                    // for meta pool, the log of input token amount = 3pool amount. which is hard to translate to usd
                    if(this.tokenName !== "USDT" && this.tokenName !== "DAI") continue
                }

                if(! [inName, outName].includes(this.tokenName)) continue

                if(normalizedInAmount === 0 || normalizedOutAmount === 0) continue

                fs.appendFileSync(this.fileName,
                    block + "," + 
                    txHash + "," +
                    inName + "," +
                    normalizedInAmount + "," +
                    outName + "," +
                    normalizedOutAmount + "\n")
                
                    let volume
                    let counterToken
                    let price
                    if(this.tokenName === inName) {
                        counterToken = outName
                        price = normalizedOutAmount / normalizedInAmount
                        volume = normalizedOutAmount
                    }
                    else {
                        counterToken = inName
                        price = normalizedInAmount / normalizedOutAmount
                        volume = normalizedInAmount
                    }

                    this.events.push({block, txHash, volume, counterToken, price})
            }
            
            this.lastUpdateBlock = currBlock
            fs.writeFileSync(this.tokenName + ".json", JSON.stringify(this.events, null, 2))
        }
        catch(error) {
            console.log(error)
        }
        finally {
            if( ! onlyOnce) {
                console.log("sleeping for 1 hour")
                setTimeout(this.fetchEvents.bind(this), 1000 * 60 * 60)    
            }
        }
    }

    async getPastEventsInSteps(contract, key, from, to, filter){
        let totalEvents = []
        for (let i = from; i < to; i = i + this.blockStep) {
            const fromBlock = i
            const toBlock = i + this.blockStep > to ? to : i + this.blockStep
            console.log("getPastEventsInSteps", i, "/", to)
            const fn = (...args) => contract.getPastEvents(...args)
            const events = await retry(fn, [key, {filter, fromBlock, toBlock}])
            totalEvents = totalEvents.concat(events)
        }
        return totalEvents
    }    
}

async function test() {
    const web3 = new Web3("TODO")
    /*const curve = new CurveParser("DOLA", 100 * 1000, web3)
    await curve.initMetapool()
    await curve.fetchEvents()*/

    for(const stable of Object.keys(Addresses.stableAddresses)) {
        //if(stable !== "UST") continue
        console.log("parsing", stable)
        const curve = new CurveParser(stable, 10 * 1000, web3)
        await curve.init()
        await curve.fetchEvents(true)    
    }
}

test()