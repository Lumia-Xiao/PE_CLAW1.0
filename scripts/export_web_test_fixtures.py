"""Regenerate browser fixtures from the real Buck topology and report builder."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import (
    BUCK_TOPOLOGY_ID, build_default_inputs,
)
from pe_claw_web.api.catalog import topology_catalog


def main():
    target = Path(__file__).resolve().parents[1] / 'web/frontend/tests/fixtures'
    target.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as output:
        report = run_topology_pipeline(
            build_default_registry().get_plugin(BUCK_TOPOLOGY_ID),
            build_default_inputs(), output_root=output,
        ).report
        result = {
            'schema_version': '1.0', 'job_id': '11111111-1111-4111-8111-111111111111',
            'topology': BUCK_TOPOLOGY_ID, 'summary': build_structured_report(report),
            'warnings': report.notes, 'artifacts': [],
        }
    for name, data in [('catalog.json', topology_catalog()), ('result.json', result)]:
        (target / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
