const { tokens } = require('./Addresses');
const fs = require('fs');

const POINT_PER_GRAPH = 48; // 1 point per 30 min = 48 point per 24h
const INTERVAL_BETWEEN_POINTS_SEC = 24 * 3600 / POINT_PER_GRAPH;

async function GraphDataExporter() {
    console.log('Creating Last Day Volume data from history src');
    const since = Math.floor(Date.now()/1000) - 24 * 60 * 60;
    const reserveData = {};
    for(const token of tokens) {
        console.log(`[${token.symbol}] Working on token ${token.symbol}`);
        reserveData[token.symbol] = {
            poolDepthInADA: {},
            tradingVolumeInADA: {}
        };

        const filePath = `./history-src/${token.symbol}-ADA.csv`;
        let historyDataSinceDate = getHistoryDataFromFile(filePath).filter(_ => _.timestamp >= since);
        // sort by block number asc
        historyDataSinceDate.sort((a,b) => a.timestamp - b.timestamp);

        let lastReserve = 0;
        for(let i = 0; i < POINT_PER_GRAPH; i ++) {
            const minDate = since + i * INTERVAL_BETWEEN_POINTS_SEC;
            const maxDate = since + (i +1) * INTERVAL_BETWEEN_POINTS_SEC;

            // find the first history data between minDate and maxDate
            const historyData = historyDataSinceDate.find(_ => _.timestamp >= minDate && _.timestamp < maxDate);
            if(!historyData) {
                console.log(`[${token.symbol}] Could not find data between dates ${minDate} and ${maxDate}`);
                continue;
            }

            reserveData[token.symbol].poolDepthInADA[historyData.timestamp] = historyData.reserveTOKEN * historyData.priceVSADA;

            const historyDataBetweenDates = historyDataSinceDate.filter(_ => _.timestamp >= minDate && _.timestamp < maxDate);
            let absoluteTradeMvt = 0;
            for(const history of historyDataBetweenDates) {
                if(lastReserve != 0) {
                    absoluteTradeMvt += Math.abs(history.reserveTOKEN - lastReserve);
                }

                lastReserve = history.reserveTOKEN;
            }

            if(absoluteTradeMvt != 0) {
                reserveData[token.symbol].tradingVolumeInADA[historyData.timestamp] = absoluteTradeMvt * historyData.priceVSADA;
            }
        }
        console.log(`[${token.symbol}] End working on token ${token.symbol}`);

    }

    fs.writeFileSync('history-src/last_day_volume.json', JSON.stringify(reserveData, null, 2));
    return true;
}

/**
 * 
 * @param {string} filePath 
 * @param {string} tokenSymbol 
 * @returns {{block: number, timestamp: number, reserveADA: number, reserveTOKEN: number, priceVSADA: number}[]}
 */
function getHistoryDataFromFile(filePath) {
    if(!fs.existsSync(filePath)) {
        throw new Error(`Could not find file ${filePath} to generate last day volume data`);
    }
    const fileContent = fs.readFileSync(filePath, 'utf-8').split('\n');
    const historyData = [];
    // first line is header so start i = 1
    // last line is empty so stop at length - 1
    for(let i = 1; i < fileContent.length - 1; i++) {
        const lineSplt = fileContent[i].split(',');
        // Block number,timestamp,reserve ADA,reserve C3,price (ADA/C3)
        const historyItem = {
            block: Number(lineSplt[0]),
            timestamp: Number(lineSplt[1]),
            reserveADA: Number(lineSplt[2]),
            reserveTOKEN: Number(lineSplt[3]),
            priceVSADA: Number(lineSplt[4]),
        };

        historyData.push(historyItem);
    }

    return historyData;
}

// GraphDataExporter();

module.exports = {GraphDataExporter};