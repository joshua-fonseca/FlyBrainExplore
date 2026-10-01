# malecns body-annotations column cheat sheet

source file: `body-annotations-male-cns-v1.0-minconf-0.5.feather`
211,577 rows (all annotated bodies), 36 columns.

confidence key: confirmed (from official docs/paper), inferred (from pattern/context), unclear (worth digging into further).

## useful now

these are the columns worth exploring first, they tell you what kind of neuron something is and its basic identity.

| column | what it means | example | confidence |
|---|---|---|---|
| `status` | broad proofreading/qc bucket. `Traced` means confirmed real, finished neuron (about 165k of these, this is where the "166k neurons" number comes from). others (`Orphan`, `Glia`, `Unimportant`, `Assign`, `Anchor`) are unfinished, non-neuronal, or excluded segments. | `Traced` | confirmed |
| `statusLabel` | finer grained version of `status`, same idea, more qc stages (e.g. `Roughly traced` vs `Reviewed` vs `Prelim Roughly traced`). | `Reviewed` | confirmed |
| `superclass` | the broadest classification bucket, where in the nervous system it lives and its general role (optic lobe, central brain, vnc, sensory, motor, etc). | `vnc_motor` | confirmed |
| `class` | a level down from `superclass`, narrower grouping. exact meaning depends on which superclass it's under. run `df[df.superclass=='X']['class'].value_counts()` to see it in context. | varies by superclass | inferred |
| `subclass` | a level down from `class`. for vnc neurons, often ties to hemilineage (developmental origin group). | `hl` | inferred |
| `supertype` | groups related fine grained `type`s together, sits between `subclass` and `type` in specificity. | varies | inferred |
| `type` | the finest grained systematic name for this neuron, specific to one functional/anatomical group. this is the most useful column for "what kind of neuron is this." | `MNhl29` | confirmed |
| `instance` | a specific instance name for one physical neuron, usually the `type` plus a side/number suffix, so it's unique per neuron rather than shared across a type. | `MNhl29_R` | inferred |
| `somaSide` | which side of the body the cell body sits on. | `L`, `R`, or `M` (midline) | confirmed |
| `somaNeuromere` | which body segment the cell body sits in, relevant mainly for vnc neurons (thoracic/abdominal segments, like a fly's version of spinal segments). | `T2` (mesothoracic) | confirmed |

`somaSide` and `somaNeuromere` are independent, not a hierarchy, one isn't a narrower version of the other. side answers left/right, neuromere answers which segment, front to back. a neuron can be any combination of the two, e.g. an `A1` neuron can exist on either the left or right side, same as a `T2` neuron can. checking both gives two separate facts about a neuron, not two levels of the same fact.

---

## can ignore for now

identifiers, cross references to other datasets, spatial coordinates, and specialized annotations. not useless, just not needed for a first pass.

| column | what it means | example | confidence |
|---|---|---|---|
| `bodyId` | unique numeric id for this segment/neuron, the primary key of the dataset. every table that references a neuron uses this id, so you'll need it eventually just not for exploring types. | `556329` | confirmed |
| `rootSide` | side of the segmentation "root" point (a technical anchor point in the 3d reconstruction), may or may not match `somaSide`. worth comparing the two columns directly to see if/when they differ. | `L`/`R`/`M` | unclear |
| `somaLocation` | 3d spatial coordinates of the cell body (x, y, z). stored as an array, which is why `.nunique()` crashed on it earlier. | `[x, y, z]` | confirmed |
| `tosomaLocation` | a reference point/vector related to soma position, likely used for orienting the skeleton toward the soma. exact technical definition unclear from public docs. | array, like somaLocation | unclear |
| `entryNerve` | for sensory neurons only, which physical cable bundle this neuron's fiber travels through to get into the brain/nerve cord from the outside world. checked values: `AN` (antennal nerve) confirmed by cross-referencing `class`/`type`, carries both `olfactory` and `mechanosensory` (including `JO`) neurons. `MxLbN`, `aPhN`, `PhN`, `ON` seen but not yet checked the same way. | `AN` | confirmed |
| `exitNerve` | for motor neurons only, which physical cable bundle this neuron's fiber travels through to leave the brain/nerve cord on its way to a muscle. | `AbN2` | confirmed |
| `receptorType` | not a general sensory-modality label despite the name. only populated for `vnc_sensory`, not `cb_sensory` (checked directly, came back empty there). the actual values seen (`ppk23`, `ppk25`, `IR52b`) are specific gene names tied to pheromone detection, species recognition, and courtship behavior, not a general "what sense is this" field. | `ppk23` | confirmed |
| `serialMotif` | identifies which serially repeating set of homologous neurons this one belongs to (many neuron types repeat once per body segment). | varies | inferred |
| `mancSerial` / `mcnsSerial` | position number within a serial motif set, in the manc dataset vs this malecns dataset respectively. | integer | inferred |
| `group` | a grouping id, likely clusters neurons considered functionally/connectionally similar during annotation. exact criteria not confirmed. | varies | unclear |
| `birthtime` | developmental timing category, whether the neuron is "early born"/"primary" or "late born"/"secondary" in development. | binary, only 2 unique values | inferred |
| `dimorphism` | notes whether this neuron shows male/female anatomical differences, relevant since this is specifically the male cns. | varies | inferred |
| `fruDsx` | whether this neuron expresses the sex determination genes fruitless (`fru`) and/or doublesex (`dsx`), tied to sexually dimorphic circuits. | varies | inferred |
| `matchingNotes` | free text notes explaining how/why a cross dataset match (to flywire, hemibrain, manc, etc) was made, including caveats. | free text | inferred |
| `synonyms` | alternate names this neuron is known by in the literature. | free text | inferred |
| `flywireType` | matching type name in the flywire connectome (a female fly brain dataset), cross reference for comparing the same neuron across datasets. | varies | confirmed |
| `hemibrainType` | matching type name in the "hemibrain" dataset (an earlier, partial fly brain connectome). | varies | confirmed |
| `mancType` / `mancBodyid` / `mancGroup` | matching type name / id / group in the manc dataset (male adult nerve cord, a separate but related connectome of just the nerve cord). | `MNhl29` | confirmed |
| `vfbId` | cross reference id into virtual fly brain, an external fly anatomy database/viewer. | `VFB_jrmc20kh` | confirmed |
| `itoleeHl` | hemilineage label under the ito/lee classification scheme, hemilineages are groups of neurons born from the same neural stem cell lineage during development. | varies | inferred |
| `trumanHl` | hemilineage label under an alternate (truman lab) naming scheme for the same underlying developmental lineages. | varies | inferred |
| `assignedOlHex1` / `assignedOlHex2` | coordinates on the optic lobe's hexagonal grid, the fly visual system is organized into repeating columns arranged in a hex pattern, and these two values likely give a column's grid address. only populated for optic lobe neurons (note the high `NaN` count). | varies | inferred |

don't confuse `entryNerve`/`exitNerve` with `weight`. `weight` is a specific, one-to-one fact, how strong the link is between exactly one neuron and one other neuron. `entryNerve`/`exitNerve` is more like a shared neighbourhood or a shared street, many different neurons, wired to completely different places, can all travel through the same named nerve bundle on their way in or out, without being connected to each other at all. one tells you the strength of a specific link, the other tells you the general corridor a neuron's wire passes through, not who it's actually talking to.

---

## superclass values

the `superclass` column has 27 possible values (26 named plus `nan` for unclassified rows). prefix tells you the region, suffix tells you the role. `_tbc` suffix appears to mean "to be confirmed", a provisional label, not officially documented so treat as unclear.

region prefixes: `ol` = optic lobe (vision), `cb` = central brain, `vnc` = ventral nerve cord (the fly's spinal cord equivalent), `sensory`/`visual`/`efferent`/`ascending`/`descending` with no region prefix = the role itself is the main distinguishing feature, cutting across regions. `ENS` = enteric nervous system (gut).

| value | what it means | human analogy | confidence |
|---|---|---|---|
| `ol_sensory` | primary visual input, the photoreceptors themselves. | your retina, the first cells that catch light. | inferred |
| `ol_intrinsic` | neurons that live and process entirely within the optic lobe, don't leave it. | the wiring right behind your eye that starts sorting out shapes and movement before anything reaches your brain. | confirmed |
| `visual_projection` | neurons that carry processed visual signal out of the optic lobe into the central brain. | your optic nerve, the cable that carries what your eye already sorted out over to your brain. | confirmed |
| `visual_centrifugal` | neurons that send signal backward, from central brain back into the optic lobe. | your brain reaching back to adjust what your eye pays attention to, like a spotlight it points on purpose. | confirmed |
| `cb_sensory` | sensory input arriving directly into the central brain, not through the optic lobe or vnc (e.g. antennae, mouthparts). confirmed example: `JO-B1_a` auditory neurons classify here, since the antennal nerve carries straight to the central brain rather than through the vnc. | smell or taste signals going straight to your brain, skipping your spine entirely. | confirmed |
| `cb_intrinsic` | neurons that live and process entirely within the central brain. | the part of your brain doing actual thinking and deciding, not just passing signals along. | confirmed |
| `cb_motor` | motor neurons that originate in the central brain (not vnc), likely controlling head/mouthpart movement. | the nerves that move your face and jaw, separate from the ones that move your arms and legs. | inferred |
| `cb_efferent` | central brain neurons sending output directly to the periphery, bypassing the vnc. | your brain sending a command straight to a muscle near your head, skipping your spine. | inferred |
| `cb_endocrine` | central brain neurons that release hormones rather than firing chemical/electrical synapses. | the part of your brain that releases hormones instead of sending nerve signals. | confirmed |
| `descending_neuron` | carries a signal from the central brain down into the vnc, a command. | your brain telling your body what to do, sent down through your spine. | confirmed |
| `ascending_neuron` | carries a signal from the vnc up into the central brain, a status report. | your spine sending feeling and status back up to your brain. | confirmed |
| `vnc_sensory` | sensory input arriving directly into the vnc (legs, wings, body surface). | touch sensors in your limbs that feed straight into your spine. | confirmed |
| `vnc_intrinsic` | neurons that live and process entirely within the vnc. | a quick reflex, like pulling your hand off something hot before your brain even gets involved. | confirmed |
| `vnc_motor` | motor neurons originating in the vnc, drive the legs/wings/flight muscles directly. | the last nerve in the chain, the one directly attached to your leg muscle. | confirmed |
| `vnc_efferent` | vnc neurons sending output to the periphery, similar role to vnc_motor but a distinct annotation bucket. | a nerve leaving your spine toward your body, but not necessarily to a muscle. | unclear |
| `vnc_endocrine` | vnc neurons that release hormones. | hormone-releasing cells sitting along your spine instead of your brain. | inferred |
| `sensory_ascending` | sensory neurons whose signal is heading upward toward the brain, may overlap conceptually with vnc_sensory/ascending_neuron. | similar to ascending_neuron, exact difference from vnc_sensory not confirmed. | unclear |
| `sensory_descending` | sensory neurons whose signal or fiber projects downward, rare category. | no simple everyday comparison found yet, exact meaning unclear. | unclear |
| `efferent_ascending` | very rare category (single digit count), output type neuron traveling upward, exact meaning not confirmed. | no simple comparison found yet, worth checking directly if it matters to your project. | unclear |
| `efferent_descending` | output type neuron traveling downward, distinct from descending_neuron in the annotation scheme, exact distinction unclear. | possibly a more specific version of the "brain sends a command down" pathway above. | unclear |
| `ENS` | enteric nervous system, neurons controlling the gut, largely independent of the main brain/vnc circuits. | your own gut has its own separate nerve network too, sometimes called a "second brain." same idea here. | confirmed |
| `cb_sensory_tbc` / `visual_projection_tbc` / `sensory_ascending_tbc` / `vnc_sensory_tbc` / `vnc_tbc` | provisional versions of the categories above, annotation not fully finalized yet. | a rough first guess at the label, not double-checked yet. | unclear |
| `nan` | no superclass assigned, likely correlates with non-traced/non-neuronal rows (orphan, glia, unimportant, etc, see `status` above). | a record with no label at all. | inferred |

---

## finding: side (left/right) is missing for almost all sensory neurons

`somaSide` tells you which side of the body a neuron sits on, and it's marked `confirmed` above, meaning the column works correctly when it has a value. but whether it actually *has* a value turns out to depend heavily on what kind of neuron you're looking at.

checked across the whole dataset: almost every sensory neuron, whether it's for seeing, hearing, smell, touch, or anything else, is missing its side. some sensory groups are missing it 100% of the time, and the rest are still above 97%. meanwhile, almost every other kind of neuron, the ones that process, decide, or move something, has its side filled in essentially all the time.

so the rule of thumb: if a neuron is a sensory neuron, don't expect to know which side it's on from this column, that information mostly just isn't there. for anything else, it's safe to trust.

why this might be true (a guess, not confirmed): sensory neurons tend to repeat many times over, thousands of near-identical photoreceptors, thousands of near-identical hearing neurons, while neurons like the Giant Fiber are one-of-a-kind and individually important. it's possible the people labeling this data prioritized the unique, important neurons and didn't get around to labeling the side for every single repeated sensory cell.

## granularity: superclass -> class -> subclass -> supertype -> type -> instance

these six columns aren't independent, they're one hierarchy, each level narrowing the one before it. broadest first:

```
superclass  ->  class  ->  subclass  ->  supertype  ->  type  ->  instance
(region+role)  (varies)   (often       (groups        (specific    (one physical
                           hemilineage)  related types)  identity)   neuron)
```

`superclass` is the only level guaranteed populated for every traced neuron. the middle three (`class`, `subclass`, `supertype`) are inconsistently filled, present for some neurons and `NaN` for others, and their exact meaning shifts depending on which `superclass` you're under (see the "run `df[df.superclass=='X']['class'].value_counts()`" note in the table above). `type` is the level that's consistently useful and consistently populated, it's the one this project has actually relied on throughout. `instance` only matters once you need a specific physical neuron rather than a category, it's `type` plus a side/number suffix.

traced examples from this project, showing the levels that were actually populated for each:

| superclass | class | type | instance | what it took to confirm this was the right level to pick from |
|---|---|---|---|---|
| `ol_sensory` | `visual` | `R1-R6` | (not checked) | had to check `type` under `ol_sensory` to find `R7`/`R8`/`HBeyelet` sitting alongside it, picking `superclass` alone wasn't enough |
| `cb_sensory` | (not checked) | `JO-B1_a` | (not checked) | had to go past `superclass`/`entryNerve` entirely, down to `type`, split further by an external source (JO-A vs JO-B) not visible in any single column |
| `vnc_motor` | (not checked) | `MNad21` | (not checked) | `type` alone didn't warn this was abdominal, that only showed up in `somaNeuromere`, a column outside this hierarchy entirely |

the practical rule this project landed on (see "never trust the first row" below): `superclass` tells you the general neighborhood, but `type` is usually the minimum level needed before treating a neuron as representative of anything. for motor neurons specifically, `type` alone still wasn't enough, `somaNeuromere`/`exitNerve` (outside this hierarchy, in the "can ignore for now" table above) turned out to carry the detail that actually mattered.

## lesson: never trust the first row

a category that looks like one thing can secretly hold several different things inside it. grabbing the first row from a category, without checking what else is in there, is a real risk, not just being careful for no reason.

concrete cases this bit:
- the antenna carries both smell and hearing. picking a random antenna neuron could easily land on smell instead of hearing, they look the same at a glance.
- within the eye's light-sensing cells, most of them detect motion and brightness, but a few detect color instead, and a rare handful aren't even used for seeing shapes at all, they help the fly track light and time of day. the first pick this project made happened to be a motion-detecting one, which was the right kind, but that was luck, not something checked ahead of time.
- within the leg/wing motor neurons, most control the legs, but some control the abdomen instead, a completely different body part. one path this project traced turned out to end at an abdomen neuron, not a leg one, and that was only caught after actually checking which body segment it belonged to.

the fix going forward: before treating any single neuron as representative of a whole group, look at what's actually inside that group first, and double check that the specific one picked is really in the sub-group wanted.

## things worth verifying yourself as you go

the unclear rows are the ones where a solid public definition wasn't findable, that's a good "next question" list:

```python
# compare rootSide vs somaSide directly
print((df['rootSide'] == df['somaSide']).value_counts())

# look at group in context
print(df[['group','type','superclass']].dropna(subset=['group']).head(10))
```

compiled from the malecns download page, the companion manc paper (marin et al./takemura et al.), and virtual fly brain neuron records. not an official janelia document, treat the unclear and inferred rows as a starting point, not gospel.