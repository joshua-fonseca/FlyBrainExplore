# FlyBrainExplore

> A working exploration of a real, 150M-row fly connectome, asking whether real neural wiring could support timed, rhythm-game-style responses, and along the way, a record of how to work through a large unfamiliar dataset carefully rather than quickly.

This is a personal project working through the [MaleCNS connectome](https://male-cns.janelia.org) dataset, a full synaptic-level map of a male *Drosophila* nervous system, released by Janelia and Google Research. It's a passion project first, fly neuroscience is genuinely interesting on its own, but it's written and documented the way I'd want a piece of real analysis work to be: assumptions checked before they're relied on, tools swapped out honestly when they stop working, and mistakes left visible rather than cleaned up after the fact.

**What's actually here:** careful exploration of a large real dataset (151M+ connectivity rows), a from-scratch neuron activity simulation (leaky integrate-and-fire), graph-based pathfinding across filtered subsets of real wiring, and two independently verified sensory-to-motor pathways, one visual, one auditory, checked against actual fly neuroscience literature rather than assumed from column names.

This project isn't finished, and it doesn't need to be to be worth reading. What matters more than the end result right now is how carefully each step was worked through.

## Project structure

```
FlyBrainExplore/
├── data/         raw and derived connectome data files (not all tracked in git)
├── src/          active work, notebooks exploring and simulating the connectome
│   └── legacy/   earlier script versions of the same work, kept as a record
```

More files will be added to `src/` as the project continues, so individual filenames aren't listed here, the structure above stays accurate regardless of how many notebooks exist at a given time.

## Getting started

Clone the repository and set up a virtual environment inside `src/`:

```shell
cd src
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Data files are expected under `data/`, see that folder for what's currently in use.

### Running the notebooks

Open any notebook in `src/` with the Jupyter extension in VS Code (or `jupyter lab`), and select the `.venv` interpreter as the kernel. Notebooks are generally self-contained but assume the folder structure above, running from a different location may break relative data paths.

## What's been explored so far

- Handled a large, messy real dataset (150M+ rows), switching tools when one stopped scaling: pandas, then PyArrow, then DuckDB
- Built a small neuron activity simulation (leaky integrate-and-fire) from scratch, to see signal actually move, not just structurally exist
- Used graph pathfinding to trace real sensory-to-motor routes through the wiring, weighted toward strong connections, not just short ones
- Found a real timing window, where two separate pulses combine to trigger a response that neither could alone
- Caught and fixed my own mistakes along the way, including a traced path that turned out to end at the wrong body part
- Traced a second, independent pathway from auditory input, checked against real published fly neuroscience

This project is ongoing, findings and direction are still being worked out as the data is better understood, and this README will keep changing to reflect that.

## Notes

A running cheat sheet of what the annotation columns mean, and what's been confirmed versus still unclear, lives alongside the notebooks in `src/`.