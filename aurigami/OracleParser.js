const Web3 = require('web3')
const Compound = require("./CompoundParser.js")
const Addresses = require("./Addresses.js")

let iter = 0
let comp
async function updateOracle() {
    try {
        comp.lastUpdateTime = Math.floor(+new Date() / 1000)  

        if(iter++ % 50 == 0) await comp.initPrices()
        else await comp.initPricesQuickly()

        comp.getData()
    }
    catch(error) {
        console.log(error, "will try again in 10 minutes")
    }

    console.log("sleeping for 10 minute", (new Date()).toString())
    setTimeout(updateOracle, 1000 * 60 * 10)
}

async function test() {
    let iter = 0
    //const web3 = new Web3("https://mainnet.aurora.dev")
    comp = new Compound(Addresses.aurigamiAddress, "NEAR", "https://mainnet.aurora.dev", "oracle.json")

    await updateOracle(comp)
 }

 test()

