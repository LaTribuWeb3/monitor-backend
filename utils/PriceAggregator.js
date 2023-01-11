const fs = require('fs');
const { roundTo } = require('./NumberHelper');


/**
 * 
 * @param {number} dx variation of x
 * @param {number} x reserve of x
 * @param {number} y reserve of y
 * @returns 
 */
function calcDestQty(dx, x, y) {
    // (x + dx) * (y-dy) = xy
    // dy = y - xy/(x+dx)
    const z = x*y/(x+dx);

    return y - z;
}

/**
 * 
 * @param {string} srcToken the token to sell
 * @param {number} srcQty base quantity
 * @param {string} destToken the token to get
 * @param {string[]} allTokens list of tokens
 * @param {{[key:string]: {reserveT0: number, reserveT1: number}}} liquidityJson representing reserves in particular pool
 * must be formated like that:
 * key: token0_token1 and contains reserveT0 = reserve of token0, reserveT1 = reserve of token1. All number should be normalized
 * @returns {{bestQty: number, route: string}} best price obtainable
 */
function findBestQtyThroughPools(srcToken, srcQty, destToken, allTokens, liquidityDictionary) {
    if (srcToken ==  destToken) {
        // console.log(`findBestDestQty: [${srcToken} -> ${destToken}] same tokens, returning ${srcQty}`);
        return {bestQty: srcQty, route: srcToken};
    }
    if (allTokens.length == 0) {
        return {bestQty: 0, route: ''};
    }


    let route = srcToken;
    let bestDestQty = -1;
    allTokens.forEach(token => {
        let key = `${srcToken}_${token}`;
        if(!liquidityDictionary[key]) {
            // console.log(`findBestDestQty: [${srcToken} -> ${destToken}] ignoring ${key} as it's not in the liquidities`);
        }
        else {
            // console.log(`findBestDestQty: [${srcToken} -> ${destToken}] working on ${key} with tokens: ${allTokens.join(', ')}`);
            const x = liquidityDictionary[key].reserveT0;
            const y = liquidityDictionary[key].reserveT1;
            const newSrcToken = token;
            const newSrcQty = calcDestQty(srcQty, x, y);
            const newAllToken = allTokens.filter(_ => _.toLowerCase() != token.toLowerCase());
    
            const bestCandidate = findBestQtyThroughPools(newSrcToken, newSrcQty, destToken, newAllToken, liquidityDictionary);
            if (bestCandidate.bestQty > bestDestQty) {
                // console.log(`findBestDestQty: [${srcToken} -> ${destToken}] new best candidate: ${bestCandidate.bestQty}`);
                bestDestQty = bestCandidate.bestQty;
                if(route) {
                    route = srcToken + '->' + bestCandidate.route;
                } else {
                    route = bestCandidate.route;
                }
            }
        }
    });

    return {bestQty: bestDestQty, route: route};
}

module.exports = { findBestQtyThroughPools };


/**
 * must be called like that: 'node PriceAggregator.js 100 ADA MELD'
 * it will get the price for 100 ada to X meld
 */
// function test() {
//     const allTokens = ['C3', 'WRT', 'Min', 'MELD', 'iUSD', 'INDY', 'HOSKY', 'COPI', 'ADA'];
//     const liquidityDictionary = JSON.parse(fs.readFileSync('liq.json'));
//     const quantity = Number(process.argv[2]);
//     const from = process.argv[3];
//     const dest = process.argv[4];
//     const bestForOne = findBestQtyThroughPools(from, 1, dest, allTokens, liquidityDictionary);
//     const best = findBestQtyThroughPools(from, quantity, dest, allTokens, liquidityDictionary);
//     const pricePerToken = best.bestQty/quantity;
//     console.log(`${quantity} ${from} = ${best.bestQty} ${dest} through route: ${best.route}. Slippage: ${Math.abs(roundTo((pricePerToken / bestForOne.bestQty - 1) * 100, 2))}%`);
// }

// test();
