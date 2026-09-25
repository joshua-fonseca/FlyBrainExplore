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

# get the confirmed finished neurons
traced = df[df['status'] == 'Traced']

# find what type of neurons are confirmed, and let's see how many there are
print(traced['type'].value_counts().head())
# Tm3, T3, T2a, L5, L2 are motion-detection neurons in the optic lobe
# can investigate more by changing the head value
# TODO: identify which neurons are for the specific use case

one_neuron = traced.iloc[0]
print(one_neuron)
# the one neuron's type is DNp01, it controls escape behaviours