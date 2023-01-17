const Addresses = require("./Addresses.js")
const Web3 = require('web3')
const fs = require('fs');
const {hadoukenVaultAbi, hadoukenVaultAddress, hadoukenUSDPoolABI, hadoukenUSDPoolAddress } = require("./Addresses.js");

async function hadoukenUSDLiquidityFetcher() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching USDT/USDC liquidity at ${new Date()}`);
        vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        liquidity = await vault.methods.getPoolTokens('0xaf9d4028272f750dd2d028990fd664dc223479b1000000000000000000000013').call();
        formattedOutput = {}
        const UsdcUsdt = liquidity['0'][0] + '_' + liquidity['0'][1];
        const UsdtUsdc = liquidity['0'][1] + '_' + liquidity['0'][0];
        // const UsdcUsdt = '0x186181e225dc1Ad85a4A94164232bD261e351C33_0x8E019acb11C7d17c26D334901fA2ac41C1f44d50';
        // const UsdtUsdc = '0x8E019acb11C7d17c26D334901fA2ac41C1f44d50_0x186181e225dc1Ad85a4A94164232bD261e351C33';
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        formattedOutput[UsdcUsdt] = {
            token0: liquidity['1'][0],
            token1:liquidity['1'][1],
            ampFactor: '300'
        };
        formattedOutput[UsdtUsdc] = {
                token0:liquidity['1'][1],
                token1: liquidity['1'][0],
                ampFactor: '300'
            };
        

        return formattedOutput;
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
 
 module.exports = {hadoukenUSDLiquidityFetcher}