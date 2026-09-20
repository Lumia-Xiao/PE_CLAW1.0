from __future__ import annotations
import json, os, hashlib
from pathlib import Path
from pe_claw_web.schemas import DesignResultResponse
from .exports import EXPORTS, write_exports
ARTIFACT_ROOT=Path(os.getenv('PE_CLAW_ARTIFACT_ROOT','outputs/web_jobs'))
def _manifest_entry(*, artifact_id, name, media_type, path, url, stage):
    data=path.read_bytes()
    return {"id":artifact_id,"name":name,"media_type":media_type,"size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"schema_version":"1.0","stage":stage,"download_url":url}
def save_result(job_id,result: DesignResultResponse):
    folder=ARTIFACT_ROOT/job_id; folder.mkdir(parents=True,exist_ok=True)
    exported = []
    for artifact_id in write_exports(result.summary, folder / 'exports'):
        name, media_type, stage = EXPORTS[artifact_id]
        exported.append(_manifest_entry(artifact_id=artifact_id,name=name,media_type=media_type,
            path=folder/'exports'/name,stage=stage,url=f"/api/v1/design-jobs/{job_id}/artifacts/{artifact_id}"))
    # The report lists all other artifacts. Its own hash lives in the API manifest
    # to avoid a self-referential checksum. Never rewrite it after hashing.
    payload=result.model_copy(update={'job_id':job_id,'artifacts':exported})
    path=folder/'result.json'; path.write_text(payload.model_dump_json(indent=2),encoding='utf-8')
    return [_manifest_entry(artifact_id="result-json",name="result.json",media_type="application/json",path=path,stage="report",url=f"/api/v1/design-jobs/{job_id}/artifacts/result-json"), *exported]


def resolve_artifact(root, job_id, artifact_id, manifest):
    """Resolve a fixed export ID under its job; never trust a client/file path."""
    entry=next((item for item in manifest if item.get('id') == artifact_id), None)
    if entry is None:
        raise FileNotFoundError(artifact_id)
    folder=(root/job_id).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise FileNotFoundError(artifact_id)
    if artifact_id == 'result-json':
        path=folder/'result.json'
    elif artifact_id in EXPORTS:
        path=folder/'exports'/EXPORTS[artifact_id][0]
    else:
        raise FileNotFoundError(artifact_id)
    if not path.resolve().is_relative_to(folder) or not path.is_file():
        raise FileNotFoundError(artifact_id)
    content=path.read_bytes()
    if len(content) != entry['size'] or (entry.get('sha256') and hashlib.sha256(content).hexdigest() != entry['sha256']):
        raise FileNotFoundError(artifact_id)
    return path, entry

def save_action_manifest(job_id, action_id, payload):
    folder=ARTIFACT_ROOT/job_id/'actions'/action_id; folder.mkdir(parents=True,exist_ok=True)
    path=folder/'result.json'; path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return [_manifest_entry(artifact_id="action-result-json",name="result.json",media_type="application/json",path=path,stage="report",url=f"/api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts/action-result-json")]
