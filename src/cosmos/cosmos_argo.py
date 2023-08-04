from hera.workflows import Workflow, WorkflowStatus, Task
from hera.workflows.models import WorkflowTemplateRef
from hera.shared import GlobalConfig

from .cosmos import cosmos

GlobalConfig.namespace = cosmos.config.cloud_config.namespace
GlobalConfig.host = cosmos.config.cloud_config.host
GlobalConfig.verify_ssl = False

class Argo:

    def __init__(self):
        pass

    def submit_template_job(self, workflow_name, subfolder):

        wt_ref = WorkflowTemplateRef(name=workflow_name, cluster_scope=False)

        w = Workflow(
            generate_name=workflow_name+"-",
            workflow_template_ref=wt_ref,
            arguments={"subfolder": subfolder}
        )

        cosmos.log("Cloud Workflow started")
        w.create()
        cosmos.log("Cloud Workflow finished")

        w.wait()
        return w

    def submit_single_job(model):
        with Workflow(model.name.replace('_', '-'), generate_name=True, workflow_template_ref="sfincs-workflow-xzv8r") as w:
            Task("sfincs-cpu-argo", image="deltares/sfincs-cpu:latest", command=["/bin/bash", "-c", "--"], args= ["chmod +x /data/run.sh && /data/run.sh"])

        return w.create()

    def get_task_status(workflow):
        # Getting the status as done before doesnt work anymore. 
        # Needs to work with the workflow service instead. For now we wait
        # for completion of the workflow when creating the workflow
        return True

        # status = workflow.status
        
        # if status == 'succeeded':
        #     return True

        # return False