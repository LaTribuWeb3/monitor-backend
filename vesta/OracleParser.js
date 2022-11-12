const Web3 = require('web3')
const Vesta = require("./Vesta.js")
const Addresses = require("./Addresses.js")

let iter = 0
let vesta
async function updateOracle() {
    try {
        if(iter++ % 50 == 0) await vesta.initPrices()
        else await vesta.initPricesQuickly()

        vesta.getData()
    }
    catch(error) {
        console.log(error, "will try again in 10 minutes")
    }

    console.log("sleeping for 10 minute")
    setTimeout(updateOracle, 1000 * 60 * 10)
}

async function test() {
    const web3 = new Web3("https://arb1.arbitrum.io/rpc")
    vesta = new Vesta(web3 ,"ARBITRUM","oracle.json")

    await updateOracle()
 }

 test()

