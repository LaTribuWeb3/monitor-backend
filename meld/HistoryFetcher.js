const { BlockfrostAdapter, NetworkId } = require('@minswap/blockfrost-adapter');
const fs = require('fs');
const { normalize } = require('../utils/TokenHelper');
require('dotenv').config();
const { tokenPoolToFetch } = require('./Addresses');

const projectId = process.env.BLOCKFROST_PROJECTID;

/**
 * 
 * @param {string} filename 
 * @returns {{blockHeight: number, timestamp: number, reserveA: number, reserveB: number, price: number}[]}
 */
function getAlreadyFetchedData(filename) {
    if(fs.existsSync(filename)) {
        const lines = fs.readFileSync(filename, 'utf-8').split(/\r?\n/).slice(1);
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
 * @param {string} blockfrostProjectId 
 * @param {string} tokenSymbol 
 * @param {number} tokenDecimals 
 * @param {string} poolId 
 */
async function fetchMinswapHistory(blockfrostProjectId, tokenSymbol, tokenDecimals, poolId) {
    const api = new BlockfrostAdapter({
        projectId: blockfrostProjectId,
        networkId: NetworkId.MAINNET,
    });

    const stopTimestamp = Date.now() / 1000 - 3 * 30 * 24 * 60 * 60; // 3 months ago
    var dateMin = new Date(stopTimestamp * 1000);
    
    let mustStop = false;
    let page = 1;

    const filename = `${tokenSymbol}-ADA.csv`;
    // find the last data fetched and keep only values more recent than stopTimestamp
    const fetchedData = getAlreadyFetchedData(filename).filter(_ => _.timestamp > stopTimestamp);

    let  lastFetchedData = undefined;
    if(fetchedData.length > 0) {
        lastFetchedData = fetchedData.reduce((prev, current) => (prev.blockHeight > current.blockHeight) ? prev : current);
        console.log(`[${tokenSymbol}/ADA]: Will stop at blockHeight: ${lastFetchedData.blockHeight}`);
    }

    while(!mustStop) {
        console.log(`[${tokenSymbol}/ADA]: Getting pool history for page ${page}`);
        const history = await api.getPoolHistory({ id: poolId, count: 100, order: 'desc', page: page++ });
        for (const historyPoint of history) {
            
            if(lastFetchedData && historyPoint.blockHeight == lastFetchedData.blockHeight) {
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


            const [price0, price1] = await api.getPoolPrice({
                pool,
                decimalsA: 6,
                decimalsB: 6,
            });
            
            console.log(`[${tokenSymbol}/ADA]: Block:${historyPoint.blockHeight}: ${price0} ADA/${tokenSymbol}, ${price1} ${tokenSymbol}/ADA`);
            fetchedData.push({
                blockHeight: historyPoint.blockHeight,
                price: price1,
                reserveA: normalize(pool.reserveA.toString(), 6), // reserve A is always ADA ?
                reserveB: normalize(pool.reserveB.toString(), tokenDecimals),
                timestamp: Math.round(historyPoint.time.getTime() / 1000)
            });
        }
    }

    // here, 'fetchedData' contains all the data fetched, order it by blockheight and save it as csv
    fetchedData.sort((a, b) => a.blockHeight - b.blockHeight);
    fs.writeFileSync(filename, 'Block number, timestamp, reserve A, reserve B, price\n');
    fs.appendFileSync(filename, fetchedData.map(_ => `${_.blockHeight},${_.timestamp},${_.reserveA},${_.reserveB},${_.price}`).join('\n'));
}

/**
 * @notice this is the main entrypoint
 */
async function HistoryFetcher() {
    if(!projectId) {
        console.error('Cannot work without blockfrost project id');
    }
    for(let i = 0; i < tokenPoolToFetch.length; i++) {
        const tokenToFetch = tokenPoolToFetch[i];
        if(!tokenToFetch.poolId) {
            console.log(`Not working on ${tokenToFetch.symbol} because no pool id in config`);
            continue;
        }

        console.log(`Fetching history for ${tokenToFetch.symbol}/ADA`);
        await fetchMinswapHistory(projectId, tokenToFetch.symbol, 6, tokenToFetch.poolId);
    }
}

HistoryFetcher();