from pe_claw_web.api.main import health

def test_health(): assert health() == {"status":"ok"}
