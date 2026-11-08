# AI use and verification

This assignment permits AI assistance. The existing project draft names Claude / Claude Code as a coding assistant for the Python code, manifests, prompt, and first report draft. Codex was used to review the supplied work against the assignment, improve documentation, add the GitHub Actions workflow, and compile the technical report. Ollama `phi3.5` is the specified teacher model in the project design.

## What was checked in this checkout

- The provided `score.py` reports 99% valid JSON and 43% full-frame accuracy for the saved v1 student predictions, and 48% full-frame accuracy for the saved teacher predictions.
- The provided NACL simulator accepts all six sample packets; the subnet script prints the planned ranges.
- The local source passes `pyflakes`, and all 22 unit tests pass. The deliberate base-model CI run passed lint, tests, and secret scanning, then failed at the quality gate as intended. The Release-based trained-model CI run is pending.
- The report's numerical cluster claims were compared with files under `results/`. The rolling-update run has 2/39 non-200 responses (5.13%), which exceeds the assignment threshold; the HPA evidence does not show the full scale-up and scale-down cycle.

## Limits of verification

The teacher shard objects, cleaned training dataset, model files, and model Release were not present in the supplied checkout. These must be restored or regenerated before the training and deployment claims can be reproduced. The GitHub Actions workflow has been added, but its Release-based evaluation cannot pass until the Release asset is published. No result should be described as personally rerun unless that run was actually performed.
