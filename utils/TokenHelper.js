const { BigNumber, utils } = require('ethers');


/**
 * compute the liquidity of a token to another, using the reserves of one pool and a target slippage
 *  with the following formula: 
 *  a = (y / e) - x
 *  with :
 *      a = amount of token from we can exchange to achieve target slippage,
 *      y = reserve to,
 *      e = target price and
 *      x = reserve from
 * @param {string} fromSymbol 
 * @param {number} reserveX 
 * @param {string} toSymbol 
 * @param {number} reserveY 
 * @param {number} targetSlippage 
 * @returns {number} amount of token exchangeable for defined slippage
 */
 function computeLiquidityForXYKPool(fromSymbol, fromReserve, toSymbol, toReserve, targetSlippage) {
    console.log(`computeLiquidity: Calculating liquidity from ${fromSymbol} to ${toSymbol} with slippage ${Math.round(targetSlippage * 100)} %`);

    const initPrice = toReserve / fromReserve;
    const targetPrice = initPrice - (initPrice * targetSlippage);
    console.log(`computeLiquidity: initPrice: ${initPrice}, targetPrice: ${targetPrice}`);
    const amountOfFromToExchange = (toReserve / targetPrice) - fromReserve;
    console.log(`computeLiquidity: ${fromSymbol}/${toSymbol} liquidity: ${amountOfFromToExchange} ${fromSymbol}`);
    return amountOfFromToExchange;
}

/**
 * Normalize a integer value to a number
 * @param {string | BigNumber} amount 
 * @param {number} decimals 
 * @returns {number} normalized number for the decimals in inputs
 */
function normalize(amount, decimals) {
    if(decimals === 18) {
        return Number(utils.formatEther(amount));
    }
    else if(decimals > 18) {
        const factor = BigNumber.from('10').pow(BigNumber.from(decimals - 18));
        const norm = BigNumber.from(amount.toString()).div(factor);
        return Number(utils.formatEther(norm));
    } else {
        const factor = BigNumber.from('10').pow(BigNumber.from(18 - decimals));
        const norm = BigNumber.from(amount.toString()).mul(factor);
        return Number(utils.formatEther(norm));
    }
}

module.exports = { normalize, computeLiquidityForXYKPool };