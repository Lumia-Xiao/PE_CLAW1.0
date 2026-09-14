param([int]$RetentionHours=168)
python -c "from pe_claw_web.jobs.cleanup import cleanup_artifacts; print(cleanup_artifacts(retention_hours=$RetentionHours))"
