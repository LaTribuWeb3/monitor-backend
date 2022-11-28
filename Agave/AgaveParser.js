const Web3 = require('web3')
const Aave = require("./AaveParser.js")
const Addresses = require("./Addresses.js")

async function test() {
    const web3 = new Web3("https://rpc.gnosischain.com")    
    const aave = new Aave(Addresses.agaveAddress, "GNOSIS", web3, "data.json")
    await aave.main(false)
 }

 test()
