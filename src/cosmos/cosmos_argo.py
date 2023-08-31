from hera.workflows import Workflow, WorkflowStatus, Task
from hera.workflows.models import WorkflowTemplateRef
from hera.shared import GlobalConfig
import time

from .cosmos import cosmos

GlobalConfig.namespace = cosmos.config.cloud_config.namespace
GlobalConfig.host = cosmos.config.cloud_config.host
GlobalConfig.verify_ssl = False

class Argo:

    def __init__(self):
        pass

    def submit_template_job(self, workflow_name, subfolder, tilingfolder):

        wt_ref = WorkflowTemplateRef(name=workflow_name, cluster_scope=False)

        w = Workflow(
            generate_name=workflow_name+"-",
            workflow_template_ref=wt_ref,
            arguments={"subfolder": subfolder,
                       "tilingfolder": tilingfolder}
        )

        cosmos.log("Cloud Workflow started")
        w.create()

        return w

    def submit_single_job(model):
        with Workflow(model.name.replace('_', '-'), generate_name=True, workflow_template_ref="sfincs-workflow-xzv8r") as w:
            Task("sfincs-cpu-argo", image="deltares/sfincs-cpu:latest", command=["/bin/bash", "-c", "--"], args= ["chmod +x /data/run.sh && /data/run.sh"])

        return w.create()

    def get_task_status(workflow):

        wf = workflow.workflows_service.get_workflow(workflow.name, namespace=workflow.namespace)
        status = WorkflowStatus.from_argo_status(wf.status.phase)

        cosmos.log("Status of workflow: " + status)

        return status