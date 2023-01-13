const { getTokaiLiquidity } = require("../yokaiswap/univ2Parser.js");
const { hadoukenUSDLiquidityFetcher } = require("./HadoukenUSDLiquidity.js");
const fs = require('fs');


async function NervosLiquidityFetcher() {
    try {
        console.log('============================================');
        console.log(`Started Nervos liquidity fetcher at ${new Date()}`);

        const USDLiquidity = await hadoukenUSDLiquidityFetcher();
        const GeneralLiquidity = await getTokaiLiquidity();
        

        const aggregated_liquidity = {};
        for(entry in USDLiquidity){
            if(entry === "lastUpdate"){
            }
            else{
                aggregated_liquidity[entry] = USDLiquidity[entry]
                aggregated_liquidity[entry]['type'] = 'curve'
            }
        }
        for(entry in GeneralLiquidity){
            if(entry === "lastUpdate"){
            }
            else{
                aggregated_liquidity[entry] = GeneralLiquidity[entry]
                aggregated_liquidity[entry]['type'] = 'uniswap'
            }
        }



        console.log('aggregated_liquidity', aggregated_liquidity)
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

 NervosLiquidityFetcher()