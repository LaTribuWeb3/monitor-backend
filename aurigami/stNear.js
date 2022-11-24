const Web3 = require('web3')
const { toBN, toWei, fromWei } = Web3.utils
const axios = require('axios')
const Addresses = require("./Addresses.js")
const fs = require('fs');


async function checkMetapoolLiquidity(web3) {
    const nearAddress = "0xC42C30aC6Cc15faC9bD938618BcaA1a1FaE8501d"
    const near = new web3.eth.Contract(Addresses.erc20Abi, nearAddress)
    const nearDecimals = await near.methods.decimals().call()
    
    const stNEARAddress = "0x07F9F7f963C5cD2BBFFd30CcfB964Be114332E30"
    const stNEAR = new web3.eth.Contract(Addresses.erc20Abi, stNEARAddress)
    const stNEARDecimals = await stNEAR.methods.decimals().call()

    const metapoolAddress = "0x534BACf1126f60EA513F796a3377ff432BE62cf9"
    const nearBalance = await near.methods.balanceOf(metapoolAddress).call()
    const stNEARBalance = await stNEAR.methods.balanceOf(metapoolAddress).call()

    const balance = toBN(nearBalance).div(toBN("10").pow(toBN(nearDecimals)))
    const stbalance = toBN(stNEARBalance).div(toBN("10").pow(toBN(stNEARDecimals)))

    console.log(balance.toString())
    console.log(stbalance.toString())    

    fs.writeFileSync("stNEARLiquidity.json", JSON.stringify({"wNEARBalance" : balance.toString(), "stNEARBalance" : stbalance.toString()}))
}

async function checkNearXLiquidity(web3) {
    const nearAddress = "0xC42C30aC6Cc15faC9bD938618BcaA1a1FaE8501d"
    const near = new web3.eth.Contract(Addresses.erc20Abi, nearAddress)
    const nearDecimals = await near.methods.decimals().call()
    
    const stNEARAddress = "0xb39EEB9E168eF6c639f5e282FEf1F6bC4Dcae375"
    const stNEAR = new web3.eth.Contract(Addresses.erc20Abi, stNEARAddress)
    const stNEARDecimals = await stNEAR.methods.decimals().call()

    const metapoolAddress = "0x8E30eE730d4a6F3457befA60b25533F1400d31A6"
    const nearBalance = await near.methods.balanceOf(metapoolAddress).call()
    const stNEARBalance = await stNEAR.methods.balanceOf(metapoolAddress).call()

    const balance = toBN(nearBalance).div(toBN("10").pow(toBN(nearDecimals)))
    const stbalance = toBN(stNEARBalance).div(toBN("10").pow(toBN(stNEARDecimals)))

    console.log(balance.toString())
    console.log(stbalance.toString())    

    fs.writeFileSync("NEARXLiquidity.json", JSON.stringify({"wNEARBalance" : balance.toString(), "NEARXBalance" : stbalance.toString()}))
}

function sleep(ms) {
    return new Promise((resolve) => {
      setTimeout(resolve, ms);
    });
  }

async function test() {
    const web3 = new Web3("https://mainnet.aurora.dev")    

    while(true) {
        try {
            await checkMetapoolLiquidity(web3)
            await checkNearXLiquidity(web3)            
        }
        catch(error) {
            console.log(error)
        }

        console.log("sleep for an hour")
        await sleep(1000 * 60 * 60)
    }
}

test()
