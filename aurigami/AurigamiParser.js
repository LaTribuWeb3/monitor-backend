const Web3 = require('web3')
const Compound = require("./CompoundParser.js")
const Addresses = require("./Addresses.js")

async function test() {
    const web3 = new Web3("https://mainnet.aurora.dev")
    const comp = new Compound(Addresses.aurigamiAddress, "NEAR", web3, "data.json")
    await comp.main()
 }

 test()

