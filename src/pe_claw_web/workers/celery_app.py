from celery import Celery
import os
celery_app=Celery("pe_claw", broker=os.getenv("PE_CLAW_REDIS_URL","redis://localhost:6379/0"), backend=os.getenv("PE_CLAW_REDIS_URL","redis://localhost:6379/0"))
celery_app.conf.update(task_track_started=True, task_serializer="json", accept_content=["json"], result_serializer="json")
