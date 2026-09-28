# Graph traversal
# Finding a path from the eyes (ol_sensory) to the motor neurons (vnc_motor)

# The idea: the toy LIF in 01_lif.py only went one hop deep, so the charge had nowhere further to go
# - instead of hand querying neighbours of neighbours, let a graph do the walking
# - the graph structurally shows how neurons are connected, it does not simulate any charge moving
# - the shortest path is a question of structure (is there a route?), LIF is a question of dynamics (does charge survive it?)

# the goal is to find a real ol_sensory -> vnc_motor path
# - then that path (and its neurons/edges) can be handed back to the LIF to see if the charge dies before reaching vnc_motor

# dependencies recreated from 01_lif.py
import pandas as pd
from pathlib import Path

root = Path(__file__).resolve().parent.parent
neurons_file = root / 'data' / 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
df = pd.read_feather(neurons_file)

connections_file = root / 'data' / 'connectome-weights-male-cns-v1.0-minconf-0.5.feather'

id_to_superclass = df[df['status'] == 'Traced'].set_index('bodyId')['superclass'].to_dict()

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