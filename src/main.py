import pandas as pd

filename = 'body-annotations-male-cns-v1.0-minconf-0.5.feather'

df = pd.read_feather(filename)

def other_functions_used_to_explore():
    print(df.columns)   # 36 cols are all strings
    print(df.head())    # a lot of data

print(df.shape)     # 211577 rows, 36 cols
# why is there so much rows compared to the claimed 166k number?

print(df.columns.tolist())
# see if any are self explanatory or trash
# see .md