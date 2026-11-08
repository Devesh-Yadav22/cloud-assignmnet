"""Cost-per-1000-requests estimator for Task 7, using data/rate_card.json."""
import argparse
import json
import os


def estimate(replicas, cpu_limit, mem_gib, rps, card):
    """Estimate hourly and per-1000-request costs from the supplied rate card."""
    if rps <= 0:
        raise ValueError("rps must be greater than 0")
    per_replica_hour = cpu_limit * card["vcpu_hour"] + mem_gib * card["gib_memory_hour"]
    hourly = replicas * per_replica_hour
    requests_per_hour = rps * 3600.0
    cost_per_1000 = hourly / requests_per_hour * 1000.0
    return {
        "per_replica_hour": round(per_replica_hour, 4),
        "hourly_all_replicas": round(hourly, 4),
        "requests_per_hour": round(requests_per_hour, 2),
        "cost_per_1000_requests": round(cost_per_1000, 4),
        "currency": card.get("currency", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicas", type=int, required=True)
    ap.add_argument("--cpu-limit", type=float, required=True, help="vCPU limit per replica")
    ap.add_argument("--mem-gib", type=float, required=True, help="memory limit (GiB) per replica")
    ap.add_argument("--rps", type=float, required=True, help="requests per second")
    ap.add_argument("--rate-card", default=os.path.join("data", "rate_card.json"))
    args = ap.parse_args()
    with open(args.rate_card, encoding="utf-8") as f:
        card = json.load(f)
    result = estimate(args.replicas, args.cpu_limit, args.mem_gib, args.rps, card)
    print(f"per replica/hour      {result['per_replica_hour']} {result['currency']}  "
          f"(= {args.cpu_limit}*{card['vcpu_hour']} + {args.mem_gib}*{card['gib_memory_hour']})")
    print(f"all {args.replicas} replicas/hour   {result['hourly_all_replicas']} {result['currency']}")
    print(f"requests/hour         {result['requests_per_hour']}  (= {args.rps} rps * 3600)")
    print(f"cost per 1000 reqs     {result['cost_per_1000_requests']} {result['currency']}")


if __name__ == "__main__":
    main()
