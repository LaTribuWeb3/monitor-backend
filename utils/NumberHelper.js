
function roundTo(num, dec) {
    const pow =  Math.pow(10,dec);
    return Math.round((num + Number.EPSILON) * pow) / pow;
}

module.exports = { roundTo };