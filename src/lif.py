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
# print(neighbours)
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
# print(neighbours)
# this further confirms the suspicion that the big ID's are not annotated at all

# filter out these NaN neighbours since the cluster needed requires neurons
# that can be labelled and reasoned about

real_neighbours = neighbours.dropna(subset=['pre_type', 'post_type']) # drop if subset cols has missing values
print(real_neighbours)

neuron_ids = real_neighbours[['body_pre', 'body_post']].stack().unique().tolist() # flatten, remove dupes, then list

# set up the neurons and connections as plain Python structures
charge = {nid: 0 for nid in neuron_ids} # dict comprehension -> everyone starts at 0 charge

# convert df rows into tuples -> (pre, post, weight)
# - iterate over specific columns so must filter them
# - index=False excludes index from the tuple, and name=None prevents a named tuple.. whatever that means
edges = list(real_neighbours[['body_pre', 'body_post', 'weight']].itertuples(index=False, name=None))
print(edges)

# constants
# decay: each tick, whatever charge is sitting in a bucket loses 20% of itself. fast, but shows change
# threshold: want at least one neuron to actually fire in this toy run
# time_steps: let's see what happens
decay_factor = 0.8
threshold = 5
time_steps = 6

# external input mentioned
# - at tick 0, the photoreceptor gets a huge unit of charge simulating light hitting the eye
external_input = {11139: 10}

for t in range(time_steps):
    print(f"--- time step {t} ---")

    # apply external input only at the very first tick
    if t == 0:
        for nid, amount in external_input.items():
            print("external applied to", nid)
            charge[nid] += amount

    # figure out who fires this tick, based on charge BEFORE any resets happen
    fired = [nid for nid in neuron_ids if charge[nid] >= threshold]

    # apply the leak to everyone
    for nid in neuron_ids:
        charge[nid] *= decay_factor

    # firing neurons dump their charge to neighbors, then reset to 0
    for pre, post, weight in edges:
        if pre in fired:
            print(f"{pre} fires away to {post}")
            charge[post] += weight

    for nid in fired:
        charge[nid] = 0

    print({nid: round(c, 2) for nid, c in charge.items()})

# analysis:
# while yes the other ones pass the threshold, particularly 26947 and 29782,
# they dont have any edges connecting to anyone else so they fire and go to rest,
# while the others slowly go to rest

# as a result of this experiment what was learned: 
# ol -> vnc means the charge has to travel quite far
# so for that to happen, weights need to change so that the right paths get reinforced
# - down the line, some rule* that adjusts weights based on simulation runs
# bottom line: the fly is dead. so this file can be treated as a starting point to train the fly

# from here the decision can be made to expand what is currently built;
# to get a charge from ol_sensory to vnc_motor
# or circle back to that "some rule"

# to expand what is currently built, collect neighbours of 26947, 29782
# and add them to neuron_ids and edge structures. then repeat until reaching vnc_motor
# nothing about simulation logic changes, maybe the parameters, but only neuron_ids and edges itself grows
# note: graph traversal like dfs or bfs exist for this problem...
# - trying to find a vnc_motor neuron as the solution, while finding the path that lets charges travel there

filtered_path = root / 'data' / 'pipeline_edges_filtered.feather'
if filtered_path.exists():
    strong_only = pd.read_feather(filtered_path)
else:
    # code from the exploration
    import pyarrow.feather as feather
    import duckdb

    meta = feather.read_table(connections_file, memory_map=True)

    traced = df[df['status'] == 'Traced']
    lookup = traced[['bodyId', 'superclass']]

    target_superclasses = [
        'ol_sensory', 'ol_intrinsic', 'visual_projection',
        'cb_intrinsic', 'descending_neuron',
        'vnc_intrinsic', 'vnc_motor'
    ]

    # again let duckdb do the heavy lifting
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=2")

    con.register('lookup', lookup)
    con.register('connections', meta)

    placeholders = ",".join(["?"] * len(target_superclasses))

    pipeline_edges = con.execute(f"""
        SELECT c.body_pre, c.body_post, c.weight,
            pre.superclass AS pre_sc, post.superclass AS post_sc
        FROM connections AS c
        JOIN lookup AS pre ON c.body_pre = pre.bodyId
        JOIN lookup AS post ON c.body_post = post.bodyId
        WHERE pre.superclass IN ({placeholders})
        AND post.superclass IN ({placeholders})
    """, target_superclasses + target_superclasses).df()
    
    print(pipeline_edges.shape) # (22237488, 5) -> very large
    print(pipeline_edges.head())

    # try trimming the data, remember the '1' weights were trimmed
    # although because they were NaN ids, a weight of 1 is insignificant for the toy test

    # same-superclass edges are local self-talk, not pipeline progress
    cross_region = pipeline_edges[pipeline_edges['pre_sc'] != pipeline_edges['post_sc']]

    # weight=1 correlated with unreliable/fragment-adjacent connections earlier
    strong_only = cross_region[cross_region['weight'] >= 3]

    print(strong_only.shape)

    strong_only.to_feather(root / 'data' / 'pipeline_edges_filtered.feather')

strong_only_sorted = strong_only.sort_values('weight', ascending=False)
print(strong_only_sorted.head(20))





