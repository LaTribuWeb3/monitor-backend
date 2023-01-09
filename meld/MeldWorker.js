const { FetchMinswapData } = require('./MinSwapFetcher');
const { ParseLiquidityAndSlippage } = require('./SlippageParser');
const { TranslateMeldData } = require('./UserDataTranslator');
const { FetchWingrindersData } = require('./WingridersLiquidityFetcher');
const processExecutor = require('child_process');

const pythonCommand = process.env.PYTHON_CMD ? process.env.PYTHON_CMD : 'python';

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
        
        // processExecutor.execSync(`cd ../simulations && ${pythonCommand} runner_meld.py 1`, {stdio: 'inherit'});

        // TODO CHECK FILES ARE UPDATED

        // prepare other files needed
        

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