const Web3 = require('web3')
const Compound = require("./CompoundParser.js")
const Addresses = require("./Addresses.js")

async function test() {


    const fs = require('fs');

    const filePath = './key.json';
    let url
    
    if (fs.existsSync(filePath)) {
      const data = fs.readFileSync(filePath)
      const json = JSON.parse(data)
      const key = json["key"]
      
      url = "https://aurora-mainnet.infura.io/v3/" + key
    } else {
        url = "https://mainnet.aurora.dev"
    }

    console.log({url})

    //const web3 = new Web3(url)


    const comp = new Compound(Addresses.aurigamiAddress, "NEAR", url, "data.json")
    await comp.main()
 }

 test()
