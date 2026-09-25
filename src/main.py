import pandas as pd
from pathlib import Path
import pyarrow.feather as feather
import pyarrow.dataset as ds
import duckdb

root = Path(__file__).resolve().parent.parent

neurons_file = root / 'data' / 'body-annotations-male-cns-v1.0-minconf-0.5.feather'

df = pd.read_feather(neurons_file)

def exploring_neurons():
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
    # the goal is to identify which neurons are for the specific use case

    one_neuron = traced.iloc[0]
    print(one_neuron)
    # the one neuron's type is DNp01, it controls escape behaviours

    # next step is to get the connectivity file, filter to just the interested neurons
    # think of it as the wiring

connections_file = root / 'data' / 'connectome-weights-male-cns-v1.0-minconf-0.5.feather'

# the goal is to filter the connections to something small to work with
# need to investigate the data via columns again
# feather.read_table with memory map = True uses less memory for such a large file
meta = feather.read_table(connections_file, memory_map=True)
print("schema: ", meta.schema)
print("rows: ", meta.num_rows)
# looks to be 3 int columns but too big to load in full. body_pre, body_post, weight

# look at 5 rows
print(meta.slice(0, 5).to_pandas())
# recognize that a neuron has a bodyId, so this table shows who talks to who. weight is how strong the connection is.

# again get the confirmed finished neurons
traced = df[df['status'] == 'Traced']

# need to tell what neuron is on either end of a connection via superclass, as superclass tells the general role
id_to_superclass = traced.set_index('bodyId')['superclass'].to_dict()
# this line makes bodyId the unique identifier for the df, and selects only the superclass column
# format is { id : superclass }

# again because the dataset is so big, a lazier loading method is used: .dataset
# do not use .read_table because it's build for reading only
dataset = ds.dataset(connections_file, format="feather")

batches = dataset.to_batches(columns=["body_pre", "body_post", "weight"])
# this essentially will give the data in chunks, not all at once

first_batch = next(batches) # pull a batch

sample = first_batch.to_pandas()
print(sample.shape) # see how big that batch is

sample['pre_sc'] = sample['body_pre'].map(id_to_superclass)
sample['post_sc'] = sample['body_post'].map(id_to_superclass)

print(sample.head())
#    body_pre  body_post  weight              pre_sc       post_sc
# 0     10352      10351    2591        ol_intrinsic  ol_intrinsic
# 1     13612      16076    2443        ol_intrinsic  ol_intrinsic
# 2     10663      10051    2248  visual_centrifugal  ol_intrinsic
# 3     10289      10611    2230  visual_centrifugal  ol_intrinsic
# 4     10893      10066    1929        ol_intrinsic  ol_intrinsic

# now we can see real readable connections i.e., optic lobe neuron talking to another optic lobe neuron
# weights seem to be in descending order

lookup = traced[['bodyId', 'superclass']]

con = duckdb.connect()

# settings: caps how much memory DuckDB is allowed to use
con.execute("PRAGMA memory_limit='6GB'")
con.execute("PRAGMA threads=2")

# key: it takes the dataframe as if it's a queryable table
con.register('lookup', lookup)
con.register('connections', meta)

flow_df = con.execute("""
    SELECT pre.superclass AS pre_sc, post.superclass AS post_sc, SUM(c.weight) AS total_weight
    FROM connections AS c
    JOIN lookup AS pre ON c.body_pre = pre.bodyId
    JOIN lookup AS post ON c.body_post = post.bodyId
    GROUP BY pre_sc, post_sc
    ORDER BY total_weight DESC
""").df()

print(flow_df.head(30))
#                 pre_sc             post_sc  total_weight
# 0         ol_intrinsic        ol_intrinsic    35690242.0
# 1         cb_intrinsic        cb_intrinsic    34364111.0
# 2        vnc_intrinsic       vnc_intrinsic    11040961.0
# 3         ol_intrinsic   visual_projection     7714137.0
# 4    visual_projection        cb_intrinsic     3847546.0
# 5         cb_intrinsic   descending_neuron     2732690.0
# 6        vnc_intrinsic           vnc_motor     2214497.0
# 7          vnc_sensory       vnc_intrinsic     1967945.0
# 8     ascending_neuron        cb_intrinsic     1872657.0
# 9           cb_sensory        cb_intrinsic     1785077.0
# 10   descending_neuron       vnc_intrinsic     1718740.0
# 11       vnc_intrinsic    ascending_neuron     1636228.0
# 12   visual_projection   visual_projection     1613964.0
# 13    ascending_neuron       vnc_intrinsic     1594252.0
# 14  visual_centrifugal        ol_intrinsic     1469887.0
# 15   visual_projection        ol_intrinsic     1321728.0
# 16   descending_neuron        cb_intrinsic      864565.0
# 17         vnc_sensory    ascending_neuron      783999.0
# 18        cb_intrinsic   visual_projection      680696.0
# 19    ascending_neuron    ascending_neuron      656576.0
# 20   descending_neuron   descending_neuron      598721.0
# 21    ascending_neuron   descending_neuron      572657.0
# 22        cb_intrinsic  visual_centrifugal      527964.0
# 23          ol_sensory        ol_intrinsic      443851.0
# 24         vnc_sensory         vnc_sensory      439444.0
# 25  visual_centrifugal   visual_projection      439005.0
# 26   descending_neuron    ascending_neuron      427455.0
# 27        cb_intrinsic          cb_sensory      371798.0
# 28        ol_intrinsic  visual_centrifugal      366826.0
# 29       vnc_intrinsic         vnc_sensory      365850.0

# a dominant pattern is that everything talks to itself (row 0 1 2)
# but other than that a pipeline is visible:
# ol_intrinsic > visual_projection > cb_instrinsic > descending_neuron > vnc_intrinsic
# translation: eyes > optic nerve > brain/decision > spinal cord > reflex/muscle
