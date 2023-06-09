import os
import pandas as pd
import sys
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
                usersData[step_user]["total_diff_vETH"] += amount_vETH_minus_fees
                usersData[step_user]["total_diff_vNFT"] -= amount_vNFT
                step_collected_fees_vETH = fees_amount_vETH
                total_collected_fees_vETH += fees_amount_vETH

        print('step', step['t'], 'updated reserves to:', current_reserve_vETH, current_reserve_vNFT)
        step_output_platform = {
            "t": step['t'],
            "step_name": step_name,
            "reserve_vETH": current_reserve_vETH,
            "reserve_vNFT": current_reserve_vNFT,
            "price (vETH/vNFT)": current_reserve_vETH / current_reserve_vNFT,
            "step_diff_vETH": step_diff_vETH,
            "step_diff_vNFT": step_diff_vNFT,
            "step_collected_fees_vETH": step_collected_fees_vETH,
            "total_collected_fees_vETH": total_collected_fees_vETH,
            "total_diff_vETH": total_diff_vETH,
            "total_diff_vNFT": total_diff_vNFT,
            "user_id": step_user
        }

        cpt_user_long = 0
        total_long = 0
        cpt_user_short = 0
        total_short = 0
        for user in users:
            # only take value when != 0; value == 0 mean user did not do anything yet so should not be counted
            if usersData[user]['total_diff_vNFT'] < 0:
                cpt_user_short += 1
                total_short += usersData[user]['total_diff_vNFT']
                
            if usersData[user]['total_diff_vNFT'] > 0:
                cpt_user_long += 1
                total_long += usersData[user]['total_diff_vNFT']

        step_output_platform['cpt_user_long'] = cpt_user_long
        step_output_platform['total_long'] = total_long
        step_output_platform['cpt_user_short'] = cpt_user_short
        step_output_platform['total_short'] = total_short
        outputs_platform.append(step_output_platform)


    # calculate platform PNL
    # let's set the next step as pnl calculation, and for that we need to track all in assets and out assets (since inception)
    # and then to calc pnl we need to reverse the position. meaning if the total is 7 ETH in, and 5 NFT out,
    # then we need to see how much ETH we get for dumping 5 NFT (According to current x,y) and the pnl is the difference from 7. 
    # if the total is 7 nft in and 9 eth out. when we need to find out how much eth is needed to buy 7 nft back. 
    # and the diff is the difference from 9 eth.

    pnl = 0
    # find which asset is out
    # eth out
    if total_diff_vETH < 0:
        print(f'pnl calc: will search amount of vETH needed to buy', total_diff_vNFT, 'vNFT to calc PNL')
        vETH_needed_to_buy_vNFT = find_amount_vETH_to_buy_vNFT(current_reserve_vETH, current_reserve_vNFT, total_diff_vNFT)
        # vNFT_bought = swap_vETH_to_vNFT(current_reserve_vETH, current_reserve_vNFT, vETH_needed_to_buy_vNFT)
        # print(vNFT_bought, total_diff_vNFT)
        print(f'pnl calc: needing {vETH_needed_to_buy_vNFT} vETH to buy back {total_diff_vNFT} vNFT')
        pnl = abs(total_diff_vETH) - vETH_needed_to_buy_vNFT
    # nft out
    elif total_diff_vNFT < 0:
        vNFT_to_dump = -1 * total_diff_vNFT
        print(f'pnl calc: will dump', vNFT_to_dump, 'vNFT to vETH to calc PNL')
        amount_vETH = swap_vNFT_to_vETH(current_reserve_vETH, current_reserve_vNFT, vNFT_to_dump)
        print(f'pnl calc: dumping {vNFT_to_dump} will get back {amount_vETH} vETH')
        pnl = total_diff_vETH - amount_vETH
    else: 
        raise Exception('no asset in negative??')
    
    print(f'pnl calc: {pnl} vETH')

    return { 'outputs_platform': outputs_platform, 'outputs_users': outputs_users, 'pnl': pnl}


# x * y = k
# (x + Δx) * (y - Δy) = k
# Δy = (y * Δx) / (x + Δx)
def swap_vETH_to_vNFT(reserve_vETH, reserve_vNFT, amount_vETH):
    output_vNFT = (reserve_vNFT * amount_vETH) / (reserve_vETH + amount_vETH)
    return output_vNFT

def swap_vNFT_to_vETH(reserve_vETH, reserve_vNFT, amount_vNFT):
    output_vETH = (reserve_vETH * amount_vNFT) / (reserve_vNFT + amount_vNFT)
    return output_vETH

# Δx = (x * Δy) / (y - Δy)
def find_amount_vETH_to_buy_vNFT(reserve_vETH, reserve_vNFT, amount_vNFT):
    amount_needed_to_buy_vNFT = (reserve_vETH * amount_vNFT) / (reserve_vNFT - amount_vNFT)
    return amount_needed_to_buy_vNFT

if __name__ == '__main__':
    print(sys.argv)
    scenario_path = f'{sys.argv[1]}'
    scenario_name = os.path.basename(scenario_path)
    print('starting amm simulator on', scenario_path, scenario_name)
    steps = import_scenario(scenario_path)
    # print(steps)
    scenario_result = run_scenario(steps)
    df_platform = pd.DataFrame(scenario_result['outputs_platform'])
    output_path = scenario_path.replace(scenario_name, f'output_{scenario_name}')
    df_platform.to_csv(output_path, index=False)
    print('result saved to', output_path)
    # df_users = pd.DataFrame(scenario_result['outputs_users'])
    # df_users.to_csv(scenario_path.replace(scenario_name, f'output_{scenario_name}'), index=False)
    
    # fig, ax1 = plt.subplots()
    # fig.set_size_inches(12.5, 8.5)
    # ax2 = ax1.twinx()
    # ax1.plot(df_platform["block"], df_platform["reserve_vETH"], 'g-')
    # ax2.plot(df_platform["block"], df_platform["total_collected_fees_vETH"], 'b-', label='fees vETH')
    # ax2.plot(df_platform["block"], df_platform["reserve_vNFT"], 'r-')
    # ax1.set_label('Step')
    # ax1.set_ylabel('Reserve vETH', color='g')
    # ax2.set_label('Step')
    # ax2.set_ylabel('Reserve vNFT', color='r')

    # scenario_name = scenario_path.replace('.csv', '')
    # plt.title(scenario_name)
    # plt.legend()
    # plt.savefig(scenario_name + ".jpg")
    # plt.cla()
    # plt.close()
    exit()


