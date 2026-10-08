"""Audit transcript joins and completeness; print only aggregate counts and hashes."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys


def file_digest(path):
    h = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def audit(files):
    starts, ends, requests, outputs = {}, {}, Counter(), Counter()
    cited, artifacts = set(), []
    for run in files:
        trace = run.parent / "traces" / f"{run.stem}.traces.jsonl.gz"
        if not trace.exists():
            trace = trace.with_suffix("")
        if not trace.exists():
            raise ValueError(f"Missing trace for {run.name}")
        opener = gzip.open if trace.suffix == ".gz" else open
        with opener(trace, "rt") as stream:
            for line in stream:
                row = json.loads(line)
                tid, kind = row["trace_id"], row["kind"]
                if kind == "start":
                    if tid in starts:
                        raise ValueError("Duplicate trace start")
                    if row["value"].get("offline_fixture"):
                        raise ValueError("Offline fixture entered a live run")
                    starts[tid] = row["value"]
                elif kind == "end":
                    if tid in ends:
                        raise ValueError("Duplicate trace end")
                    ends[tid] = row["value"]
                elif kind == "request":
                    requests[tid] += 1
                elif kind == "provider_stream":
                    outputs[tid] += 1
        with run.open() as stream:
            for line in stream:
                row = json.loads(line)
                if row.get("type") != "episode":
                    continue
                for call in row.get("calls", []):
                    backend = call.get("backend") or {}
                    records = [backend, *backend.get("retries", [])]
                    for record in records:
                        if record.get("trace_id"):
                            cited.add(record["trace_id"])
        artifacts.append({"file": trace.name, "sha256": file_digest(trace), "bytes": trace.stat().st_size})
    missing = cited - starts.keys()
    incomplete = starts.keys() - ends.keys()
    if missing or incomplete:
        raise ValueError(f"Trace audit failed: {len(missing)} missing joins, {len(incomplete)} interrupted traces")
    answered = [tid for tid, end in ends.items() if end["outcome"] in ("answer", "no_answer")]
    if any(requests[tid] != 1 or not outputs[tid] for tid in answered):
        raise ValueError("Answered call lacks its single request or provider stream")
    return {"tries": len(starts), "answered_tries": len(answered), "cited_tries": len(cited),
            "uncited_tries": len(starts.keys() - cited), "missing_joins": 0, "interrupted_traces": 0,
            "trace_files": artifacts}


if __name__ == "__main__":
    print(json.dumps(audit([Path(path) for path in sys.argv[1:]]), indent=2))
