import matplotlib.pyplot as plt
import json
import time
import os
import glob
import numpy as np
import pandas as pd
import copy
import sys
import shutil
import datetime
import math 

if __name__ == '__main__':
    trade_file = 'punks_full_trade_data.csv'
    repeg_file = 'repegs_1.csv'
    scenario_name = 'scenario_punks.csv'
    start_vNFT = 500
    start_vETH = 32133


    df_trades = pd.read_csv(trade_file)
    df_repegs = pd.read_csv(repeg_file)

    trades = []
    repegs = []
    for index, row in df_trades.iterrows():
        block = row['block']
        vETH_value = float(row['trade_notional'])
        trade_size = float(row['trade_size'])
        user_id = row['trader']
        fee_pct = float(row['fee_pct']) / 100
        
        # "Trade size is the base asset, say Punk. And the notional is the eth(x) that its worth. If trade size positive user goes long. If negative he is short."
        if trade_size > 0: # If trade size positive user goes long --> sell eth to buy punks
            trades.append({
                'block': block,
                'vETH_value': vETH_value,
                'vNFT_value': 0,
                'fee_pct': fee_pct,
                'user_id': user_id
            })
        else: # If negative he is short --> sell punks to buy eth 
            trades.append({
                'block': block,
                'vETH_value': 0,
                'vNFT_value': abs(trade_size),
                'fee_pct': fee_pct,
                'user_id': user_id
            })


    
    for index, row in df_repegs.iterrows():
        block = row['blockNumber']
        vETH_reserve = float(row['Y0_after'])
        vNFT_reserve = float(row['X0_after'])

        
        repegs.append({
            'block': block,
            'vETH_reserve': vETH_reserve,
            'vNFT_reserve': vNFT_reserve,
        })

    next_repeg_index = 0
    simulation_formatted_input = []
    all_repegs_filled = next_repeg_index >= len(repegs)

    simulation_formatted_input.append({
        't': 0,
        'action': 'set_liquidity',
        'vETH': start_vETH,
        'vNFT': start_vNFT,
        'userid': 'admin',
    })

    for trade in trades:
        while not all_repegs_filled and trade['block'] > repegs[next_repeg_index]['block']:
            # add set_liquidity to output because repeg
            simulation_formatted_input.append({
                't': repegs[next_repeg_index]['block'],
                'action': 'set_liquidity',
                'vETH': repegs[next_repeg_index]['vETH_reserve'],
                'vNFT': repegs[next_repeg_index]['vNFT_reserve'],
                'fees': 0,
                'userid': 'admin',
            })

            next_repeg_index += 1
            if next_repeg_index > len(repegs) - 1:
                all_repegs_filled = True

        simulation_formatted_input.append({
                't': trade['block'],
                'action': 'swap',
                'vETH': trade['vETH_value'],
                'vNFT': trade['vNFT_value'],
                'fees': trade['fee_pct'],
                'userid': trade['user_id'],
        })
        
    
    df_scenario = pd.DataFrame(simulation_formatted_input)
    df_scenario.to_csv(scenario_name, index=False)
    exit()