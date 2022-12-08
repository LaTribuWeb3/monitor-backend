const Web3 = require('web3')
const Aave = require("./AaveParser.js")
const Addresses = require("./Addresses.js")

let iter = 0
let aave
async function updateOracle() {
    try {
        aave.lastUpdateTime = Math.floor(+new Date() / 1000)  

        if(iter++ % 50 == 0) await aave.initPrices()
        else await aave.initPricesQuickly()

        aave.getData()
    }
    catch(error) {
        console.log(error, "will try again in 10 minutes")
    }

    console.log("sleeping for 10 minute")
    setTimeout(updateOracle, 1000 * 60 * 10)
}

async function test() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc")
    aave = new Aave(Addresses.hadoukenAddress, "GW", web3, "oracle.json")

    await updateOracle(aave)
 }

 test()

