const axios = require('axios');
const fs = require('fs');

async function format() {
    try {
        const dataToWrite = [];
        const fileContent = fs.readFileSync('simulations/data_worst_day/2022-june-10-19-weth-usdc-history-full.csv', 'utf-8').split('\n');
        fileContent.shift();
        const blocks = fs.readFileSync('simulations/data_worst_day/blockcache.json');
        const blockDir = JSON.parse(blocks);
        let progress = 0;
        let lastTimeStamp = undefined;
        const end = fileContent.length;
        for (const line of fileContent) {
            progress++;
            if (!line) {
                continue;
            }
            const lineData = line.split(',');
            const blockNumber = lineData[0];
            const price = lineData[1];
            if (blockNumber in blockDir) {
                lastTimeStamp = blockDir[blockNumber];
            }
            if(progress === 1) {
                lastTimeStamp = await getTimestamp(blockNumber);
            }
            else {
                lastTimeStamp += 14.8;
            }
            const date = new Date(lastTimeStamp * 1000).toISOString().replace(/T/, ' ').replace(/\..+/, '');
            const lineToWrite = `${blockNumber},${lastTimeStamp*1e6},${price},${price},0.0,0.0,${date}\n`;
            dataToWrite.push(lineToWrite);
            console.log(`line ${progress} / ${end} -- ${(progress / end * 100).toFixed(2)}% done`);
        }
        fs.writeFileSync('data_unified_2022-june-10-19-weth-usdc-history-full', dataToWrite.join(''));


    }
    catch (error) {
        console.log(error);
    }

}

format();

async function getTimestamp(blockNumber) {
    const blockTimestampResp = await axios.get(`http://dev-0.la-tribu.xyz:7878/api/getblocktimestamp?blocknumber=${blockNumber}`);
    return blockTimestampResp.data.timestamp;
}