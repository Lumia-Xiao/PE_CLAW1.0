"""Versioned JSON snapshots of trusted report dataclasses; no pickle or dynamic type imports."""
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import lru_cache
import hashlib
import importlib
import json
import math
from pathlib import Path
import pkgutil

from pe_claw_gui.models.design_report import DesignReport

class CheckpointIncompatible(ValueError):
    pass

@lru_cache
def registry():
    import pe_claw_gui.models as models
    modules = [m.name for m in pkgutil.iter_modules(models.__path__, models.__name__ + '.')]
    modules += ['pe_claw_gui.topologies.base.candidate', 'pe_claw_gui.topologies.base.result', 'pe_claw_gui.topologies.base.spec']
    types = {}
    for name in modules:
        module = importlib.import_module(name)
        for value in vars(module).values():
            if isinstance(value, type) and (is_dataclass(value) or issubclass(value, Enum)):
                types[value.__module__ + ':' + value.__qualname__] = value
    return types

@lru_cache
def pipeline_version():
    import pe_claw_gui
    digest = hashlib.sha256(b'complete-buck-recovery-v1')
    root = Path(pe_claw_gui.__file__).parent
    # A checkpoint cannot silently resume under changed engineering code.
    for path in sorted(root.rglob('*.py')):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()

def encode(value):
    if isinstance(value, Enum):
        name = type(value).__module__ + ':' + type(value).__qualname__
        if name not in registry():
            raise CheckpointIncompatible(f'Unregistered enum: {name}')
        return {'kind': 'enum', 'type': name, 'value': value.value}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {'kind': 'float', 'value': str(value)}
    if is_dataclass(value):
        name = type(value).__module__ + ':' + type(value).__qualname__
        if name not in registry():
            raise CheckpointIncompatible(f'Unregistered dataclass: {name}')
        return {'kind': 'dataclass', 'type': name, 'fields': {f.name: encode(getattr(value, f.name)) for f in fields(value) if f.init}}
    if isinstance(value, Path):
        return {'kind': 'path', 'value': str(value)}
    if isinstance(value, dict):
        return {'kind': 'mapping', 'items': [[encode(k), encode(v)] for k, v in value.items()]}
    if isinstance(value, (tuple, list, set, frozenset)):
        return {'kind': type(value).__name__, 'items': [encode(v) for v in value]}
    raise CheckpointIncompatible(f'Unsupported checkpoint value: {type(value).__name__}')

def decode(value):
    if not isinstance(value, dict):
        return value
    kind = value.get('kind')
    if kind in {'dataclass', 'enum'}:
        cls = registry().get(value.get('type'))
        if cls is None:
            raise CheckpointIncompatible('Unknown checkpoint type')
        if kind == 'enum':
            return cls(value['value'])
        return cls(**{k: decode(v) for k, v in value['fields'].items()})
    if kind == 'mapping':
        return {decode(k): decode(v) for k, v in value['items']}
    if kind in {'list', 'tuple', 'set', 'frozenset'}:
        return {'list': list, 'tuple': tuple, 'set': set, 'frozenset': frozenset}[kind](decode(v) for v in value['items'])
    if kind == 'path':
        return Path(value['value'])
    if kind == 'float' and value['value'] in {'nan', 'inf', '-inf'}:
        return float(value['value'])
    raise CheckpointIncompatible('Unknown checkpoint node')

def checksum(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def snapshot(report, stage, request_key):
    body = {'schema_version': '1.0', 'pipeline_version': pipeline_version(),
            'request_key': request_key, 'completed_stage': stage, 'report': encode(report)}
    return {**body, 'sha256': checksum(body)}

def restore(payload, request_key):
    body = {k: v for k, v in payload.items() if k != 'sha256'}
    if body.get('schema_version') != '1.0' or body.get('pipeline_version') != pipeline_version() or body.get('request_key') != request_key or checksum(body) != payload.get('sha256'):
        raise CheckpointIncompatible('Checkpoint version, input or checksum mismatch; start a new design')
    try:
        report = decode(body['report'])
    except (TypeError, KeyError, ValueError) as exc:
        raise CheckpointIncompatible('Checkpoint cannot be decoded') from exc
    if not isinstance(report, DesignReport):
        raise CheckpointIncompatible('Checkpoint is not a design report')
    return report, body['completed_stage']
