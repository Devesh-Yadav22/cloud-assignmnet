# Submission verification (CS3081)

Repository: https://github.com/Devesh-Yadav22/cloud-assignmnet  
Student: Devesh, 230101052

This list separates source files and saved output from checks that still need a successful run. A saved log is evidence of its recorded values; it does not replace a missing model artifact or a missing GitHub Actions run.

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Task 1: k3d, SeaweedFS, parallel labeling, clean data | Manifests, worker, counts JSON | Teacher shards and cleaned dataset must be restored or regenerated; checksum must be checked. |
| Task 2: v1/v2 models, Release, evaluation | Training code and saved scores; v1 predictions pass 95% gate | No model files or GitHub Release asset yet. |
| Task 3: service and container | API code, tests, saved image-size and endpoint output | Separate 50-request constrained run is not in the saved evidence. |
| Task 4: deployment and reliability | Manifests and cluster logs | Rollout 2/39 non-200 (5.13%) exceeds 0.5%; HPA 1→2→1 cycle and recovery-window failure rate are missing. |
| Task 5: subnet and NACL | Subnet plan and 6/6 sample packet check | Locally verified. |
| Task 6: CI and quality gate | Workflow, 22 passing local tests, 99% saved-prediction validity; [base-model run failed at the gate](https://github.com/Devesh-Yadav22/cloud-assignmnet/actions/runs/42484822377) | Release-based trained-model CI run pending. |
| Task 7: load and cost | 90-second cluster run and cost output | Assignment specifies a 2-minute standard Locust run. |
| Typed report | `report/report.pdf` | Compiled and visually checked; three pages. |
| Handwritten reflection | `report/reflection_draft.md` | Student's handwritten scan is required as `230101052.pdf`, at most three pages. |
| Final tag | None until all required assets and evidence are verified | Tag the actual final commit as `final` and push the tag. |

Do not commit `.env`, `models/`, or `datasets/`. Publish model archives as GitHub Release assets and keep training datasets in SeaweedFS. Update the report with new measurements when pending runs are completed.
