const Addresses = require("./Addresses.js")
const Web3 = require('web3')
const fs = require('fs');
const {hadoukenVaultAbi, linearPoolABI, hadoukenVaultAddress, hadoukenUSDPoolABI, hadoukenUSDPoolAddress } = require("./Addresses.js");
const { retry } = require("../utils/CommonFunctions.js");
const { BigNumber } = require("ethers");
const USDCAddress = '0x186181e225dc1Ad85a4A94164232bD261e351C33';
const boostedUSDCAddress = "0x149916D7128C36bbcebD04F794217Baf51085fB9"

const USDTAddress = '0x8E019acb11C7d17c26D334901fA2ac41C1f44d50';
const boostedUSDTAddress = "0xa0430F122fb7E4F6F509c9cb664912C2f01db3e2"

const BoostedUSDPoolId = '0xaf9d4028272f750dd2d028990fd664dc223479b1000000000000000000000013';
async function hadoukenUSDLiquidityFetcher() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching USDT/USDC liquidity at ${new Date()}`);
        const pool = new web3.eth.Contract(hadoukenUSDPoolABI, hadoukenUSDPoolAddress);
        const ampParameters = await retry(pool.methods.getAmplificationParameter().call, []);
        const ampFactor = Number(ampParameters["value"]) / Number(ampParameters["precision"]);
        const vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);

        const liquidity = await retry(vault.methods.getPoolTokens(BoostedUSDPoolId).call, []);

        // we will consider boostedUSDC and boostedUSDT to be USDC and USDT
        const indexOfBoostedUSDC = liquidity.tokens.indexOf(boostedUSDCAddress);
        const indexOfBoostedUSDT = liquidity.tokens.indexOf(boostedUSDTAddress);

        const balanceOfBoostedUSDC = liquidity.balances[indexOfBoostedUSDC];
        const balanceOfBoostedUSDT = liquidity.balances[indexOfBoostedUSDT];
        
        // boosted liquidity have 18 decimals, need to short it to 6 like USDC and USDT,
        // so we divide by 1e12 (18 - 6)
        const _1e12 = BigNumber.from(10).pow(12);
        const usdcBalance = BigNumber.from(balanceOfBoostedUSDC).div(_1e12).toString()
        console.log(usdcBalance)
        const usdtBalance = BigNumber.from(balanceOfBoostedUSDT).div(_1e12).toString()
        console.log(usdtBalance)

        formattedOutput = {}
        const UsdcUsdt = `${USDCAddress}_${USDTAddress}`;
        const UsdtUsdc = `${USDTAddress}_${USDCAddress}`;
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        formattedOutput[UsdcUsdt] = {
            token0: usdcBalance,
            token1: usdtBalance,
            ampFactor: ampFactor
        };
        formattedOutput[UsdtUsdc] = {
            token0: usdtBalance,
            token1: usdcBalance,
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
        const vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        const liquidity = await retry(vault.methods.getPoolTokens('0xd0b29dda7bf9ba85f975170e31040a959e4c59e1000100000000000000000004').call, []);
        const formattedOutput = {}

        const WBTCAddress = '0x82455018F2c32943b3f12F4e59D0DA2FAf2257Ef';
        const ETHAddress = '0x9E858A7aAEDf9FDB1026Ab1f77f627be2791e98A';
        const CKBAddress = '0x7538C85caE4E4673253fFd2568c1F1b48A71558a';

        const WbtcEth = `${WBTCAddress}_${ETHAddress}`;
        const EthWbtc = `${ETHAddress}_${WBTCAddress}`;
        const EthCkb = `${ETHAddress}_${CKBAddress}`;
        const CkbEth = `${CKBAddress}_${ETHAddress}`;
        const CkbWbtc = `${CKBAddress}_${WBTCAddress}`;
        const WbtcCkb = `${WBTCAddress}_${CKBAddress}`;

        const indexOfWBTC = liquidity.tokens.indexOf(WBTCAddress);
        const indexOfETH = liquidity.tokens.indexOf(ETHAddress);
        const indexOfCKB = liquidity.tokens.indexOf(CKBAddress);

        const WbtcLqty = liquidity.balances[indexOfWBTC];
        const EthLqty = liquidity.balances[indexOfETH];
        const CkbLqty = liquidity.balances[indexOfCKB];

        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        
        formattedOutput[WbtcEth] = {
            token0: WbtcLqty,
            token1: EthLqty,
        }
        formattedOutput[EthWbtc] ={
            token0: EthLqty,
            token1: WbtcLqty,
        }
        formattedOutput[EthCkb] = {
            token0: EthLqty,
            token1: CkbLqty,
        }
        formattedOutput[CkbEth] = {
            token0: CkbLqty,
            token1: EthLqty,
        }
        formattedOutput[CkbWbtc] = {
            token0: CkbLqty,
            token1: WbtcLqty,
        }
        formattedOutput[WbtcCkb] = {
            token0: WbtcLqty,
            token1: CkbLqty,
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

// hadoukenUSDLiquidityFetcher();

 module.exports = {hadoukenUSDLiquidityFetcher, hadoukenWBTCLiquidityFetcher}