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
