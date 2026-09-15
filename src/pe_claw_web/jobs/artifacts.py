from __future__ import annotations
import json, os, hashlib
from pathlib import Path
from pe_claw_web.schemas import DesignResultResponse
ARTIFACT_ROOT=Path(os.getenv('PE_CLAW_ARTIFACT_ROOT','outputs/web_jobs'))
def save_result(job_id,result: DesignResultResponse):
    folder=ARTIFACT_ROOT/job_id; folder.mkdir(parents=True,exist_ok=True)
    path=folder/'result.json'; path.write_text(result.model_dump_json(indent=2),encoding='utf-8')
    return [{"id":"result-json","name":"result.json","media_type":"application/json","size":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"download_url":f"/api/v1/design-jobs/{job_id}/artifacts/result-json"}]

def save_action_manifest(job_id, action_id, payload):
    folder=ARTIFACT_ROOT/job_id/'actions'/action_id; folder.mkdir(parents=True,exist_ok=True)
    path=folder/'result.json'; path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return [{"id":"action-result-json","name":"result.json","media_type":"application/json","size":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"download_url":f"/api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts/action-result-json"}]
