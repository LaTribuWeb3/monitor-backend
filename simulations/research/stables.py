import glob

import matplotlib.pyplot as plt
import pandas as pd
import os

files = glob.glob("..\\datasets\\*_clean*.csv")
all_dfs = {}
for file in files:
    print(file)
    df = pd.read_csv(file)
    asset = os.path.basename(file).replace(".csv", "")
    print(df["price"].describe())

# for asset in all_dfs:
#     plt.plot(all_dfs[asset]["block"], all_dfs[asset]["price"], label=asset)
#
# plt.legend()
# plt.show()