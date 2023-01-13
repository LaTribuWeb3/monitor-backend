const Addresses = require("./Addresses.js")
const Web3 = require('web3')
const fs = require('fs');
const {hadoukenVaultAbi, hadoukenVaultAddress } = require("./Addresses.js");

// const USDC = "0x149916D7128C36bbcebD04F794217Baf51085fB9";
// const USDT = "0xa0430f122fb7e4f6f509c9cb664912c2f01db3e2";

// function getSymbol(address){
//     if(address === "0xa0430f122fb7e4f6f509c9cb664912c2f01db3e2"){
//         return "USDT"
//     }
//     if(address === "0x149916D7128C36bbcebD04F794217Baf51085fB9"){
//         return "USDC"
//     }
//     else{
//         throw error(console.log("unknown token"))
//     }
// }

async function test() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching USDT/USDC liquidity at ${new Date()}`);

        vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        liquidity = await vault.methods.getPoolTokens('0xaf9d4028272f750dd2d028990fd664dc223479b1000000000000000000000013').call();
        formattedOutput = {}
        const UsdcUsdt = liquidity['0'][0] + '_' + liquidity['0'][1];
        const UsdtUsdc = liquidity['0'][1] + '_' + liquidity['0'][0];
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        formattedOutput[UsdcUsdt] = {
            token0: liquidity['1'][0],
            token1:liquidity['1'][1]
        };
        formattedOutput[UsdtUsdc] = {
                token0:liquidity['1'][1],
                token1: liquidity['1'][0]
            };
        

        fs.writeFileSync(`./hadouken_usd_liquidity.json`, JSON.stringify(formattedOutput, null, 2));
        }
    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ended fetching USDT/USDC liquidity at ${new Date()}`);
        console.log('============================================');
    }
 }


 test()