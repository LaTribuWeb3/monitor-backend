const fs = require('fs');
const liquidityDirectory = './liquidity';

/// take the two liquidity files and merges them to ouptut merged_liquidity.json

async function main() {
    try {
        console.log('============================================');
        console.log(`Starting Slippage Parser - aggregating data ${new Date()}`);
        if (!fs.existsSync(`${liquidityDirectory}/minswap_liquidity.json`) || !fs.existsSync(`${liquidityDirectory}/wingriders_liquidity.json`)) {
            console.error('Cannot read data files');
        }
        const aggregatedData = {};
        const minswapJson = fs.readFileSync(`${liquidityDirectory}/minswap_liquidity.json`);
        const minswapData = JSON.parse(minswapJson);
        const wingridersJson = fs.readFileSync(`${liquidityDirectory}/wingriders_liquidity.json`);
        const wingridersData = JSON.parse(wingridersJson);
        
        for(const entry in minswapData){
            if(entry !== 'json_time'){
                aggregatedData[entry] = {
                    reserveT0: minswapData[entry]['reserveT0'] + wingridersData[entry]['reserveT0'],
                    reserveT1: minswapData[entry]['reserveT1'] + wingridersData[entry]['reserveT1']
                };
            }
        }
        fs.writeFileSync(`${liquidityDirectory}/aggregated_liquidity.json`, JSON.stringify(aggregatedData, null, 2));
    }
    catch (e) {
        console.log('Error occured:', e);
    }
    finally {
        console.log(`Ending Slippage Parser - data aggregated at ${new Date()}`);
        console.log('============================================');
    }
}

main();