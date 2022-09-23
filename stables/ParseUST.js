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

class USTParser {
    constructor(blockStep, web3) {
        this.blockStep = blockStep
        this.web3 = web3
        this.crvAddress = "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490"
        this.ustpoolAddress = Addresses.stableAddresses["UST"].curve
        console.log(this.crvAddress)
        this.threepool = new web3.eth.Contract(Addresses.erc20Abi, this.crvAddress)
        this.ust = new web3.eth.Contract(Addresses.ustAbi, Addresses.stableAddresses["UST"].token)

        this.lastUpdateBlock = Addresses.stableAddresses["UST"].deployment - 5000

        this.fileName =  "LiquidityUST2.csv"
        this.jsonFileName = "LiquidityUST2.json"

        this.currUSTBalance = toBN("0")
        this.curr3PoolBalance = toBN("0")
        fs.writeFileSync(this.fileName, "block,tx,ust balance, 3 pool balance\n")       
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
            let currBlock = await this.web3.eth.getBlockNumber() - 5
            console.log("reading balances ust")
            let currUSTBalance = toBN(await this.ust.methods.balanceOf(this.ustpoolAddress).call(currBlock))
            console.log("reading balances 3pool")            
            let curr3PoolBalance = toBN(await this.threepool.methods.balanceOf(this.ustpoolAddress).call(currBlock))

            //currBlock = 11467027 + 100
            console.log("fetching events from block", this.lastUpdateBlock, " to block", currBlock)

            const contracts = [this.ust, this.threepool]
            const events = []

            {
                const inEvent = await this.getPastEventsInSteps(this.ust,
                    "Transfer",
                    this.lastUpdateBlock,
                    currBlock, {from: this.ustpoolAddress})

                const outEvent = await this.getPastEventsInSteps(this.ust,
                        "Transfer",
                        this.lastUpdateBlock,
                        currBlock, {"to": this.ustpoolAddress})    

                events.push(inEvent)
                events.push(outEvent)
            }

            {
                const inEvent = await this.getPastEventsInSteps(this.threepool,
                    "Transfer",
                    this.lastUpdateBlock,
                    currBlock, {_from: this.ustpoolAddress})

                const outEvent = await this.getPastEventsInSteps(this.threepool,
                        "Transfer",
                        this.lastUpdateBlock,
                        currBlock, {_to : this.ustpoolAddress})
    
                events.push(inEvent)
                events.push(outEvent)
            }            

            console.log(events[0].length, events[1].length, events[2].length, events[3].length)


            const balanceChangeEvents = {}

            const ustInEvents = events[0]
            const ustOutEvents = events[1]
            const threepoolInEvents = events[2]
            const threepoolOutEvents = events[3]

            for(const e of ustInEvents) {
                if(! balanceChangeEvents[e.blockNumber]) balanceChangeEvents[e.blockNumber] = []
                balanceChangeEvents[e.blockNumber].push({"tx" : e.transactionHash, "token" : "ust", "size" : toBN(e.returnValues.value)})
            }

            for(const e of ustOutEvents) {
                if(! balanceChangeEvents[e.blockNumber]) balanceChangeEvents[e.blockNumber] = []                
                balanceChangeEvents[e.blockNumber].push({"tx" : e.transactionHash, "token" : "ust", "size" : toBN(e.returnValues.value).mul(toBN("-1"))})
            }

            for(const e of threepoolInEvents) {
                if(! balanceChangeEvents[e.blockNumber]) balanceChangeEvents[e.blockNumber] = []                
                balanceChangeEvents[e.blockNumber].push({"tx" : e.transactionHash, "token" : "3pool", "size" : toBN(e.returnValues._value)})
            }

            for(const e of threepoolOutEvents) {
                if(! balanceChangeEvents[e.blockNumber]) balanceChangeEvents[e.blockNumber] = []                
                balanceChangeEvents[e.blockNumber].push({"tx" : e.transactionHash, "token" : "3pool", "size" : toBN(e.returnValues._value).mul(toBN("-1"))})
            }

            const blocks = Object.keys(balanceChangeEvents).reverse()

            const balances = {}
            
            balances[currBlock] = {"txs" : ["current"], "ust" : this.normalize(currUSTBalance, 6), "threepool" : this.normalize(curr3PoolBalance, 18) }
            /*
            fs.appendFileSync(this.fileName, currBlock + "," +
                "current," +
                this.normalize(currUSTBalance, 18) + "," +
                this.normalize(curr3PoolBalance, 18) + "\n")*/

            //console.log({blocks}, {balanceChangeEvents})

            for(const block of blocks) {
                for(const change of balanceChangeEvents[block]) {
                    //console.log({change})
                    if(change.token === "ust") currUSTBalance = currUSTBalance.add(change.size)
                    else curr3PoolBalance = curr3PoolBalance.add(change.size)

                    /*
                    fs.appendFileSync(this.fileName, block + "," +
                    change.tx + "," +
                    this.normalize(currUSTBalance, 18) + "," +
                    this.normalize(curr3PoolBalance, 18) + "\n")*/

                    const txs = []
                    if(balances[block]) {
                        txs.push(...balances[block].txs)
                    }

                    txs.push(change.tx)
                    balances[block] = {txs, "ust" : this.normalize(currUSTBalance, 6), "threepool" : this.normalize(curr3PoolBalance, 18)}
                }
            }

            for(const block of Object.keys(balances)) {

                /*
                if(block < 14733118) continue
                if(block > 14766817) continue*/

                fs.appendFileSync(this.fileName, block + "," +
                balances[block].txs[0] + "," +
                balances[block].ust + "," +
                balances[block].threepool + "\n")                
            }

            fs.writeFileSync(this.jsonFileName, JSON.stringify(balances))
        }
        catch(error) {
            console.log(error)
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

    const curve = new USTParser(50 * 1000, web3)
    await curve.fetchEvents(true)    
}

test()