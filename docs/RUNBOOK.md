# Runbook — build, run, measure, submit

Exact commands for the parts that need a running cluster, plus the 4-day plan and commit schedule.
Capture every command's output into `results/` (e.g. `... | tee results/<name>.txt`) — that is the
evidence the report and marking need.

---

## Current verification status

The supplied `results/` directory contains scores, cluster logs, load-test output, and cost output.
The saved student predictions pass the local 95% JSON-validity gate (99% measured). The sample NACL
check passes 6/6. The source and reports are present.

The teacher shard objects, cleaned training file, model weights, and model Release are absent from
this checkout and the linked GitHub repository currently has no Release. Preserve or regenerate
those artifacts before claiming Tasks 1 and 2 are reproducible. The saved rollout run has 2/39
non-200 responses (5.13%), above the 0.5% criterion, and the HPA output does not show a 1→2→1 cycle.
Repeat those runs before claiming full Task 4 credit. Run CI after publishing the model asset, then
record a link to a deliberately failed base-model quality-gate run in the report.

The required handwritten reflection is a separate scanned file named `230101052.pdf`, at most
three pages, with the student's name, roll number, and repository link. It is distinct from
`report/report.pdf`, which is the typed technical report.

---

## Task-wise commit guide

Commit work after it has been checked. Keep real commit dates; do not backdate history.

| Day | Do | Commit (suggested message) |
|-----|----|----|
| **1** | Repo scaffold, Task 5 networking (verify `nacl_sim` 6/6, subnet calc), `make up` brings cluster + SeaweedFS up | `feat: repo scaffold, k3d+seaweedfs, task5 networking (nacl 6/6)` |
| **2** | Task 1 labelling (`ollama pull phi3.5`, `make label` or local), `make clean-data`; commit counts | `feat: task1 teacher labelling workers + clean.py (counts in results/)` |
| **3** | Task 2 training (`make train`, `make train-v2`, `make eval`), publish Release assets | `feat: task2 train pythia-70m student + eval vs teacher/base` |
| **4** | Task 3 container, Task 4 deploy+reliability, Task 6 CI, Task 7 load+cost, report, **tag final** | `feat: task3-7 service, k8s, ci, load test, cost, report` |

```bash
git add -A && git commit -m "<message for the day>"
git push                     # after you create the GitHub repo (see below)
# on day 4, after everything is in:
git tag final && git push --tags
```

### Publish the model as a Release
After training and verifying checksums, publish `v1.tar.gz` and `v2.tar.gz` under the
`model-v1` tag. To replace assets after retraining:
```bash
gh release upload model-v1 models/v1.tar.gz models/v2.tar.gz --clobber
```

---

## Task 1 — labelling evidence
```bash
make label
kubectl -n pipeline get pods -o wide | tee results/task1_workers.txt   # two pods, different index
make clean-data                                                        # writes results/clean_counts.json
```

## Task 4 — reliability tests (keep a load test running in another terminal where noted)

**Rolling update + rollback** (step 5):
```bash
# terminal A: load
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 4m \
  --host http://localhost:8080 --csv results/rollout | tee results/rollout.txt
# terminal B: while load runs
kubectl -n app set env deployment/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2
kubectl -n app rollout status deployment/command-parser
kubectl -n app rollout undo deployment/command-parser
kubectl -n app rollout status deployment/command-parser
```
Check `results/rollout_headers.json` for `X-Model-Version`: it should show v2 during, v1 after.
Failed requests must stay ≤ 0.5%.

**Recovery** (step 6) — delete a Pod under load:
```bash
kubectl -n app delete pod "$(kubectl -n app get pod -l app=command-parser -o name | head -1)"
kubectl -n app get pods -w | tee results/recovery.txt   # replica count returns to 2
```

**Cold start** (step 7) — three runs, report the median; show the model download in the logs:
```bash
for i in 1 2 3; do
  kubectl -n app delete pod -l app=command-parser
  start=$(date +%s)
  kubectl -n app wait --for=condition=ready pod -l app=command-parser --timeout=600s
  echo "run $i cold start: $(( $(date +%s) - start ))s"
done | tee results/coldstart.txt
kubectl -n app logs -l app=command-parser --tail=20 | tee results/coldstart_logs.txt   # shows the S3 download
```

**Load balancing** (step 8) — exactly two Ready replicas, read per-replica counts:
```bash
kubectl -n app scale deployment/command-parser --replicas=2
make load                                               # writes results/loadtest_headers.json
cat results/loadtest_headers.json                        # each replica should serve >= 30%
```

## Task 7 — performance, resources, cost
```bash
make load                                                # results/loadtest_stats.csv (p50, p95, rps, failures)
kubectl -n app top pods | tee results/top_pods.txt       # CPU + memory per pod during load
python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps <rps_from_csv> | tee results/cost.txt
```

## Container size + limits (Task 3)
```bash
docker images cloud-mini/service:v1 --format '{{.Size}}' | tee results/image_size.txt   # <= 2 GB
docker run --rm --cpus 1 --memory 1g ... cloud-mini/service:v1   # send 50 requests, watch for OOM
```
