
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

def import_scenario(csv_file_path):
    steps = []
    df = pd.read_csv(csv_file_path)
    
    for index, row in df.iterrows():
        if index == 0:
            if row['action'] != 'set_liquidity':
                raise Exception('First action should be set_liquidity, not', df['action'])
            
        steps.append({
            "t": row['t'],
            "action": row['action'],
            "vETH": float(row['vETH']),
            "vNFT": float(row['vNFT']),
            "fees": float(row['fees']),
            "userid": row['userid'],
        })
    return steps


def run_scenario(steps):
    print('running scenario with', len(steps), 'steps')
    outputs_platform = []
    outputs_users = []
    current_reserve_vETH = 0
    current_reserve_vNFT = 0
    total_collected_fees_vETH = 0

    # check number of differents users that will interract during this simulation
    users = []
    usersData = {}
    for step in steps:
        step_user = step['userid']
        if step_user != 'admin' and step_user not in users:
            usersData[step_user] = {
                "total_diff_vETH": 0,
                "total_diff_vNFT": 0
            }
            users.append(step_user)

    total_diff_vETH = 0
    total_diff_vNFT = 0
    step_id = 0

    # loop through steps, for each steps we will to something based on the 'action' of the step
    # possible actions: add_liquidity or swap
    for step in steps:
        step_name = ''
        action = step['action']
        print('working on step with action:', action)
        step_user = step['userid']
        fees_pct = step['fees']
        step_diff_vETH = 0
        step_diff_vNFT = 0
        step_collected_fees_vETH = 0
        if action == 'set_liquidity':
            current_reserve_vETH = step['vETH']
            current_reserve_vNFT = step['vNFT']
            step_name = f'set liquidity: {step["vETH"]} vETH / {step["vNFT"]} vNFT'
        elif action == 'swap':
            # IF vETH is not NAN: it's swap vETH => vNFT
            if not math.isnan(step['vETH']) and step['vETH'] > 0:
                amount_vETH = step['vETH']
                step_name = f'{step_user} swaps {amount_vETH} vETH to vNFT'
                print('step', step['t'], 'is swap_vETH_to_vNFT')

                # calc vETH fees before swapping
                fees_amount_vETH = amount_vETH * fees_pct
                amount_vETH_minus_fees = amount_vETH - fees_amount_vETH
                amount_vNFT = swap_vETH_to_vNFT(current_reserve_vETH, current_reserve_vNFT, amount_vETH_minus_fees)
                print('step', step['t'], 'fees:', fees_amount_vETH, 'vETH')
                print('step', step['t'], step_user, 'received', amount_vNFT, 'vNFT by swapping', amount_vETH_minus_fees, 'vETH')
                current_reserve_vETH += amount_vETH_minus_fees
                current_reserve_vNFT -= amount_vNFT

                step_diff_vETH = amount_vETH_minus_fees
                step_diff_vNFT = -1 * amount_vNFT
                total_diff_vETH += amount_vETH_minus_fees
                total_diff_vNFT -= amount_vNFT
                usersData[step_user]["total_diff_vETH"] -= amount_vETH
                usersData[step_user]["total_diff_vNFT"] += amount_vNFT
                step_collected_fees_vETH = fees_amount_vETH
                total_collected_fees_vETH += fees_amount_vETH

            # IF vNFT is not NAN: it's swap vNFT => vETH
            elif not math.isnan(step['vNFT']) and step['vNFT'] > 0:
                amount_vNFT = step['vNFT']
                step_name = f'{step_user} swaps {amount_vNFT} vNFT to vETH'
                print('step', step['t'], 'is swap_vNFT_to_vETH')
                amount_vETH = swap_vNFT_to_vETH(current_reserve_vETH, current_reserve_vNFT, amount_vNFT)
                fees_amount_vETH = fees_pct * amount_vETH
                amount_vETH_minus_fees = amount_vETH - fees_amount_vETH
                print('step', step['t'], 'fees:', fees_amount_vETH, 'vETH')
                print('step', step['t'], step_user, 'received', amount_vETH_minus_fees, 'vETH by swapping', amount_vNFT, 'vNFT')
                current_reserve_vETH -= amount_vETH
                current_reserve_vNFT += amount_vNFT
                
                step_diff_vETH = -1 * amount_vETH
                step_diff_vNFT = amount_vNFT
                total_diff_vETH -= amount_vETH
                total_diff_vNFT += amount_vNFT
                usersData[step_user]["total_diff_vETH"] += amount_vETH
                usersData[step_user]["total_diff_vNFT"] -= amount_vNFT
                step_collected_fees_vETH = fees_amount_vETH
                total_collected_fees_vETH += fees_amount_vETH

        print('step', step['t'], 'updated reserves to:', current_reserve_vETH, current_reserve_vNFT)
        step_output_platform = {
            "step_id": step_id,
            "step_name": step_name,
            "reserve_vETH": current_reserve_vETH,
            "reserve_vNFT": current_reserve_vNFT,
            "price (vNFT/vETH)": current_reserve_vNFT / current_reserve_vETH,
            "step_diff_vETH": step_diff_vETH,
            "step_diff_vNFT": step_diff_vNFT,
            "step_collected_fees_vETH": step_collected_fees_vETH,
            "total_collected_fees_vETH": total_collected_fees_vETH,
            "total_diff_vETH": total_diff_vETH,
            "total_diff_vNFT": total_diff_vNFT,
            "trader_id": step_user
        }

        step_output_users = {
            "step_id": step_id,
            "step_name": step_name,
        }

        for user in users:
            step_output_users[user + "_total_diff_vETH"] = usersData[user]['total_diff_vETH']
            step_output_users[user + "_total_diff_vNFT"] = usersData[user]['total_diff_vNFT']
                

        outputs_platform.append(step_output_platform)
        outputs_users.append(step_output_users)
        step_id += 1



    return { 'outputs_platform': outputs_platform, 'outputs_users': outputs_users }


# x * y = k
# (x + Δx) * (y - Δy) = k
# x * y = (x + Δx) * (y - Δy)
# Δy = (y * Δx) / (x + Δx)
def swap_vETH_to_vNFT(reserve_vETH, reserve_vNFT, amount_vETH):
    output_vNFT = (reserve_vNFT * amount_vETH) / (reserve_vETH + amount_vETH)
    return output_vNFT

def swap_vNFT_to_vETH(reserve_vETH, reserve_vNFT, amount_vNFT):
    output_vETH = (reserve_vETH * amount_vNFT) / (reserve_vNFT + amount_vNFT)
    return output_vETH

if __name__ == '__main__':
    scenario_path = 'scenario_0.csv'
    
    print('starting amm simulator on', scenario_path)
    steps = import_scenario(scenario_path)
    print(steps)
    scenario_result = run_scenario(steps)
    df_platform = pd.DataFrame(scenario_result['outputs_platform'])
    df_platform.to_csv(f'output_platform_{scenario_path}', index=False)
    df_users = pd.DataFrame(scenario_result['outputs_users'])
    df_users.to_csv(f'output_users_{scenario_path}', index=False)
    fig, ax1 = plt.subplots()
    fig.set_size_inches(12.5, 8.5)
    ax2 = ax1.twinx()
    ax1.plot(df_platform["step_id"], df_platform["reserve_vETH"], 'g-')
    ax2.plot(df_platform["step_id"], df_platform["total_collected_fees_vETH"], 'b-', label='fees vETH')
    ax2.plot(df_platform["step_id"], df_platform["reserve_vNFT"], 'r-')
    ax1.set_label('Step')
    ax1.set_ylabel('Reserve vETH', color='g')
    ax2.set_label('Step')
    ax2.set_ylabel('Reserve vNFT', color='r')

    scenario_name = scenario_path.replace('.csv', '')
    plt.title(scenario_name)
    plt.legend()
    plt.savefig(scenario_name + ".jpg")
    plt.cla()
    plt.close()
    exit()


