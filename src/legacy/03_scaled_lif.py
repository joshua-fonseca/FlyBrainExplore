import pandas as pd
from pathlib import Path

root = Path(__file__).resolve().parent.parent
neurons_file = root / 'data' / 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
df = pd.read_feather(neurons_file)

id_to_superclass = df[df['status'] == 'Traced'].set_index('bodyId')['superclass'].to_dict()

filtered_path = root / 'data' / 'pipeline_edges_filtered.feather'
strong_only = pd.read_feather(filtered_path)

# the path found in 02_graph.py
path = [14428, 13984, 10286, 11974, 10680, 164190]

# every edge where BOTH ends are one of these 6 neurons
path_edges = strong_only[
    strong_only['body_pre'].isin(path) & strong_only['body_post'].isin(path)
]
print(path_edges)

#           body_pre  body_post  weight             pre_sc            post_sc
# 6322824      10680      11974       5  descending_neuron       cb_intrinsic
# 6324876      10680     164190      78  descending_neuron          vnc_motor
# 10227568     14428      13984      74         ol_sensory  visual_projection
# 11913142     10286      13984       9  descending_neuron  visual_projection
# 11913888     10286      11974      92  descending_neuron       cb_intrinsic
# 11930105     10286     164190      10  descending_neuron          vnc_motor
# 13407577     11974      10286       4       cb_intrinsic  descending_neuron
# 13408386     11974      10680      41       cb_intrinsic  descending_neuron
# 17544937     13984      10286      45  visual_projection  descending_neuron

# Notice:
# There's a shortcut: 10286 -> 164190, and there are backwards jumps again.

# from 01_lif.py
neuron_ids = path
charge = {nid: 0 for nid in neuron_ids}
edges = list(path_edges[['body_pre', 'body_post', 'weight']].itertuples(index=False, name=None))

decay_factor = 0.8
threshold = 42 # 40 -> 42
time_steps = 16
external_input = {14428: 100}

for t in range(time_steps):
    print(f"--- time step {t+1} ---")

    # apply external input only at the very first tick
    if t == 0 or t == 10:
        for nid, amount in external_input.items():
            print("external applied to", nid)
            charge[nid] += amount

    # figure out who fires this tick, based on charge BEFORE any resets happen
    fired = [nid for nid in neuron_ids if charge[nid] >= threshold]
    print("fired:", fired)

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

# what is learned from this?
# - Firing clears a neuron's charge, and a near miss doesn't
# - That might have a consequence for the rhythm game
# - A single isolated pulse and a rapid train of pulses behave very differently in this model

# New term: temporal summation
# - Charge from events that are separated in time can still add up, as long as the leak hasn't drained it first

# KEY: A timing "window"

# Remember:
# - 10680 is a bucket with a rim at 42. Once the water reaches 42, it fires.
# - Each pulse that comes down the chain pours 41 into it.
# - The bucket leaks 20% of its water every tick.

# What happens with two pulses:
# - The first pulse leaves the bucket at 41. It doesn't fire, but it isn't empty either. Then the leak starts draining it.
# - When the second pulse arrives, it pours in another 41, and the question is:
# - does the water still in the bucket, plus the 41, reach 42?

# So the window is just: how long does the leftover stay at 1 or more?
# - For this particular bucket, after 17 ticks energy is fired, 0.9 is leftover and 41 is received,
# the bucket won't fire to meet the 42 threshold

# The takeaway is that the circuit remembers the first pulse for about 16 ticks
# and can combine it with a later one. After that, the memory is gone.

# Sumamry:
# - the window is the longest gap between two pulses where the leftover water, plus the new pour, still reaches the rim
# - Past that gap, the leftover has drained too far and the second pulse is treated like a first one
# - The window belongs to the weak link, not the whole path.
# - 10680 is the only neuron here that needs leftover charge, because its pour (41) is below its rim (42).
# - A higher rim shrinks the window.
# - A slower leak widens it.

# There is now math involved.
# How to calculate the window: how many ticks the leftover survives before it drops below what's needed?
# - The pour is 41 and the rim is 42, so the bucket needs at least 1 unit left over
# - Each tick multiplies the leftover by the decay factor
# - So you count how many ticks it takes for 41 to shrink below 1

# leftover = 41
# k = 0
# while leftover * decay >= 1:
#     leftover *= decay
#     k += 1
# print(k)

# With decay = 0.8 this prints 16, and with 0.9 it prints 35. 35/16 * 100 = 218% increase of window
# formula version, it's k = ln(41) / -ln(decay), then round down

# ---------------------------------------------

# What does this mean for input design?
# Everything in the simulation turns into a design choice for stage 1

# The response has a fixed delay
# In the scaled LIF, a pulse takes 5 ticks to get from 14428 to 164190 (Eyes to body)
# So to press something on beat, inject the input 5 ticks early

# The threshold decides what one input can do
# At threshold <= 41, a single pulse always gets through, so the fly presses on any input.
# At threshold = 42, a single pulse fails, and you need two pulses within the window.
# The second setup gives you a natural design: an arrow appearing is the first pulse,
# and the arrow reaching the hit line is the second. 
# The fly only presses if the second follows the first closely enough.

# The window becomes the tempo tolerance

# A tick needs a real length: it will be some number of ms

# Where the external input is injected matters
# Some photo receptors reach 80,350 neurons and some reach only 5, so pick a well-connected one like 14428