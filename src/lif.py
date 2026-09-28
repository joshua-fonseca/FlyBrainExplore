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

traced = df[df['status'] == 'Traced']

if filtered_path.exists():
    strong_only = pd.read_feather(filtered_path)
else:
    # code from the exploration
    import pyarrow.feather as feather
    import duckdb

    meta = feather.read_table(connections_file, memory_map=True)

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

# strong_only_sorted = strong_only.sort_values('weight', ascending=False)
# print(strong_only_sorted.head(20))

# build the graph
import networkx as nx

print(strong_only.head())

G = nx.from_pandas_edgelist(
    strong_only,
    source='body_pre',
    target='body_post',
    edge_attr='weight',     # carry the weight onto each edge
    create_using=nx.DiGraph # directed graph because energy flows one way
)

print(G.number_of_nodes(), G.number_of_edges())
# good news: program won't crash trying to make this graph

# so this means the traversal can occur. but there is one problem:
# nx.shortest_path(G, source, target, weight='weight')
# does not know "weight" means "connection strength"
# all graph problems are meant to minimize, rather than maximize (want the highest synapse)

# The fix: transform each edge's weight into a cost where strong = cheap, weak = expensive
# A common, principled way to do this: cost = 1 / weight
# A weight-1500 edge becomes cost = 0.00067, and a weight-3 edge becomes cost = 0.33
for u, v, data in G.edges(data=True):
    data['cost'] = 1 / data['weight']

def first_attempt():
    # feed a real target bodyId whose superclass is vnc_motor
    vnc_motor_neuron = traced.query('superclass == "vnc_motor"').iloc[0] # get one row of vnc_motor
    print(vnc_motor_neuron)

    target_id = vnc_motor_neuron['bodyId'] # only get the bodyId

    # checking if it's in the original graph -> it returns True
    print(target_id in G.nodes)

    # so assuming the start and end are in the graph, surely it will create a path
    path = nx.shortest_path(G, source=11139, target=target_id, weight='cost')
    print(path)
    print(len(path))

    # networkx.exception.NetworkXNoPath: No path between 11139 and 164190

    reachable = nx.descendants(G, 11139)
    print(len(reachable)) # result is 5

    # from 11139, following only strong it can reach a grand total of 5 other nodes
    # this matches the initial real_neighbours cluster that was connected to 5 nodes
    # none of those 5 ol_intrinsic targets happen to have their own strong,
    # cross-region outgoing edges that survived the filter, so the graph stops
    # one hop out, same as the toy LIF simulation found by hand

    # try a different ol_sensory starting neuron first
    ol_sensory_ids = traced.query('superclass == "ol_sensory"')['bodyId']
    for nid in ol_sensory_ids[:20]:
        if nid in G.nodes:
            r = len(nx.descendants(G, nid))
            print(nid, r)
    # 11139 5
    # 14428 80350
    # 15479 80350
    # 15625 80350
    # 16394 6
    # 16398 80353
    # 16681 80350
    # 16924 5
    # 17721 80350
    # 18040 80352
    # 18975 10
    # 18979 80350
    # 19418 5
    # 20107 80350
    # 20428 80350
    # 21134 6
    # 22842 80350
    # 24385 6
    # 25245 5
    # 25360 80350

    # after running the loop, it confirms that 11139 is just a poor, low-connectivity starting point
    # 11139 can reach 5 nodes while the rest can reach 80350. so start will be changed

source_id = 14428 # this id reaches 80k nodes

vnc_motor_ids = traced.query('superclass == "vnc_motor"')['bodyId']
valid_targets = [nid for nid in vnc_motor_ids if nid in G.nodes] # get data for vnc_motors in the graph
print(len(valid_targets)) # 705

# starting from source_id (ol_sensory neuron, 14428), and following directed edges forward only,
# what's the complete set of every node it could possibly reach, through any number of hops?
# 80,350 nodes for this particular source
reachable = nx.descendants(G, source_id)

# intersection of:
# "real motor neurons present in the graph" (valid_targets)
# "everything actually reachable from the specific starting neuron" (reachable)
reachable_motor = [nid for nid in valid_targets if nid in reachable] 
print(len(reachable_motor)) # 702

# reachable_motor comes back non-empty, go straight to
path = nx.shortest_path(G, source=source_id, target=reachable_motor[0], weight='cost')
for nid in path:
    print(nid, id_to_superclass.get(nid))

# output:
# 14428 ol_sensory
# 13984 visual_projection
# 10286 descending_neuron
# 11974 cb_intrinsic
# 10680 descending_neuron
# 164190 vnc_motor

# notice:
# descending_neuron to cb_intrinsic and then back to descending_neuron?
# translation:
# brain tells body what to do, brain thinks? then to a different neuron, it brain tells body what to do
# it could be two different descending neurons -> remember type vs. supertype
# it could be a loop in the fly's brain biologically

# new question: is the fly wiring not linear compared to the expectation, or is there a flaw in graph?

# check their types:
weird = traced[['bodyId', 'superclass', 'subclass', 'class', 'type']].query('bodyId in [10286, 10680]')
print(weird)
#      bodyId         superclass subclass class     type
# 267   10286  descending_neuron       xn   NaN  DNpe053
# 639   10680  descending_neuron       xn   NaN    DNp48

# 2 options:
# look up the neurons and see if the non linear pathing makes sense
# check if this happens in any other path (to isolate it to a problem with the graph?)

# loops through the first 5 reachable vnc_motor targets (instead of just reachable_motor[0]),
# runs the same shortest-path search against each one from the same source_id,
# and prints each full path translated into superclasses

# want to check if descending_neuron show up twice, with cb_intrinsic in between, in most or all of these paths
for i in range(min(5, len(reachable_motor))):
    target = reachable_motor[i]
    path = nx.shortest_path(G, source=source_id, target=target, weight='cost')
    readable = [(nid, id_to_superclass.get(nid)) for nid in path]
    print(f"--- path to {target} ---")
    for nid, sc in readable:
        print(nid, sc)
    print()

# output is quite large, so to summarize, the fly brain is not as linear as expected

# what was the point of all this?
# - the graph structurally shows how neurons are connected
# - scaling the toy LIF would show the distribution of energy
#    -> answers: would the charge die before reaching vnc_motor?

# so next would be to scale the LIF:
# - allows to tune decay_factor/threshold/external_input just enough
# to see whether the real path can physically carry a signal end to end