from celery import Celery
import os
celery_app=Celery("pe_claw", broker=os.getenv("PE_CLAW_REDIS_URL","redis://localhost:6379/0"), backend=os.getenv("PE_CLAW_REDIS_URL","redis://localhost:6379/0"))
celery_app.conf.update(task_track_started=True, task_serializer="json", accept_content=["json"], result_serializer="json")
celery_app.conf.update(
    include=["pe_claw_web.workers.tasks"],
    broker_connection_timeout=3,
    task_publish_retry=False,
    broker_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1, "retry_on_timeout": False},
    redis_socket_connect_timeout=1,
    redis_socket_timeout=1,
    result_backend_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1, "retry_on_timeout": False},
)
if os.getenv("PE_CLAW_CELERY_EAGER", "0") == "1":
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
