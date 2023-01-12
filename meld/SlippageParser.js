const fs = require('fs');
const { roundTo } = require('../utils/NumberHelper');
const { findBestQtyThroughPools } = require('../utils/PriceAggregator');
const liquidityDirectory = './liquidity';
const { tokens } = require('./Addresses');

/**
 * 
 * @param {string} fromToken 
 * @param {string} toToken 
 * @param {number} targetSlippage 
 * @param {string[]} allTokens 
 * @param {{[key:string]: {reserveT0: number, reserveT1: number}}} liquidityDictionary 
 */
function getLiquidityForSlippageWithBinarySearch(fromToken, toToken, targetSlippage, allTokens, liquidityDictionary) {
    const baseQty = findBestQtyThroughPools(fromToken, 1, toToken, allTokens, liquidityDictionary);
    const basePrice = baseQty.bestQty;
    console.log(`${fromToken}->${toToken}: base price of ${fromToken} = ${basePrice} ${toToken}`);

    let minQty = undefined;
    let maxQty = undefined;
    let tryQty = 10;
    let lastTry = 0;
    let foundSlippage = 0;
    let route = '';
    const stopCondition = 0.001; // define when we stop the loop, when minQty and maxQty are less than this value

    // eslint-disable-next-line no-constant-condition
    while(true) {
        // stops when we have found the min and max qty and when the difference
        // between max and min is less than stopGap value
        if(minQty && maxQty && (maxQty - minQty) < stopCondition) {
            break;
        }

        const tryResult = findBestQtyThroughPools(fromToken, tryQty, toToken, allTokens, liquidityDictionary);
        // console.log(`${fromToken}->${toToken}: route for ${tryQty} ${fromToken} is ${tryResult.route}`);
        route = tryResult.route;
        const priceForTryQuantity = tryResult.bestQty/tryQty;
        const slippage = priceForTryQuantity / basePrice - 1;
        const slippageBeautified = Math.abs(roundTo(slippage * 100, 2));
        console.log(`${fromToken}->${toToken}: [${minQty || 0} - ${maxQty || '+∞'}] | price for ${tryQty} ${fromToken} is ${priceForTryQuantity} ${fromToken}/${toToken}, slippage: ${slippageBeautified}%`);

        lastTry = tryQty;
        foundSlippage = 1 + Math.abs(slippage);

        if(Math.abs(slippage) > targetSlippage) {
            // if slippage too high, next try should be lower
            maxQty = tryQty;

            if(minQty) {
                tryQty = tryQty - ((maxQty - minQty) / 2);
            } else {
                tryQty = tryQty / 2;
            }

        } else {
            // if slippage too low, next try should be higher
            minQty = tryQty;

            if(maxQty) {
                tryQty = tryQty + ((maxQty - minQty) / 2);

            } else {
                tryQty = tryQty * 2;
            }
        }

        // console.log(`${fromToken}->${toToken}: quantity changed from ${lastTry} to ${tryQty} ${fromToken}`);
    }

    return { quantity: lastTry, slippage: foundSlippage, route: route };
}

function createAggregatedLiquidityData() {
    if (!fs.existsSync(`${liquidityDirectory}/minswap_liquidity.json`) || !fs.existsSync(`${liquidityDirectory}/wingriders_liquidity.json`)) {
        throw new Error('Cannot read data files');
    }
    const aggregatedData = {};
    const minswapJson = fs.readFileSync(`${liquidityDirectory}/minswap_liquidity.json`);
    const minswapData = JSON.parse(minswapJson);
    const wingridersJson = fs.readFileSync(`${liquidityDirectory}/wingriders_liquidity.json`);
    const wingridersData = JSON.parse(wingridersJson);

    const minAcceptableTime = Date.now() / 1000 - 3 * 60 * 60;
    if (minswapData.json_time < minAcceptableTime) {
        throw new Error('minswapData is too old');
    } if (wingridersData.json_time < minAcceptableTime) {
        throw new Error('wingridersData is too old');
    }

    for (const entry in minswapData) {
        if (entry !== 'json_time') {
            aggregatedData[entry] = {
                reserveT0: minswapData[entry]['reserveT0'] + wingridersData[entry]['reserveT0'],
                reserveT1: minswapData[entry]['reserveT1'] + wingridersData[entry]['reserveT1']
            };
        }
    }
    fs.writeFileSync(`${liquidityDirectory}/aggregated_liquidity.json`, JSON.stringify(aggregatedData, null, 2));
    return aggregatedData;
}

async function ParseLiquidityAndSlippage() {
    try {
        console.log('============================================');
        console.log(`Starting Slippage Parser - aggregating data ${new Date()}`);
        
        const targetSlippage = 10/100;
        const liquidityDictionary = createAggregatedLiquidityData();//  JSON.parse(fs.readFileSync('liquidity/minswap_liquidity.json'));// 
        const allTokens = tokens.map(_ => _.symbol);
        allTokens.push('ADA'); // add ada as all available reverse are with ada as the second token

        const slippageObj = {
            'json_time': Math.floor(Date.now() / 1000),
        };

        const dexPriceObj = {
            'json_time': Math.floor(Date.now() / 1000),
        };

        for(let i = 0; i < allTokens.length; i++) {
            const fromToken = allTokens[i];
            
            // find the current price of the from in iUSD
            const fromTokenPriceIniUSD = findBestQtyThroughPools(fromToken, 1, 'iUSD', allTokens, liquidityDictionary);
            dexPriceObj[fromToken] = {
                priceUSD: fromTokenPriceIniUSD.bestQty,
            };

            slippageObj[fromToken] = {};
            for(let j = 0; j < allTokens.length; j++) {
                const toToken = allTokens[j];
                if(fromToken === toToken) {
                    continue;
                }

                console.log(`Searching quantity of ${fromToken} -> ${toToken} for ${targetSlippage * 100}% slippage`);
                const liquidityData = getLiquidityForSlippageWithBinarySearch(fromToken, toToken, targetSlippage, allTokens, liquidityDictionary);
                // console.log('liquidityData', liquidityData);

                slippageObj[fromToken][toToken] = {
                    volume: liquidityData.quantity * fromTokenPriceIniUSD.bestQty,
                    llc: liquidityData.slippage,
                    route: liquidityData.route
                };
            }
        }

        fs.writeFileSync(`${liquidityDirectory}/usd_volume_for_slippage.json`, JSON.stringify(slippageObj, null, 2));
        fs.writeFileSync(`${liquidityDirectory}/dex_price.json`, JSON.stringify(dexPriceObj, null, 2));
        return true;
    }
    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ending Slippage Parser - data aggregated at ${new Date()}`);
        console.log('============================================');
    }
}

// ParseLiquidityAndSlippage();

module.exports = { ParseLiquidityAndSlippage };