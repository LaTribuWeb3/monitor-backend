const Web3 = require('web3')
const Addresses = require("./Addresses.js")
const { toBN, toWei, fromWei } = Web3.utils
const fs = require('fs')
const nodeplot = require('nodeplotlib');

const start = 0//14.7e6
const end = 19e6//14.8e6

class ProcessJSONs {
    constructor(endBlock) {
        this.jsons = {}
        this.mainStablesPrice = {}

        console.log("reading jsons")
        for(const stable of Object.keys(Addresses.stableAddresses)) {
            this.jsons[stable] = JSON.parse(fs.readFileSync(stable + ".json"))
        }

        this.startBlock = Addresses.stableAddresses["SUSD"].deployment
        this.endBlock = endBlock

        /*
        console.log("fill USDT prices")
        this.fill3PoolPrices("USDT")

        console.log("fill DAI prices")
        this.fill3PoolPrices("DAI")
        */

        for(const stable of Object.keys(Addresses.stableAddresses)) {
            if(stable !== "UST") continue
            console.log("generate clean csv", stable)
            this.generateCleanCsv(stable)
        }        
    }

    generateCleanCsv(stable) {
        const fileName = "./onlyUsdc/" + stable + "_only_usdc.csv"
        fs.writeFileSync(fileName, "block,txHash,volume,price\n")
        const x = []
        const y = []
        for(let i = 0 ; i < this.jsons[stable].length ; i++) {
            const event = this.jsons[stable][i]

            // filter txs with multiple swaps, as it might be a manipulation on price (attacks)
            /*
            if(i < this.jsons[stable].length - 1) {
                const nextEvent = this.jsons[stable][i + 1]
                if(nextEvent.txHash === event.txHash) continue
            }
            if(i > 0) {
                const prevEvent = this.jsons[stable][i - 1]
                if(prevEvent.txHash === event.txHash) continue                
            }*/

            // filter dust
            if(event.volume < 1.0) continue

            let price = event.price
            const block = event.block            
            const counterToken = event.counterToken

            // take only trade with usdc
            if(counterToken !== "USDC") continue

            if(counterToken !== "USDC") {
                const counterPrice = this.mainStablesPrice[counterToken][block - this.startBlock]
                price = price / counterPrice
            }

            if((price < 0.5 || price > 2) && (stable !== "UST")) console.log(event.price, {price}, event.txHash, {stable})            

            if(event.block > start && event.block < end) {
                x.push(event.block)
                y.push(price )    
            }


            fs.appendFileSync(fileName,
                event.block +"," +
                event.txHash + "," +
                event.volume + "," +
                price + "\n")


        }


          const ori = JSON.parse(fs.readFileSync("LiquidityUST2.json"))
          const x2 = []
          const y2 = []
          for(const block of Object.keys(ori)) {
            if(Number(ori[block].ust) == 0) continue

            if(block > start && block < end) {
                x2.push(block)
                y2.push(Number(ori[block].threepool) / Number(ori[block].ust))
            }

          }

          const x3 = []
          const y3 = []
          for(const block of Object.keys(ori)) {
            if(Number(ori[block].ust) == 0) continue

            if(block > start && block < end) {
                x3.push(block)
                y3.push(Number(ori[block].threepool) / 500e6)
            }

          }          

          const data = [
            {
              x: x,
              y: y,
              type: 'scatter',
              title: "yaron",
              name : "price"
            },
/*
            {
                x: x2,
                y: y2,
                type: 'scatter',
                title: "yaron",
                name : "ust/usdc inventory ratio"
              },            */


              {
                x: x3,
                y: y3,
                type: 'scatter',
                title: "yaron",
                name : "usdc inventory in 500m"
              },                  
          ];


          nodeplot.plot({"data" : data, "title" : "yaron"});   
          //process.exit(1)     
    }

    fill3PoolPrices(stable) {
        let lastBlock = this.startBlock
        let lastPrice = 1.0

        this.mainStablesPrice[stable] = []

        for(const event of this.jsons[stable]) {
            const newBlock = event.block
            const price = event.price
            const counterToken = event.counterToken

            // try to filter out price manipulations in flash loans
            if(price < 0.9 || price > 1.1) continue

            if(price < 0.5 || price > 2) console.log({price}, event.txHash, {stable})

            if(counterToken !== "FRAX") continue

            for(let i = lastBlock ; i < newBlock ; i++) {
                this.mainStablesPrice[stable].push(lastPrice)
            }

            lastPrice = price
            lastBlock = newBlock
        }

        for(let i = lastBlock ; i <= this.endBlock ; i++) {
            this.mainStablesPrice[stable].push(lastPrice)
        }
    }
}

const parser = new ProcessJSONs(15489252)
