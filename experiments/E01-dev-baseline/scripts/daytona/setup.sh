#!/usr/bin/env bash
# setup.sh REPO REVISION NAME   box bootstrap (from the 2026-10-04 dev36 pilot): uv, vLLM 0.30.0 in a venv, the model
# at a pinned revision (download in parallel with the install), every LFS file's SHA-256 checked against the Hub's.
# No zendo-bench code or secret comes here: only the model server runs on the box.
set -uo pipefail
REPO=${1:?REPO}; PIN=${2:?REVISION}; NAME=${3:?NAME}
ROOT=/workspace/e01
LOG=$ROOT/logs
MODEL=/workspace/models/$NAME
mkdir -p $LOG /workspace/models
export DEBIAN_FRONTEND=noninteractive MAX_JOBS=16 OMP_NUM_THREADS=16 UV_CONCURRENT_DOWNLOADS=32 UV_LINK_MODE=copy
export HF_XET_HIGH_PERFORMANCE=1
log() { echo "[$(date -u +%FT%TZ)] $*"; }

log start
{ nvidia-smi; nvidia-smi -q | grep -i -E 'driver version|cuda version|product name|memory|ecc' | head -20; } > $LOG/nvidia-smi.txt 2>&1
{ echo "nproc $(nproc)"; cat /sys/fs/cgroup/cpu.max 2>/dev/null; free -g; df -h /workspace /; head -3 /etc/os-release; nvcc --version | tail -2; } > $LOG/box.txt 2>&1
command -v curl >/dev/null || { apt-get update -qq && apt-get install -y -qq curl ca-certificates >/dev/null; }
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh
log "uv $(uv --version)"

log hf-env
uv venv -q --python 3.12 /workspace/hfenv && uv pip install -q --python /workspace/hfenv/bin/python "huggingface_hub[hf_xet]"
/workspace/hfenv/bin/python - <<EOF > $LOG/model-info.json
import json
from huggingface_hub import HfApi
i = HfApi().model_info("$REPO", revision="$PIN", files_metadata=True)
print(json.dumps(dict(repo="$REPO", sha=i.sha, last_modified=str(i.last_modified),
    files=[dict(name=s.rfilename, size=s.size, lfs_sha256=(s.lfs.sha256 if s.lfs else None)) for s in i.siblings]), indent=1))
EOF
REV=$(/workspace/hfenv/bin/python -c "import json; print(json.load(open('$LOG/model-info.json'))['sha'])")
log "revision $REV"

log download-start
( /workspace/hfenv/bin/hf download $REPO --revision $REV --local-dir $MODEL > $LOG/download.log 2>&1; echo "download exit $?" >> $LOG/download.log; log download-done >> $LOG/download.log ) &
DL=$!

log vllm-install
uv venv -q --python 3.12 /workspace/venv
uv pip install --python /workspace/venv/bin/python vllm==0.30.0 > $LOG/pip-vllm.log 2>&1
echo "pip exit $?" >> $LOG/pip-vllm.log
uv pip list --python /workspace/venv/bin/python > $LOG/pip-list.txt 2>&1
/workspace/venv/bin/python -c "import torch, vllm; print('vllm', vllm.__version__, 'torch', torch.__version__, 'cuda', torch.version.cuda, 'gpu', torch.cuda.get_device_name(0))" > $LOG/versions.txt 2>&1
log "vllm-installed $(cat $LOG/versions.txt)"

wait $DL
log "download finished: $(tail -2 $LOG/download.log | tr '\n' ' ')"
du -sb $MODEL > $LOG/model-du.txt
/workspace/hfenv/bin/python - <<EOF > $LOG/model-sha256-check.txt 2>&1
import hashlib, json, os
from concurrent.futures import ThreadPoolExecutor
info = json.load(open("$LOG/model-info.json"))
def check(f):
    p = os.path.join("$MODEL", f["name"])
    if not os.path.exists(p):
        return f["name"], "MISSING"
    if os.path.getsize(p) != f["size"]:
        return f["name"], f"SIZE {os.path.getsize(p)} != {f['size']}"
    if not f["lfs_sha256"]:
        return f["name"], "ok-size (not LFS)"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while b := fh.read(1 << 24):
            h.update(b)
    return f["name"], "ok" if h.hexdigest() == f["lfs_sha256"] else f"SHA MISMATCH {h.hexdigest()}"
with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(check, info["files"]))
bad = [r for r in res if not r[1].startswith("ok")]
for r in res: print(*r)
print("ALL_OK" if not bad else f"BAD {len(bad)}")
EOF
log "sha256: $(tail -1 $LOG/model-sha256-check.txt)"
touch $ROOT/setup.done
log done
