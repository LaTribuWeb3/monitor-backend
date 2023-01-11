const { BigNumber, utils } = require('ethers');

/**
 * 
 * @param {string} bnStr big number string representation
 * @returns hex value for a big number
 */
function BNToHex(bnStr) {
    const bn = BigNumber.from(bnStr);
    const hex = bn.toHexString();
    if (hex == '0x00') {
        return '0';
    } else {
        return hex.replace('0x', '').replace(/^0+/, '');
    }
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
module.exports = { normalize, BNToHex };
