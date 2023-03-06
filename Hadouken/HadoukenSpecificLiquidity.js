const Addresses = require("./Addresses.js")
const Web3 = require('web3')
const fs = require('fs');
const {hadoukenVaultAbi, linearPoolABI, hadoukenVaultAddress, hadoukenUSDPoolABI, hadoukenUSDPoolAddress } = require("./Addresses.js");

async function hadoukenUSDLiquidityFetcher() {
    const web3 = new Web3("https://v1.mainnet.godwoken.io/rpc");
    try {
        console.log('============================================');
        console.log(`Started fetching USDT/USDC liquidity at ${new Date()}`);
        const pool = new web3.eth.Contract(hadoukenUSDPoolABI, hadoukenUSDPoolAddress);
        const ampParameters = await pool.methods.getAmplificationParameter().call();
        const ampFactor = Number(ampParameters["value"]) / Number(ampParameters["precision"]);
        const vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);

        const USDCAddress = '0x186181e225dc1Ad85a4A94164232bD261e351C33';
        const linearUSDCPoolAddress = '0x149916d7128c36bbcebd04f794217baf51085fb9';
        const USDCPoolContract = new web3.eth.Contract(linearPoolABI, linearUSDCPoolAddress);
        const USDCPoolId = await USDCPoolContract.methods.getPoolId().call();
        const LinearUSDCliquidity = await vault.methods.getPoolTokens(USDCPoolId).call();
        const indexOfUSDC = LinearUSDCliquidity.tokens.indexOf(USDCAddress);
        const balanceOfUSDC = LinearUSDCliquidity.balances[indexOfUSDC];
        console.log('balanceOfUSDC', balanceOfUSDC);

        const USDTAddress = '0x8E019acb11C7d17c26D334901fA2ac41C1f44d50';
        const linearUSDTPoolAddress = '0xa0430f122fb7e4f6f509c9cb664912c2f01db3e2';
        const USDTPoolContract = new web3.eth.Contract(linearPoolABI, linearUSDTPoolAddress);
        const USDTPoolId = await USDTPoolContract.methods.getPoolId().call();
        const LinearUSDTliquidity = await vault.methods.getPoolTokens(USDTPoolId).call();
        const indexOfUSDT = LinearUSDTliquidity.tokens.indexOf(USDTAddress);
        const balanceOfUSDT = LinearUSDTliquidity.balances[indexOfUSDT];
        console.log('balanceOfUSDT', balanceOfUSDT);


        formattedOutput = {}
        const UsdcUsdt = `${USDCAddress}_${USDTAddress}`;
        const UsdtUsdc = `${USDTAddress}_${USDCAddress}`;
        formattedOutput['lastUpdate'] = Math.floor(Date.now() / 1000);
        formattedOutput[UsdcUsdt] = {
            token0: balanceOfUSDC,
            token1: balanceOfUSDT,
            ampFactor: ampFactor
        };
        formattedOutput[UsdtUsdc] = {
            token0: balanceOfUSDT,
            token1: balanceOfUSDC,
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
        const pool = new web3.eth.Contract(hadoukenUSDPoolABI, hadoukenUSDPoolAddress);
        const ampParameters = await pool.methods.getAmplificationParameter().call();
        const ampFactor = Number(ampParameters["value"]) / Number(ampParameters["precision"]);
        const vault = new web3.eth.Contract(hadoukenVaultAbi, hadoukenVaultAddress);
        const liquidity = await vault.methods.getPoolTokens('0xd0b29dda7bf9ba85f975170e31040a959e4c59e1000100000000000000000004').call();
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

//  hadoukenUSDLiquidityFetcher();

 module.exports = {hadoukenUSDLiquidityFetcher, hadoukenWBTCLiquidityFetcher}