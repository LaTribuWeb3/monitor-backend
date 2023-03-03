const Addresses = require("./Addresses.js")
const Web3 = require('web3')
const fs = require('fs');
const {hadoukenVaultAbi, hadoukenVaultAddress, hadoukenUSDPoolABI, hadoukenUSDPoolAddress } = require("./Addresses.js");

async function hadoukenUSDLiquidityFetcher() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching USDT/USDC liquidity at ${new Date()}`);
        pool = new web3.eth.Contract(hadoukenUSDPoolABI, hadoukenUSDPoolAddress);
        ampParameters = await pool.methods.getAmplificationParameter().call();
        ampFactor = Number(ampParameters["value"]) / Number(ampParameters["precision"]);
        vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        liquidity = await vault.methods.getPoolTokens('0xaf9d4028272f750dd2d028990fd664dc223479b1000000000000000000000013').call();
        formattedOutput = {}
        // const UsdcUsdt = liquidity['0'][0] + '_' + liquidity['0'][1];
        // const UsdtUsdc = liquidity['0'][1] + '_' + liquidity['0'][0];
        const UsdcUsdt = '0x186181e225dc1Ad85a4A94164232bD261e351C33_0x8E019acb11C7d17c26D334901fA2ac41C1f44d50';
        const UsdtUsdc = '0x8E019acb11C7d17c26D334901fA2ac41C1f44d50_0x186181e225dc1Ad85a4A94164232bD261e351C33';
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        formattedOutput[UsdcUsdt] = {
            token0: liquidity['1'][0].slice(0, -12),
            token1:liquidity['1'][1].slice(0, -12),
            ampFactor: ampFactor
        };
        formattedOutput[UsdtUsdc] = {
                token0:liquidity['1'][1].slice(0, -12),
                token1: liquidity['1'][0].slice(0, -12),
                ampFactor: ampFactor
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

 async function hadoukenWBTCLiquidityFetcher() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching WBTC/ETH/CKB liquidity at ${new Date()}`);
        pool = new web3.eth.Contract(hadoukenUSDPoolABI, hadoukenUSDPoolAddress);
        ampParameters = await pool.methods.getAmplificationParameter().call();
        ampFactor = Number(ampParameters["value"]) / Number(ampParameters["precision"]);
        vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        liquidity = await vault.methods.getPoolTokens('0xd0b29dda7bf9ba85f975170e31040a959e4c59e1000100000000000000000004').call();
        formattedOutput = {}
        console.log(liquidity)
        // const UsdcUsdt = liquidity['0'][0] + '_' + liquidity['0'][1];
        // const UsdtUsdc = liquidity['0'][1] + '_' + liquidity['0'][0];
        const WbtcEth = '0x82455018f2c32943b3f12f4e59d0da2faf2257ef_0x9e858a7aaedf9fdb1026ab1f77f627be2791e98a'
        const EthWbtc = '0x9e858a7aaedf9fdb1026ab1f77f627be2791e98a_0x82455018f2c32943b3f12f4e59d0da2faf2257ef'
        const EthCkb = '0x9e858a7aaedf9fdb1026ab1f77f627be2791e98a_0x7538c85cae4e4673253ffd2568c1f1b48a71558a'
        const CkbEth = '0x7538c85cae4e4673253ffd2568c1f1b48a71558a_0x9e858a7aaedf9fdb1026ab1f77f627be2791e98a'
        const CkbWbtc = '0x7538c85cae4e4673253ffd2568c1f1b48a71558a_0x82455018f2c32943b3f12f4e59d0da2faf2257ef'
        const WbtcCkb = '0x82455018f2c32943b3f12f4e59d0da2faf2257ef_0x7538c85cae4e4673253ffd2568c1f1b48a71558a'
        const WbtcLqty = liquidity['1'][1].slice(0, -2);
        const EthLqty = liquidity['1'][2].slice(0, -12);
        const CkbLqty = liquidity['1'][0].slice(0, -12);
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        
        formattedOutput[WbtcEth] = {
            token0: WbtcLqty,
            token1: EthLqty,
            ampFactor: ampFactor
        }
        formattedOutput[EthWbtc] ={
            token0: EthLqty,
            token1: WbtcLqty,
            ampFactor: ampFactor
        }
        formattedOutput[EthCkb] = {
            token0: EthLqty,
            token1: CkbLqty,
            ampFactor: ampFactor
        }
        formattedOutput[CkbEth] = {
            token0: CkbLqty,
            token1: EthLqty,
            ampFactor: ampFactor
        }
        formattedOutput[CkbWbtc] = {
            token0: CkbLqty,
            token1: WbtcLqty,
            ampFactor: ampFactor
        }
        formattedOutput[WbtcCkb] = {
            token0: WbtcLqty,
            token1: CkbLqty,
            ampFactor: ampFactor
        }
        console.log(formattedOutput);
        return formattedOutput;
        }
    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ended fetching WBTC/ETH/CKB liquidity at ${new Date()}`);
        console.log('============================================');
    }
 }

 hadoukenWBTCLiquidityFetcher();

 module.exports = {hadoukenUSDLiquidityFetcher}