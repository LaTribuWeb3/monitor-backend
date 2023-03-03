import json
import requests
import time
import private_config
import datetime


last_gas_price_fetch = None
current_gas_price = None
class KyberPrices:
    def __init__(self, network, inv_names, underlying, decimals):
        self.url = "https://aggregator-api.kyberswap.com/" + network + "/route/encode?" \
                                                                       "tokenIn=TOKEN_IN&" \
                                                                       "tokenOut=TOKEN_OUT&" \
                                                                       "amountIn=AMOUNT_IN&" \
                                                                       "saveGas=0&" \
                                                                       "gasInclude=0&" \
                                                                       "gasPrice=70000000&" \
                                                                       "slippageTolerance=50&" \
                                                                       "deadline=DEAD_LINE&" \
                                                                       "to=0x0000000000000000000000000000000000000000&" \
                                                                       "chargeFeeBy=&" \
                                                                       "feeReceiver=&" \
                                                                       "isInBps=&feeAmount=&" \
                                                                       "clientData={'source':'kyberswap'}"

        self.underlying = underlying
        self.decimals = decimals
        self.inv_names = inv_names
        self.chain_id = network

    def get_price(self, base, quote, volume_in_base):
        token_in = self.underlying[self.inv_names[base]]
        token_out = self.underlying[self.inv_names[quote]]
        amount_in = volume_in_base * 10 ** self.decimals[self.inv_names[base]]
        if base == "VST":
            token_in = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
            amount_in = volume_in_base * 10 ** 6

        # url_to_send = self.url.replace("DEAD_LINE", str(time.time() + 1000))
        # url_to_send = url_to_send.replace("TOKEN_IN", str(token_in))
        # url_to_send = url_to_send.replace("TOKEN_OUT", str(token_out))
        # url_to_send = url_to_send.replace("AMOUNT_IN", str(int(amount_in)))
        url_to_send = ""
        global current_gas_price
        global last_gas_price_fetch

        if private_config.use_one_inch_pathfinder: 
            now = datetime.datetime.now()
            if last_gas_price_fetch == None or (now - last_gas_price_fetch).total_seconds() > 120 : # fetch gas price every 2 minutes
                etherscanGastResponse = requests.get('https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YourApiKeyToken')
                etherscanGastResponseData = etherscanGastResponse.json()
                last_gas_price_fetch = datetime.datetime.now()
                current_gas_price = int(int(etherscanGastResponseData['result']['ProposeGasPrice']) * 1e9)
                print('updated gas price to', current_gas_price)

            url_to_send = 'https://pathfinder.1inch.io/v1.4/chain/'+str(self.chain_id)+'/router/v5/quotes?fromTokenAddress='+ str(token_in) + \
                            '&toTokenAddress='+str(token_out)+'&amount='+str(int(amount_in))+'&preset=maxReturnResult&gasPrice='+ str(current_gas_price)
        else:
            url_to_send = "https://api.1inch.io/v4.0/" + str(self.chain_id) + "/quote?" \
                "fromTokenAddress=" + str(token_in) + "&" \
                "toTokenAddress=" + str(token_out) + "&" \
                "amount=" + str(int(amount_in))
        time.sleep(1)
        time_to_sleep = 1
        while True:
            try:
                response = requests.get(url_to_send, headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'})
                data = response.json()
                response_amount_in = int(amount_in) / 10 ** self.decimals[self.inv_names[base]]
                if base == "VST":
                    response_amount_in = int(amount_in) / 10 ** 6

                response_amount_out = 0
                if private_config.use_one_inch_pathfinder: 
                    response_amount_out = int(data['bestResult']['toTokenAmount']) / 10 ** self.decimals[self.inv_names[quote]]
                else:
                    response_amount_out = int(data["toTokenAmount"]) / 10 ** self.decimals[self.inv_names[quote]]

                price_in_base = response_amount_in / response_amount_out
                return price_in_base
            except Exception as e:
                print(e)
                print(response.json)
                print(response.text)
                time.sleep(time_to_sleep)
                time_to_sleep += 3


