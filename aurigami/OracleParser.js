const Web3 = require('web3')
const Compound = require("./CompoundParser.js")
const Addresses = require("./Addresses.js")

let iter = 0
let comp
async function updateOracle() {
    try {
        if(iter++ % 50 == 0) await comp.initPrices()
        else await comp.initPricesQuickly()

        console.log(comp.getData())
    }
    catch(error) {
        console.log(error, "will try again in 10 minutes")
    }

    console.log("sleeping for 10 minute")
    setTimeout(updateOracle, 1000 * 6 * 1)
}

async function test() {
    let iter = 0
    const web3 = new Web3("https://mainnet.aurora.dev")
    comp = new Compound(Addresses.aurigamiAddress, "NEAR", web3, "oracle.json")

    await updateOracle(comp)
 }

 test()

