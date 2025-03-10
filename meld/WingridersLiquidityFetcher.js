const fs = require('fs');
const wr = require('@wingriders/dex-blockfrost-adapter');
require('dotenv').config();
const addressMap = require('./lpmap.mainnet.20230103.json');
const { normalize } = require('../utils/TokenHelper');
const { tokens } = require('./Addresses');
const projectId = process.env.BLOCKFROST_PROJECTID;
const liquidityDirectory = './liquidity';


async function FetchWingrindersData() {
    try {
        console.log('============================================');
        console.log(`Starting Wingriders liquidity fetch at ${new Date()}`);
        if (!projectId) {
            console.error('Cannot read env variable BLOCKFROST_PROJECTID');
        }
        const adapter = new wr.WingRidersAdapter({
            projectId: projectId,
            lpAddressMap: addressMap,
        });
        const poolsObject = {
            json_time: Math.round(Date.now() / 1000)
        };

        for (let i = 0; i < tokens.length; i++) {
            const map = Object.entries(addressMap);
            for (let j = 0; j < map.length; j++) {
                const tokenToFetch = tokens[i];
                if (map[j][1].unitA === 'lovelace' && map[j][1].unitB === tokenToFetch.address) {
                    const tokenLP = map[j][1];
                    const lastFetched = await adapter.getLiquidityPoolState(tokenLP.unitA, tokenLP.unitB);
                    poolsObject[`${tokenToFetch.symbol}_ADA`] = {
                        reserveT0: normalize(lastFetched.quantityB, tokenToFetch.decimals),
                        reserveT1: normalize(lastFetched.quantityA, 6),
                    };
                    poolsObject[`ADA_${tokenToFetch.symbol}`] = {
                        reserveT0: normalize(lastFetched.quantityA, 6),
                        reserveT1: normalize(lastFetched.quantityB, tokenToFetch.decimals),
                    };
                }
            }
        }
        fs.writeFileSync(`${liquidityDirectory}/wingriders_liquidity.json`, JSON.stringify(poolsObject, null, 2));
        return true;
    }
    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ending Wingriders liquidity fetch at ${new Date()}`);
        console.log('============================================');
    }
}

// FetchWingrindersData();

module.exports = { FetchWingrindersData };