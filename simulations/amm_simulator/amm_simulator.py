
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
            if row['action'] != 'add_liquidity':
                raise Exception('First action should be add_liquidity, not', df['action'])
            
        steps.append({
            "t": row['t'],
            "action": row['action'],
            "x": float(row['x']),
            "y": float(row['y']),
            "fees": float(row['fees']),
            "userid": row['userid'],
        })
    return steps


def run_scenario(steps):
    print('running scenario with', len(steps), 'steps')
    outputs = []
    current_reserve_x = 0
    current_reserve_y = 0
    total_collected_fees_x = 0
    total_collected_fees_y = 0

    # check number of differents users that will interract during this simulation
    users = []
    usersData = {}
    for step in steps:
        step_user = step['userid']
        if step_user != 'admin' and step_user not in users:
            usersData[step_user] = {
                "total_diff_x": 0,
                "total_diff_y": 0
            }
            users.append(step_user)

    total_diff_x = 0
    total_diff_y = 0
    step_id = 0

    # loop through steps, for each steps we will to something based on the 'action' of the step
    # possible actions: add_liquidity or swap
    for step in steps:
        step_name = ''
        action = step['action']
        print('working on step with action:', action)
        step_user = step['userid']
        fees_pct = step['fees']
        step_diff_x = 0
        step_diff_y = 0
        step_collected_fees_x = 0
        step_collected_fees_y = 0
        if action == 'add_liquidity':
            current_reserve_x += step['x']
            current_reserve_y += step['y']
            step_name = f'add liquidity: {step["x"]} x / {step["y"]} y'
        elif action == 'swap':
            # IF X is not NAN: it's swap x => y
            if not math.isnan(step['x']) and step['x'] > 0:
                amount_x = step['x']
                step_name = f'{step_user} swaps {amount_x} x to y'
                print('step', step['t'], 'is swap_x_to_y')
                fees = amount_x * fees_pct
                print('step', step['t'], 'fees:', fees)
                amount_y = swap_x_to_y(current_reserve_x, current_reserve_y, amount_x, fees_pct)
                print('step', step['t'], step_user, 'received', amount_y, 'y by swapping', amount_x, 'x')
                current_reserve_x += amount_x
                current_reserve_y -= amount_y

                step_diff_x = amount_x
                step_diff_y = -1 * amount_y
                total_diff_x += amount_x
                total_diff_y -= amount_y
                usersData[step_user]["total_diff_x"] -= amount_x
                usersData[step_user]["total_diff_y"] += amount_y
                step_collected_fees_x = fees
                total_collected_fees_x += fees

            # IF Y is not NAN: it's swap y => x
            elif not math.isnan(step['y']) and step['y'] > 0:
                amount_y = step['y']
                step_name = f'{step_user} swaps {amount_y} y to x'
                print('step', step['t'], 'is swap_y_to_x')
                fees = amount_y * fees_pct
                print('step', step['t'], 'fees:', fees)
                amount_x = swap_y_to_x(current_reserve_x, current_reserve_y, amount_y, fees_pct)
                print('step', step['t'], step_user, 'received', amount_x, 'x by swapping', amount_y, 'y')
                current_reserve_x -= amount_x
                current_reserve_y += amount_y
                
                step_diff_x = -1 * amount_x
                step_diff_y = amount_y
                total_diff_x -= amount_x
                total_diff_y += amount_y
                usersData[step_user]["total_diff_x"] += amount_x
                usersData[step_user]["total_diff_y"] -= amount_y
                step_collected_fees_y = fees
                total_collected_fees_y += fees

        print('step', step['t'], 'updated reserves to:', current_reserve_x, current_reserve_y)
        step_output = {
            "step_id": step_id,
            "step_name": step_name,
            "reserve_x": current_reserve_x,
            "reserve_y": current_reserve_y,
            "price (y/x)": current_reserve_y / current_reserve_x,
            "step_diff_x": step_diff_x,
            "step_diff_y": step_diff_y,
            "step_collected_fees_x": step_collected_fees_x,
            "step_collected_fees_y": step_collected_fees_y,
            "total_diff_x": total_diff_x,
            "total_diff_y": total_diff_y,
            "total_collected_fees_x": total_collected_fees_x,
            "total_collected_fees_y": total_collected_fees_y
        }

        for user in users:
            step_output[user + "_total_diff_x"] = usersData[user]['total_diff_x']
            step_output[user + "_total_diff_y"] = usersData[user]['total_diff_y']
                

        outputs.append(step_output)
        step_id += 1



    return outputs

    # x * y = k
    # (x + Δx) * (y - Δy) = k
    # x * y = (x + Δx) * (y - Δy)
    # Δy = (y * Δx) / (x + Δx)

def swap_x_to_y(reserve_x, reserve_y, amount_x, fees):
    numerator = amount_x * reserve_y * (1 - fees)
    denominator = reserve_x + (amount_x * (1 - fees))
    return numerator / denominator

def swap_y_to_x(reserve_x, reserve_y, amount_y, fees):
    numerator = amount_y * reserve_x * (1 - fees)
    denominator = reserve_y + (amount_y * (1 - fees))
    return numerator / denominator

if __name__ == '__main__':
    scenario_path = 'scenario_0.csv'
    
    print('starting amm simulator on', scenario_path)
    steps = import_scenario(scenario_path)
    print(steps)
    scenario_result = run_scenario(steps)
    df = pd.DataFrame(scenario_result)
    df.to_csv(f'output_{scenario_path}', index=False)
    fig, ax1 = plt.subplots()
    fig.set_size_inches(12.5, 8.5)
    ax2 = ax1.twinx()
    ax1.plot(df["step_id"], df["reserve_x"], 'g-')
    ax2.plot(df["step_id"], df["total_collected_fees_x"], 'b-', label='fees x')
    ax2.plot(df["step_id"], df["reserve_y"], 'r-')
    ax2.plot(df["step_id"], df["total_collected_fees_y"], 'y-', label='fees y')
    ax1.set_label('Step')
    ax1.set_ylabel('Reserve x', color='g')
    ax2.set_label('Step')
    ax2.set_ylabel('Reserve y', color='r')

    scenario_name = scenario_path.replace('.csv', '')
    plt.title(scenario_name)
    plt.legend()
    plt.savefig(scenario_name + ".jpg")
    plt.cla()
    plt.close()
    exit()


