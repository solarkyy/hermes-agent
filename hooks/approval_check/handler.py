import requests

async def handle(event_type, context):
    build_id = context.get("build_id") or context.get("task_id")
    if not build_id:
        return

    response = requests.get(f"http://localhost:3000/approvals?buildId={build_id}")
    if not response.json().get("approved", False):
        raise RuntimeError(f"Task {build_id} blocked: Approval pending.")

