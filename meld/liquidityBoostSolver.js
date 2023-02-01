const { roundTo } = require('../utils/NumberHelper');
const slippageValues = require('./liquidity/usd_volume_for_slippage.json');

/*Liquidity MELD->HOSKY for 10% slippage = $27188
We want to do x2 on MELD HOSKY to have a liquidity $54376 with 10% slippage

Liquidity MELD->ADA = $123910
Liquidity ADA->HOSKY = $34825

Liquidity MELD->ADA / Liquidity ADA->HOSKY = 123910 / 34825 = 3.56

Ratio is 3.56:1
10 / (3.56 + 1) = 2,19

Ratio is 3.56*2.19:1*2.19
Ratio is 7.8:2.2

so 2.2% of the slippage is caused by MELD->ADA
and 7.8% of the slippage is caused by ADA->HOSKY

we then do x2 on ADA->HOSKY liquidity as it's the lowest liquidity

new liquidities: 
Liquidity MELD->ADA = $123910
Liquidity ADA->HOSKY = $34825*2 = $69650
new slippage: 
2.2 + 7.8/2 = 6,1% 

continue increasing ADA->HOSKY liquidity until reaching 5% slippage (meaning x2 MELD/HOSKY liquidity)*/

main(process.argv[2], process.argv[3], process.argv[4]);

async function main(tokenA, tokenB, increaseFactor) {
    // const tokenA = 'MELD';
    // const tokenB = 'HOSKY';
    const baseLiquidityAvsADA = slippageValues[tokenA]['ADA'].volume;
    const baseLiquidityADAvsB = slippageValues['ADA'][tokenB].volume;
    const slippageAvsADA = slippageValues[tokenA]['ADA'].llc - 1;
    const slippageADAvsB = slippageValues['ADA'][tokenB].llc - 1;
    const currentSlippage = Math.round(Math.max(slippageAvsADA, slippageADAvsB) * 100);
    const liquidityFactorRequired = increaseFactor; // 2 = we want 100% increase
    const targetSlippage = currentSlippage / liquidityFactorRequired;

    console.log(`Increase required on ${tokenA}->${tokenB}: +${(liquidityFactorRequired-1)*100}%`);
    console.log(`Finding liquidity increase for ${tokenA}->${tokenB}, meaning ${tokenA}->ADA and ADA->${tokenB}`);
    console.log(`Target effective slippage: ${targetSlippage}%`);

    // console.log(`Base liquidity ${tokenA}->ADA: $${baseLiquidityAvsADA}`);
    // console.log(`Base liquidity ADA->${tokenB}: $${baseLiquidityADAvsB}`);

    const baseRatio = baseLiquidityAvsADA / baseLiquidityADAvsB;
    const ratioToCurrentSlippage = currentSlippage / (baseRatio + 1);
    let slippageWeightOfTokenA = ratioToCurrentSlippage;
    let slippageWeightOfTokenB = ratioToCurrentSlippage * baseRatio;
    
    // console.log(`baseRatio: ${baseRatio}`);
    // console.log(`${tokenA} is causing ${roundTo(slippageWeightOfTokenA)} of the ${currentSlippage}% slippage`);
    // console.log(`${tokenB} is causing ${roundTo(slippageWeightOfTokenB)} of the ${currentSlippage}% slippage`);

    let currentEffectiveSlippage = currentSlippage;

    let simulatedLiquidityA = baseLiquidityAvsADA;
    let simulatedLiquidityB = baseLiquidityADAvsB;
    
    const stepSize = 1 + 1 / 1000; // 1.001
    console.log(`Base liquidities:\n   - ${tokenA}->ADA: $${roundTo(simulatedLiquidityA)}\n   - ADA->${tokenB}: $${roundTo(simulatedLiquidityB)}`);
    console.log(`Slippage weights: \n   - ${tokenA}: ${roundTo(slippageWeightOfTokenA)} of the ${currentSlippage}% slippage\n   - ${tokenB}: ${roundTo(slippageWeightOfTokenB)} of the ${currentSlippage}% slippage`);
    // console.log(`Current slippage: ${currentEffectiveSlippage}%`);
    while(currentEffectiveSlippage > targetSlippage) {
        if(simulatedLiquidityA == simulatedLiquidityB) {
            // increase both liquidities by stepSize
            const newLiquidity = stepSize * simulatedLiquidityA;
            simulatedLiquidityA = newLiquidity;
            simulatedLiquidityB = newLiquidity;
            slippageWeightOfTokenB = slippageWeightOfTokenB / stepSize;
            slippageWeightOfTokenA = slippageWeightOfTokenA / stepSize;
        } else {
            if(simulatedLiquidityA < simulatedLiquidityB) {
                // increase liquidity A by stepSize
                let newLiquidity = stepSize * simulatedLiquidityA;
                if(newLiquidity >= simulatedLiquidityB) {
                    newLiquidity = simulatedLiquidityB;
                    // console.log(`Liquidity of ${tokenA} reached liquidity of token ${tokenB}: ${newLiquidity}`);
                }
                const changeRatio = newLiquidity / simulatedLiquidityA;
                simulatedLiquidityA = newLiquidity;
                slippageWeightOfTokenA = slippageWeightOfTokenA / changeRatio;
            } else {
                // increase liquidity B by stepSize
                let newLiquidity = stepSize * simulatedLiquidityB;
                if(newLiquidity >= simulatedLiquidityA) {
                    newLiquidity = simulatedLiquidityA;
                    // console.log(`Liquidity of ${tokenB} reached liquidity of token ${tokenA}: ${newLiquidity}`);
                }
                const changeRatio = newLiquidity / simulatedLiquidityB;
                simulatedLiquidityB = newLiquidity;
                slippageWeightOfTokenB = slippageWeightOfTokenB / changeRatio;
            }
        }

        currentEffectiveSlippage = slippageWeightOfTokenA + slippageWeightOfTokenB;
    }

    // console.log(`ENDING effective slippage: ${roundTo(currentEffectiveSlippage, 2)}%`);
    const increaseRatioOfLiquidityAvsADA = simulatedLiquidityA / baseLiquidityAvsADA;
    const increaseRatioOfLiquidityADAvsB = simulatedLiquidityB / baseLiquidityADAvsB;
    // console.log(`Increasing ${tokenA}->${tokenB} liquidity by ${(liquidityFactorRequired-1)*100}% requires:`);
    // console.log(`    - Increasing ${tokenA}->ADA liquidity by ${roundTo((increaseRatioOfLiquidityAvsADA-1)*100)}%`);
    // console.log(`    - Increasing ADA->${tokenB} liquidity by ${roundTo((increaseRatioOfLiquidityADAvsB-1)*100)}%`);
    console.log(`Required Liquidities for a ${roundTo((liquidityFactorRequired-1)*100)}% increase:\n   - ${tokenA}->ADA: $${roundTo(simulatedLiquidityA)} (+${roundTo((increaseRatioOfLiquidityAvsADA-1)*100)}%)\n   - ADA->${tokenB}: $${roundTo(simulatedLiquidityB)} (+${roundTo((increaseRatioOfLiquidityADAvsB -1)*100)}%)`);
    
    return {
        tokenAIncreaseRatio: increaseRatioOfLiquidityAvsADA,
        tokenBIncreaseRatio: increaseRatioOfLiquidityADAvsB,
    };
}
