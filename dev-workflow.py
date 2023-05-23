from flytekit import task, workflow, Resources
import time

@task(
    requests=Resources(cpu="16", mem="240Gi", gpu="6"),
    limits=Resources(cpu="16", mem="240Gi", gpu="6"),
)
def sleep():
    time.sleep(60 * 60 * 24 * 2) # 2 days

@workflow
def workflow():
    sleep()