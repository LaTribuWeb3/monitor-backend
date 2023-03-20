const { FetchMinswapData } = require('./MinSwapFetcher');
const { ParseLiquidityAndSlippage } = require('./SlippageParser');
const { TranslateMeldData } = require('./UserDataTranslator');
const { FetchWingrindersData } = require('./WingridersLiquidityFetcher');
const { GraphDataExporter } = require('./GraphDataExporter');


async function main() {
    let success = false;
    try { 
        // start the minswap fetcher
        success = await FetchMinswapData();
        if(!success) {
            return;
        }

        // start the wingrider fetcher
        success = await FetchWingrindersData();
        if(!success) {
            return;
        }

        // start the slippage fetcher
        success = await ParseLiquidityAndSlippage();
        if(!success) {
            return;
        }

        // start the user data translator
        success = await TranslateMeldData();
        if(!success) {
            return;
        }

        success = await GraphDataExporter();
        if(!success) {
            return;
        }
    }
    catch(e) {
        console.log('Error occured:', e);
    }
    finally {
        console.log(`Ending Meld Worker with ${(success ? 'success' : 'error')} at ${new Date()}`);
        console.log('============================================');
    }
}

main();