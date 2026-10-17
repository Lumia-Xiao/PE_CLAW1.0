"""Shared stage order and initial durable state for complete design jobs."""

PIPELINE_STAGES = (
    "topology",
    "devices",
    "capacitor",
    "magnetics",
    "operating_point",
    "loss",
    "thermal",
    "efficiency_sweep",
    "report",
)
COMPLETE_STAGES = ("validate", *PIPELINE_STAGES, "finalize")
STAGE_PROGRESS = {
    "topology": 8,
    "devices": 18,
    "capacitor": 28,
    "magnetics": 40,
    "operating_point": 52,
    "loss": 64,
    "thermal": 74,
    "efficiency_sweep": 86,
    "report": 94,
}


def new_stage_details():
    """Return an independent JSON-ready pending record for every stage."""

    return {
        stage: {
            "schema_version": "1.0",
            "status": "pending",
            "progress": 0,
            "warnings": [],
            "error": None,
            "started_at": None,
            "finished_at": None,
        }
        for stage in COMPLETE_STAGES
    }
