import json
import db
import guardrails



def approve_and_run(task_id):
    """Approve a pending task and run it. A second call does nothing."""
    from agent import run_tool  # imported here to avoid a circular import

    task = db.get_task(task_id)
    if task is None:
        return {"success": False, "error": "Task not found."}

    if task["status"] != "pending":
        return {"success": False, "error": "Task is " + task["status"] + ", so nothing was done."}

    tool = task["tool_name"]
    args = json.loads(task["args_json"])

    ok, problem = guardrails.validate_call(tool, args)
    if not ok:
        db.log_event(task_id, "approval_blocked", problem)
        return {"success": False, "error": problem}

    try:
        db.approve_task(task_id)
    except ValueError as error:
        return {"success": False, "error": str(error)}

    db.set_status(task_id, "executing")

    try:
        result = run_tool(tool, args)
    except Exception as error:
        db.set_status(task_id, "failed", error_message="Tool crashed: " + str(error))
        return {"success": False, "error": "The tool crashed. Nothing was done."}

    if result["success"]:
        db.set_status(task_id, "executed", result_json=result)
        return {"success": True, "result": result}

    db.set_status(task_id, "failed", error_message=result["error"])
    return {"success": False, "error": result["error"]}


def reject_task(task_id):
    """Reject a task. Works only while it is pending."""
    task = db.get_task(task_id)
    if task is None:
        return {"success": False, "error": "Task not found."}
    if task["status"] != "pending":
        return {"success": False, "error": "Task is " + task["status"] + ", so it cannot be rejected."}
    db.set_status(task_id, "rejected")
    return {"success": True}


def edit_task(task_id, new_args):
    """Edit a pending task. The new values must pass the guardrails too."""
    task = db.get_task(task_id)
    if task is None:
        return {"success": False, "error": "Task not found."}
    ok, problem = guardrails.validate_call(task["tool_name"], new_args)
    if not ok:
        return {"success": False, "error": problem}
    try:
        db.update_task_payload(task_id, new_args)
    except ValueError as error:
        return {"success": False, "error": str(error)}
    return {"success": True}