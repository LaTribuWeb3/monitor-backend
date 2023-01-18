const Web3 = require('web3')
const Aave = require("./AaveParser.js")
const Addresses = require("./Addresses.js")

async function HadoukenParser() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc")
    const aave = new Aave(Addresses.hadoukenAddress, "GW", web3, "data.json")
    await aave.main(false)
 }

 module.exports = {HadoukenParser}
