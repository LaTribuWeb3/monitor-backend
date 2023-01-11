const meldData = require('./dummy_user_data2.json');
const fs = require('fs');
const { tokens } = require('./Addresses');
const { BigNumber } = require('ethers');
const { BNToHex } = require('../utils/TokenHelper');
require('dotenv').config();

function getMarkets() {
    const markets = [];
    const marketMap = {};
    for (const [key, assetStateMap] of Object.entries(meldData.qrdGlobalState.gsAssetStateMap)) {
        const assetClass = assetStateMap.asRiskParameters.rpAssetClassData;
        let market = 'lovelace';
        if (assetClass.toLowerCase() != 'lovelace') {
            // "rpAssetClassData": "87ecaf019a342a7b3ec6227213e0c523d22bfab4315e5103909c0e85.4d454c44",
            // here we need to only keep the token name, which is the value after the '.'
            market = assetClass.split('.')[1];
        }

        markets.push(market);
        marketMap[key] = market;

    }

    return { markets: markets, marketMap: marketMap };
}

/**
 * @param {string[]} markets 
 */
function getLiquidationIncentives(markets) {
    const liquidationIncentives = {};
    markets.forEach(m => liquidationIncentives[m] = (1 + meldData.qrdGlobalState.gsLiquidatorIncentive).toString());
    return liquidationIncentives;
}

/**
 * 
 * @param {{[marketId: string]: string} marketMap 
 */
function getCollateralFactors(marketMap) {
    const collateralFactors = {};
    for (const [tokenId, marketName] of Object.entries(marketMap)) {
        const assetStateMap = meldData.qrdGlobalState.gsAssetStateMap[tokenId];
        collateralFactors[marketName] = assetStateMap.asRiskParameters.rpLiquidationThreshold.toString();
    }

    return collateralFactors;
}

/**
 * 
 * @param {{[marketId: string]: string} marketMap 
 */
function getBorrowCaps(marketMap) {
    const borrowCaps = {};
    for (const [tokenId, marketName] of Object.entries(marketMap)) {
        const assetStateMap = meldData.qrdGlobalState.gsAssetStateMap[tokenId];
        borrowCaps[marketName] = assetStateMap.asRiskParameters.rpBorrowCap.toString();
    }

    return borrowCaps;
}

/**
 * 
 * @param {{[marketId: string]: string} marketMap 
 */
function getCollateralCaps(marketMap) {
    const collateralCaps = {};
    for (const [tokenId, marketName] of Object.entries(marketMap)) {
        const assetStateMap = meldData.qrdGlobalState.gsAssetStateMap[tokenId];
        collateralCaps[marketName] = assetStateMap.asRiskParameters.rpSupplyCap.toString();
    }

    return collateralCaps;
}

/**
 * 
 * @param {{[marketId: string]: string} marketMap 
 */
function getTotalBorrows(marketMap) {
    const totalBorrows = {};
    for (const [tokenId, marketName] of Object.entries(marketMap)) {
        const assetStateMap = meldData.qrdGlobalState.gsAssetStateMap[tokenId];
        totalBorrows[marketName] = BNToHex(assetStateMap.asTotalBorrow.toString());
    }

    return totalBorrows;
}


/**
 * @param {{[marketId: string]: string} marketMap 
 * @param {{[marketId: string]: number} decimals
 */
// eslint-disable-next-line no-unused-vars
function getPrices(marketMap, decimals) {
    const prices = {};
    for (const [tokenId, marketName] of Object.entries(marketMap)) {
        const assetState = meldData.qrdGlobalState.gsAssetStateMap[tokenId];
        const meldPrice = assetState.asPrice; // in USD
        console.log('meldPrice', meldPrice);
        const meldPriceWith6Decimals = Math.round(meldPrice * 1e6);
        console.log('meldPriceWith6Decimals', meldPriceWith6Decimals);
        const meldPrice18Decimals = BigNumber.from(meldPriceWith6Decimals).mul(BigNumber.from(10).pow(12));

        console.log('meldPrice18Decimals', meldPrice18Decimals.toString());

        // now we must pad with a number of zeroes = 18 - decimals
        // for most of the cardano tokens it will add 18 - 6 = 12 zeroes
        const numberOfZeroToAdd = 18 - getDecimalForTokenHex(marketName);
        const priceWithValidNumberOfZeroes = meldPrice18Decimals.toString() + ''.padEnd(numberOfZeroToAdd, '0');
        console.log('priceWithValidNumberOfZeroes', priceWithValidNumberOfZeroes);
        prices[marketName] = BNToHex(priceWithValidNumberOfZeroes);
    }

    return prices;
}

/**
 * 
 * @param {{[marketId: string]: string} marketMap 
 */
function getTotalCollaterals(marketMap) {
    const tempCollaterals = {}; // used for sum
    for (let i = 0; i < meldData.qrdAccountList.length; i++) {
        const meldUser = meldData.qrdAccountList[i];
        for (let j = 0; j < meldUser.asCollaterals.length; j++) {
            const tokenId = meldUser.asCollaterals[j];
            const marketName = marketMap[tokenId];
            if (tempCollaterals[marketName] == undefined) {
                tempCollaterals[marketName] = meldUser.asDeposits[tokenId]['avAmount'];
            } else {
                tempCollaterals[marketName] += meldUser.asDeposits[tokenId]['avAmount'];
            }
        }
    }

    const totalCollaterals = {};
    for (const marketName of Object.values(marketMap)) {
        const tempCollateral = tempCollaterals[marketName];
        if (tempCollateral == undefined) {
            totalCollaterals[marketName] = '0';
        } else {
            totalCollaterals[marketName] = BNToHex(tempCollateral.toString());
        }
    }

    return totalCollaterals;
}

/**
 * 
 * @param {string[]} markets 
 * @param {{[marketId: string]: string} marketMap 
 */
function getUsers(markets, marketMap) {
    const users = {};
    for (let i = 0; i < meldData.qrdAccountList.length; i++) {
        const meldUser = meldData.qrdAccountList[i];
        const userBorrow = {};
        const userCollateral = {};
        let hasAnyBorrowOrCollateral = false;
        for (const [tokenId, marketName] of Object.entries(marketMap)) {
            if (meldUser.asBorrows[tokenId]) {
                userBorrow[marketName] = BNToHex(meldUser.asBorrows[tokenId]['avAmount'].toString());
                hasAnyBorrowOrCollateral = true;
            } else {
                userBorrow[marketName] = '0';
            }

            if (meldUser.asCollaterals.includes(Number(tokenId))) {
                userCollateral[marketName] = BNToHex(meldUser.asDeposits[tokenId]['avAmount'].toString());
                hasAnyBorrowOrCollateral = true;
            } else {
                userCollateral[marketName] = '0';
            }
        }

        if (hasAnyBorrowOrCollateral) {
            users[meldUser.adUserNft] = {
                succ: true,
                assets: markets,
                borrowBalances: userBorrow,
                collateralBalances: userCollateral,
            };
        }
    }



    return users;
}

/**
 * @param {string[]} markets 
 */
function getDecimals(markets) {
    const tokenDecimals = {};
    markets.forEach(m => tokenDecimals[m] = getDecimalForTokenHex(m));
    return tokenDecimals;
}

function getDecimalForTokenHex(tokenHexKey) {
    let decimals = 6; // default for ADA
    if(tokenHexKey != 'lovelace') {
        const foundConfToken = tokens.find(t => t.hexKey.toLowerCase() == tokenHexKey.toLowerCase());
        if (!foundConfToken) {
            throw new Error('Cannot find symbol in configuration for hexKey: ' + tokenHexKey);
        }
        decimals = foundConfToken.decimals;
    }

    return decimals;
}

function getSymbolForTokenHex(tokenHexKey) {    
    if (tokenHexKey== 'lovelace') {
        return 'ADA';
    } else {
        // find the token with the hex key
        const foundConfToken = tokens.find(t => t.hexKey.toLowerCase() == tokenHexKey.toLowerCase());
        if (foundConfToken) {
            return foundConfToken.symbol;
        } else {
            throw new Error('Cannot find symbol in configuration for hexKey: ' + tokenHexKey);
        }
    }
}

/**
 * 
 * @param {string[]} markets 
 */
function getNames(markets) {
    const names = {};
    markets.forEach(m => names[m] = getSymbolForTokenHex(m));
    return names;
}

async function TranslateMeldData() {
    // get markets
    const { markets, marketMap } = getMarkets();
    console.log('markets', markets);
    console.log('marketMap', marketMap);

    // create a marketMap for "token id" in the json (0, 1, 2 ...) to market (lovelace, 4d454c44, etc)
    // get prices
    const prices = getPrices(marketMap);
    console.log('prices', prices);

    // get liquidation incentives
    const liquidationIncentives = getLiquidationIncentives(markets);
    console.log('liquidationIncentives', liquidationIncentives);

    // get collateral factors
    const collateralFactors = getCollateralFactors(marketMap);
    console.log('collateralFactors', collateralFactors);

    // get names
    const names = getNames(markets);
    console.log('names', names);

    // get borrowCaps
    const borrowCaps = getBorrowCaps(marketMap);
    console.log('borrowCaps', borrowCaps);

    // get collateralCaps
    const collateralCaps = getCollateralCaps(marketMap);
    console.log('collateralCaps', collateralCaps);

    // get decimals
    const decimals = getDecimals(markets);
    console.log('decimals', decimals);

    // get underlying

    const underlying = {};
    markets.forEach(m => underlying[m] = m);
    console.log('underlying', underlying);
    // get close factor

    const closeFactor = meldData.qrdGlobalState.gsCloseFactor.toString();
    console.log('closeFactor', closeFactor);
    const protocolFees = meldData.qrdGlobalState.gsProtocolIncentive.toString();
    console.log('protocolFees', protocolFees);

    // get total borrow
    const totalBorrows = getTotalBorrows(marketMap);
    console.log('totalBorrows', totalBorrows);

    // get total collateral
    const totalCollaterals = getTotalCollaterals(marketMap);
    console.log('totalCollaterals', totalCollaterals);

    // get users
    const users = getUsers(markets, marketMap);
    console.log('users', users);

    const data = {
        markets: markets,
        prices: prices,
        lastUpdateTime: Date.now(),
        liquidationIncentive: liquidationIncentives,
        collateralFactors: collateralFactors,
        names: names,
        borrowCaps: borrowCaps,
        collateralCaps: collateralCaps,
        decimals: decimals,
        underlying: underlying,
        closeFactor: closeFactor,
        protocolFees: protocolFees,
        totalBorrows: totalBorrows,
        totalCollateral: totalCollaterals,
        users: users
    };

    if (!fs.existsSync('./user-data')) {
        fs.mkdirSync('user-data');
    }

    fs.writeFileSync('./user-data/data.json', JSON.stringify(data, null, 2));
    return true;
}

// TranslateMeldData();

module.exports = { TranslateMeldData };