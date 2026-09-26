# LIF Model
# Leaky-Integrate-(and)-Fire

# The analogy: Each neuron is a leaky bucket under a dripping tap

# Integrate: 
# - when a connected neighbour fires, it drips some water into that bucket
# - how much water per drip depends on weight
# - "Integrate" just means adding these drips up over time

# Leaky:
# - the bucket has a hole in the bottom so it's leaking out and will empty out into nothing (Not into other buckets)
# - biologically, a neuron doesn't hold charge forever. like this bucket
# - decays back to resting state: which is just a charge of 0

# Fire:
# - once the water crosses a THRESHOLD, the neuron fires
# - all of it's water is dumped to every neuron it's connected to
# - amount of water depends on the weight of the connection
# - the bucket is back to being empty, or near empty

# simulations need one more ingredient: external input/artificial nudge
# - manually set a neurons charge to X so that water can circulate in the system

# the key thing to understand is that the distribution of the water is what should be observed
# "given one initial nudge, how does the charge distribute through a real piece of fly wiring,
# and does it reach anywhere interesting?"

# the initial nudge will have to happen to the eyes, in this case, the ol_sensory superclass
# - this is why the exploration was done, to know the data and not blindly inject somewhere else
# - hopefully watch whether it distributes the way it was predicted in the explore.py file

import pandas as pd
from pathlib import Path

root = Path(__file__).resolve().parent.parent
neurons_file = root / 'data' / 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
df = pd.read_feather(neurons_file)

neuron = df.query('superclass == \'ol_sensory\' and status == \'Traced\'').iloc[0]
print(neuron)

neuron_id = neuron['bodyId']
print('bodyId we are interested in: ', neuron_id)

# next, find it's neighbours to get a cluster
# because this looks at one neuron's direct connections, no batching or duckdb is needed

import pyarrow.dataset as ds
import pyarrow.compute as pc

connections_file = root / 'data' / 'connectome-weights-male-cns-v1.0-minconf-0.5.feather'

# again because the dataset is so big, a lazier loading method is used: .dataset
dataset = ds.dataset(connections_file, format="feather")

# pyarrow's filtering happens at the C++ level before things are a python object
# hence why it can do this operation and not crash
filter_expr = (pc.field("body_pre") == neuron_id) | (pc.field("body_post") == neuron_id)

# only then after we have a small subset can we go back to pandas
neighbours = dataset.to_table(filter=filter_expr).to_pandas()
print(neighbours.shape)
print(neighbours)
# 27 of 32 rows have 11139 as body_pre, which makes sense -> eyes see then must send that info out
# some id's look off, they look to be in the millions

# so check what superclass these id's are part of
id_to_superclass = df[df['status'] == 'Traced'].set_index('bodyId')['superclass'].to_dict()

neighbours['pre_type'] = neighbours['body_pre'].map(id_to_superclass)
neighbours['post_type'] = neighbours['body_post'].map(id_to_superclass)
# print(neighbours)

# every NaN neuron type correlates with either a big/unusual ID and/or weight = 1
# those NaN neighbours are connections to segments that exist in the raw EM reconstruction
# but never got fully proofread into confirmed, typed neurons

# so add a column of pre and post statuses
id_to_status = df.set_index('bodyId')['status'].to_dict()

neighbours['pre_status'] = neighbours['body_pre'].map(id_to_status)
neighbours['post_status'] = neighbours['body_post'].map(id_to_status)
print(neighbours)
# this further confirms the suspicion that the big ID's are not annotated at all

# filter out these NaN neighbours since the cluster needed requires neurons
# that can be labelled and reasoned about

real_neighbors = neighbours.dropna(subset=['pre_type', 'post_type'])
print(real_neighbors)