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

## can ignore for now

identifiers, cross references to other datasets, spatial coordinates, and specialized annotations. not useless, just not needed for a first pass.

| column | what it means | example | confidence |
|---|---|---|---|
| `bodyId` | unique numeric id for this segment/neuron, the primary key of the dataset. every table that references a neuron uses this id, so you'll need it eventually just not for exploring types. | `556329` | confirmed |
| `rootSide` | side of the segmentation "root" point (a technical anchor point in the 3d reconstruction), may or may not match `somaSide`. worth comparing the two columns directly to see if/when they differ. | `L`/`R`/`M` | unclear |
| `somaLocation` | 3d spatial coordinates of the cell body (x, y, z). stored as an array, which is why `.nunique()` crashed on it earlier. | `[x, y, z]` | confirmed |
| `tosomaLocation` | a reference point/vector related to soma position, likely used for orienting the skeleton toward the soma. exact technical definition unclear from public docs. | array, like somaLocation | unclear |
| `entryNerve` | for sensory/afferent neurons, which peripheral nerve this neuron enters the cns through. | `adult metathoracic leg nerve` | confirmed |
| `exitNerve` | for motor/efferent neurons, which peripheral nerve this neuron exits the cns through. | `adult first abdominal nerve` | confirmed |
| `receptorType` | sensory modality this neuron is associated with (e.g. mechanosensory, chemosensory), for sensory neurons only. | varies | inferred |
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

## superclass values

the `superclass` column has 27 possible values (26 named plus `nan` for unclassified rows). prefix tells you the region, suffix tells you the role. `_tbc` suffix appears to mean "to be confirmed", a provisional label, not officially documented so treat as unclear.

region prefixes: `ol` = optic lobe (vision), `cb` = central brain, `vnc` = ventral nerve cord (the fly's spinal cord equivalent), `sensory`/`visual`/`efferent`/`ascending`/`descending` with no region prefix = the role itself is the main distinguishing feature, cutting across regions. `ENS` = enteric nervous system (gut).

| value | what it means | human analogy | confidence |
|---|---|---|---|
| `ol_sensory` | primary visual input, the photoreceptors themselves. | the retina, the very first cells that catch light. | inferred |
| `ol_intrinsic` | neurons that live and process entirely within the optic lobe, don't leave it. | local circuitry in the retina/early visual cortex doing edge/motion detection before signal goes anywhere else. | confirmed |
| `visual_projection` | neurons that carry processed visual signal out of the optic lobe into the central brain. | the optic nerve, the cable carrying "already partly processed" visual info from eye to brain. | confirmed |
| `visual_centrifugal` | neurons that send signal backward, from central brain back into the optic lobe. | feedback wiring, the brain "tuning" what the eye pays attention to, like top down attention. | confirmed |
| `cb_sensory` | sensory input arriving directly into the central brain, not through the optic lobe or vnc (e.g. antennae, mouthparts). | smell/taste/touch signals reaching the brain directly, not via the spinal cord. | confirmed |
| `cb_intrinsic` | neurons that live and process entirely within the central brain. | the "thinking" part of the brain, local associative circuitry, decision making. | confirmed |
| `cb_motor` | motor neurons that originate in the central brain (not vnc), likely controlling head/mouthpart movement. | cranial nerves controlling your face/jaw, as opposed to spinal nerves controlling limbs. | inferred |
| `cb_efferent` | central brain neurons sending output directly to the periphery, bypassing the vnc. | a brain signal that skips the spinal cord entirely and goes straight to a gland or muscle near the head. | inferred |
| `cb_endocrine` | central brain neurons that release hormones rather than firing chemical/electrical synapses. | the hypothalamus, the brain region that controls hormone release. | confirmed |
| `descending_neuron` | carries a signal from the central brain down into the vnc, a command. | upper motor neurons in your spinal cord, brain telling the body what to do. | confirmed |
| `ascending_neuron` | carries a signal from the vnc up into the central brain, a status report. | sensory tracts running up your spinal cord telling the brain what the body is feeling. | confirmed |
| `vnc_sensory` | sensory input arriving directly into the vnc (legs, wings, body surface). | touch/proprioception sensors in your limbs feeding straight into the spinal cord. | confirmed |
| `vnc_intrinsic` | neurons that live and process entirely within the vnc. | local spinal cord circuits, like the reflex arc that pulls your hand off a hot stove without waiting for the brain. | confirmed |
| `vnc_motor` | motor neurons originating in the vnc, drive the legs/wings/flight muscles directly. | lower motor neurons in your spinal cord, the final link to your leg muscles. | confirmed |
| `vnc_efferent` | vnc neurons sending output to the periphery, similar role to vnc_motor but a distinct annotation bucket. | output nerves leaving the spinal cord toward the body, not necessarily to a skeletal muscle. | unclear |
| `vnc_endocrine` | vnc neurons that release hormones. | hormone-releasing cells located along the spinal cord rather than the brain. | inferred |
| `sensory_ascending` | sensory neurons whose signal is heading upward toward the brain, may overlap conceptually with vnc_sensory/ascending_neuron. | same idea as ascending_neuron, exact distinction between this and vnc_sensory not confirmed from public docs. | unclear |
| `sensory_descending` | sensory neurons whose signal or fiber projects downward, rare category. | not confidently mapped to a clean human analogy, exact distinction unclear. | unclear |
| `efferent_ascending` | very rare category (single digit count), output type neuron traveling upward, exact meaning not confirmed. | no confident analogy, flagged for verifying directly in data if it matters to your project. | unclear |
| `efferent_descending` | output type neuron traveling downward, distinct from descending_neuron in the annotation scheme, exact distinction unclear. | possibly a finer subtype of the descending command pathway. | unclear |
| `ENS` | enteric nervous system, neurons controlling the gut, largely independent of the main brain/vnc circuits. | your own enteric nervous system, sometimes called the "second brain", the gut's semi-autonomous nerve network. same term used in human biology. | confirmed |
| `cb_sensory_tbc` / `visual_projection_tbc` / `sensory_ascending_tbc` / `vnc_sensory_tbc` / `vnc_tbc` | provisional versions of the categories above, annotation not fully finalized yet. | a draft label, "probably this bucket, not double checked yet." | unclear |
| `nan` | no superclass assigned, likely correlates with non-traced/non-neuronal rows (orphan, glia, unimportant, etc, see `status` above). | an unlabeled record. | inferred |

## things worth verifying yourself as you go

the unclear rows are the ones where a solid public definition wasn't findable, that's a good "next question" list:

```python
# compare rootSide vs somaSide directly
print((df['rootSide'] == df['somaSide']).value_counts())

# look at group in context
print(df[['group','type','superclass']].dropna(subset=['group']).head(10))
```

compiled from the malecns download page, the companion manc paper (marin et al./takemura et al.), and virtual fly brain neuron records. not an official janelia document, treat the unclear and inferred rows as a starting point, not gospel.