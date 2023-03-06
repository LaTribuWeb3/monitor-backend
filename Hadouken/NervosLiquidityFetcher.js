const { getTokaiLiquidity } = require("../yokaiswap/univ2Parser");
const { hadoukenUSDLiquidityFetcher, hadoukenWBTCLiquidityFetcher } = require("./HadoukenSpecificLiquidity");
const fs = require('fs');


async function NervosLiquidityFetcher() {
    try {
        console.log('============================================');
        console.log(`Started Nervos liquidity fetcher at ${new Date()}`);

        const USDLiquidity = await hadoukenUSDLiquidityFetcher();
        const WBTCLiquidity = await hadoukenWBTCLiquidityFetcher();
        const GeneralLiquidity = await getTokaiLiquidity();
        

        const aggregated_liquidity = {};
        aggregated_liquidity['lastUpdateTime'] = Math.floor(Date.now() / 1000);
        for(entry in USDLiquidity){
            if(entry === "lastUpdate"){
            }
            else{
                aggregated_liquidity[entry] = USDLiquidity[entry]
                aggregated_liquidity[entry]['type'] = 'curve'
            }
        }
        for(entry in WBTCLiquidity){
            if(entry === "lastUpdate"){
            }
            else{
                aggregated_liquidity[entry] = WBTCLiquidity[entry]
                aggregated_liquidity[entry]['type'] = 'uniswap'
            }
        }
        for(entry in GeneralLiquidity){
            if(entry === "lastUpdate"){
            }
            else{
                // only add liquidity from yokai swap if we don't already have it
                if(!aggregated_liquidity[entry]) {
                    aggregated_liquidity[entry] = GeneralLiquidity[entry]
                    aggregated_liquidity[entry]['type'] = 'uniswap'
                } else {
                    console.log(`Liquidity for ${entry} already exists`);
                }
            }
        }

        fs.writeFileSync(`aggregated_liquidity.json`, JSON.stringify(aggregated_liquidity, null, 2));
        
    }

    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ended Nervos liquidity fetcher at ${new Date()}`);
        console.log('============================================');
    }
 }

 module.exports = {NervosLiquidityFetcher}