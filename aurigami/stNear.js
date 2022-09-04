const Web3 = require('web3')
const { toBN, toWei, fromWei } = Web3.utils
const axios = require('axios')
const Addresses = require("./Addresses.js")
const fs = require('fs');


async function checkMetapoolLiquidity(web3) {
    const nearAddress = "0xC42C30aC6Cc15faC9bD938618BcaA1a1FaE8501d"
    const near = new web3.eth.Contract(Addresses.erc20Abi, nearAddress)
    const nearDecimals = await near.methods.decimals().call()

    const metapoolAddress = "0x534BACf1126f60EA513F796a3377ff432BE62cf9"
    const nearBalance = await near.methods.balanceOf(metapoolAddress).call()

    const balance = toBN(nearBalance).div(toBN("10").pow(toBN(nearDecimals)))

    console.log(balance.toString())

    fs.writeFileSync("stNEARLiquidity.json", JSON.stringify({"stNEARBalance" : balance.toString()}))
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
        }
        catch(error) {
            console.log(error)
        }

        console.log("sleep for an hour")
        await sleep(1000 * 60 * 60)
    }
}

test()
