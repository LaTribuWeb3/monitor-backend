const { BlockfrostAdapter, NetworkId } = require('@minswap/blockfrost-adapter');
const fs = require('fs');
const { normalize } = require('../utils/TokenHelper');
require('dotenv').config();
const { tokens } = require('./Addresses');

const historySrcDirectory = './history-src';
const liquidityDirectory = './liquidity';


/**
 * @notice Read the fetched data from CSV and return it as proper array
 * @dev this allow to not refetch 3 months of data each day, which is time consuming
 * @param {string} filename 
 * @returns {{blockHeight: number, timestamp: number, reserveA: number, reserveB: number, price: number}[]}
 */
function getAlreadyFetchedData(fullFilename) {
    if(fs.existsSync(fullFilename)) {
        const lines = fs.readFileSync(fullFilename, 'utf-8').split(/\r?\n/).slice(1); // slice 1 to remove headers line
        const alreadyFetchedData = [];
        lines.forEach(_ => {
            const splitted = _.split(',');
            alreadyFetchedData.push({
                blockHeight: Number(splitted[0]),
                timestamp:  Number(splitted[1]),
                reserveA:  Number(splitted[2]),
                reserveB:  Number(splitted[3]),
                price:  Number(splitted[4]),
            });
        });

        return alreadyFetchedData;
    } else {
        return [];
    }
}

/**
 * @notice fetch 3 month of price history from minswap
 * @dev only work on pool with ADA as reserveA !!
 * @param {string} blockfrostProjectId 
 * @param {string} tokenSymbol 
 * @param {number} tokenDecimals 
 * @param {string} poolId 
 * @param {number} monthsToFetch 
 * @returns {Promise<{blockHeight: number, timestamp: number, reserveA: number, reserveB: number, price: number}>} last fetched value
 */
async function fetchMinswapHistory(blockfrostProjectId, tokenSymbol, tokenDecimals, poolId, monthsToFetch=3) {
    const api = new BlockfrostAdapter({
        projectId: blockfrostProjectId,
        networkId: NetworkId.MAINNET,
    });

    const stopTimestamp = Date.now() / 1000 - monthsToFetch * 30 * 24 * 60 * 60; // 3 months ago
    var dateMin = new Date(stopTimestamp * 1000);
    
    let mustStop = false;
    let page = 1;

    const fullFilename = historySrcDirectory + `/${tokenSymbol}-ADA.csv`;
    // find the last data fetched and keep only values more recent than stopTimestamp
    const fetchedData = getAlreadyFetchedData(fullFilename).filter(_ => _.timestamp > stopTimestamp);

    let  lastFetchedData = undefined;
    if(fetchedData.length > 0) {
        lastFetchedData = fetchedData.reduce((prev, current) => (prev.blockHeight > current.blockHeight) ? prev : current);
        console.log(`[${tokenSymbol}/ADA]: Will stop at blockHeight: ${lastFetchedData.blockHeight}`);
    }

    while(!mustStop) {
        console.log(`[${tokenSymbol}/ADA]: Getting pool history for page ${page}`);
        const history = await api.getPoolHistory({ id: poolId, count: 100, order: 'desc', page: page++ });
        if(!mustStop && history.length == 0) {
            console.log(`[${tokenSymbol}/ADA]: Could not find any more history`);
            break;
        }

        for (const historyPoint of history) {
            
            if(lastFetchedData && historyPoint.blockHeight <= lastFetchedData.blockHeight) {
                console.log(`[${tokenSymbol}/ADA]: Stopping because history point has already been fetched: ${historyPoint.blockHeight}`);
                mustStop = true;
                break;
            }

            if(dateMin > historyPoint.time) {
                console.log(`[${tokenSymbol}/ADA]: Stopping because history point too old: ${historyPoint.time}`);
                mustStop = true;
                break;
            }
            const pool = await api.getPoolInTx({ txHash: historyPoint.txHash });
            if (!pool) {
                throw new Error('pool not found');
            }

            if(pool.assetA != 'lovelace') {
                throw new Error('Can only work on pool where assetA is ADA');
            }


            const [price0, price1] = await api.getPoolPrice({
                pool,
                decimalsA: 6, // ADA
                decimalsB: tokenDecimals,
            });
            
            console.log(`[${tokenSymbol}/ADA]: Block:${historyPoint.blockHeight}: ${price0} ADA/${tokenSymbol}, ${price1} ${tokenSymbol}/ADA`);
            fetchedData.push({
                blockHeight: historyPoint.blockHeight,
                price: price0,
                reserveA: normalize(pool.reserveA.toString(), 6), // reserve A must always be ADA
                reserveB: normalize(pool.reserveB.toString(), tokenDecimals),
                timestamp: Math.round(historyPoint.time.getTime() / 1000)
            });
        }
    }

    // here, 'fetchedData' contains all the data fetched, order it by blockheight and save it as csv
    fetchedData.sort((a, b) => a.blockHeight - b.blockHeight);
    fs.writeFileSync(fullFilename, `Block number,timestamp,reserve ADA,reserve ${tokenSymbol},price (ADA/${tokenSymbol})\n`);
    fs.appendFileSync(fullFilename, fetchedData.map(_ => `${_.blockHeight},${_.timestamp},${_.reserveA},${_.reserveB},${_.price}`).join('\n'));

    // return the last fetched value
    return fetchedData[fetchedData.length-1];
}

/**
 * @notice this is the main entrypoint
 * Fetches price history going back 3 months and outputs a liquidity json
 */
async function FetchMinswapData() {
    try {
        console.log('============================================');
        console.log(`Starting MELD history fetch at ${new Date()}`);
        const projectId = process.env.BLOCKFROST_PROJECTID;

        if(!projectId) {
            console.error('Cannot read env variable BLOCKFROST_PROJECTID');
        }
        if(!fs.existsSync(historySrcDirectory)) {
            fs.mkdirSync(historySrcDirectory);
        }
        if(!fs.existsSync(liquidityDirectory)) {
            fs.mkdirSync(liquidityDirectory);
        }

        const poolsObject = {
            json_time: Math.round(Date.now() / 1000)
        };

        for(let i = 0; i < tokens.length; i++) {
            const tokenToFetch = tokens[i];
            if(!tokenToFetch.poolId) {
                console.log(`Not working on ${tokenToFetch.symbol} because no pool id in config`);
                continue;
            }

            console.log(`Fetching history for ${tokenToFetch.symbol}/ADA`);
            const lastFetched = await fetchMinswapHistory(projectId, tokenToFetch.symbol, tokenToFetch.decimals, tokenToFetch.poolId);
            poolsObject[`${tokenToFetch.symbol}_ADA`] = {
                reserveT0: lastFetched.reserveB,
                reserveT1: lastFetched.reserveA,
            };
            poolsObject[`ADA_${tokenToFetch.symbol}`] = {
                reserveT0: lastFetched.reserveA,
                reserveT1: lastFetched.reserveB,
            };

        }

        fs.writeFileSync(`${liquidityDirectory}/minswap_liquidity.json`, JSON.stringify(poolsObject, null, 2));
        return true;
    }
    catch(e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ending MELD history fetch at ${new Date()}`);
        console.log('============================================');
    }
}

// FetchMinswapData();

module.exports = { FetchMinswapData };

