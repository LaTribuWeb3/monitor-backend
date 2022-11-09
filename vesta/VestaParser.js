const Web3 = require('web3')
const Vesta = require("./Vesta.js")


async function test() {
    const web3 = new Web3("https://arb1.arbitrum.io/rpc")
    const vesta = new Vesta(web3 ,"ARBITRUM","data.json")

    /*
    await vesta.initGLP()
    console.log(vesta.glpData)
    sd

    console.log("getting last block")
    const lastblock = await web3.eth.getBlockNumber() - 10
    console.log({lastblock})
    await vesta.collectAllUsers()
    await vesta.initPrices()
    vesta.getData()
    */
    await vesta.main(false)
 }

 test()

