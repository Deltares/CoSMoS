from hera import Task, Workflow, WorkflowService, WorkflowStatus
from hera.global_config import GlobalConfig
import os

GlobalConfig.host = os.getenv("HOST")
GlobalConfig.verify_ssl = False
GlobalConfig.token = os.getenv("TOKEN")
GlobalConfig.namespace = "argo"

class Argo:

    def __init__(self, name):
        pass

    def submit_single_job(model):
        with Workflow(model.name.replace('_', '-'), generate_name=True, workflow_template_ref="sfincs-workflow-xzv8r") as w:
            Task("sfincs-cpu-argo", image="deltares/sfincs-cpu:latest", command=["/bin/bash", "-c", "--"], args= ["chmod +x /data/run.sh && /data/run.sh"])

        return w.create()

    def get_task_status(workflow):
        status = workflow.get_status()
        
        if status == WorkflowStatus.Succeeded:
            return True

        return False
