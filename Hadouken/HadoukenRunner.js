const { HadoukenParser } = require("./HadoukenParser.js");
const { NervosLiquidityFetcher } = require("./NervosLiquidityFetcher.js");
const {oracleUpdater} = require("./OracleParser.js")
const fs = require('fs');
const { hadoukenAddress } = require("./Addresses.js");


async function HadoukenRunner() {
    try {
        console.log('============================================');
        console.log(`Started Hadouken Runner at ${new Date()}`);

        await NervosLiquidityFetcher();
        await HadoukenParser();
        await oracleUpdater();

    }

    catch (e) {
        console.log('Error occured:', e);
        return false;
    }
    finally {
        console.log(`Ended Hadouken Runner at ${new Date()}`);
        console.log('============================================');
        console.log("sleeping for an hour")
        setTimeout(HadoukenRunner, 1000 * 60 * 60) // sleep for 1 hour 
    }
 }

 HadoukenRunner()