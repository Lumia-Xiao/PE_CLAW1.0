# Web API v1 contract

The initial Web boundary is version `1.0`. Its public Pydantic models are
`DesignRequest`, `BuckDesignRequest`, `DesignJobCreate`, `DesignJobResponse`,
`DesignResultResponse`, `DesignError`, and `ArtifactManifestEntry`.

The starter routes are:

```text
GET  /api/v1/health
GET  /api/v1/topologies
POST /api/v1/design/buck
```

[`web-api-v1-buck-request.json`](web-api-v1-buck-request.json) is a complete
request body for `POST /api/v1/design/buck` and is loaded directly by the
schema tests. Numeric field descriptions and generated JSON Schema include
their engineering units. The Buck relationship is explicit: `vin_max >=
vin_min` and `vout < vin_min`.

Requests are closed models. Unknown keys are rejected, the topology is a
supported-value enum, selection options are finite enums, and only the five
documented Buck options are accepted. Paths, module names, expressions,
callables, and internal Python objects therefore have no request field through
which they can enter the pipeline.

Pydantic/FastAPI validation errors retain their field location. Public job
failures use a versioned `DesignError` with a stable identifier `code`, bounded
public `message`, and optional opaque `correlation_id`. Artifact manifest
entries expose a safe filename and API download URL rather than a filesystem
path.
