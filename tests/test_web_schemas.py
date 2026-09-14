from datetime import datetime, timezone
import pytest
from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate, DesignJobResponse, DesignJobStatus
def test_buck_request():
    request = BuckDesignRequest(vin_min=36, vin_max=60, vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)
    assert request.model_dump()["topology"] == "buck_diode_rectified_unidirectional"; DesignJobCreate(request=request)
def test_invalid_request():
    with pytest.raises(ValueError): BuckDesignRequest(vin_min=60, vin_max=36, vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)
    with pytest.raises(ValueError): BuckDesignRequest(vin_min=36, vin_max=60, vout=12, pout=120, fs_khz=100, ripple_current_ratio=.3, ripple_voltage_ratio_percent=1, internal_path="secret")
def test_response_contract():
    response = DesignJobResponse(job_id="job-1", topology="buck_diode_rectified_unidirectional", status=DesignJobStatus.queued, progress=0, created_at=datetime.now(timezone.utc))
    assert response.schema_version == "1.0"
