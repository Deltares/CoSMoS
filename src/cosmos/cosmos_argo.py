from hera.workflows import Workflow, WorkflowStatus, Task
from hera.workflows.models import WorkflowTemplateRef
from hera.shared import GlobalConfig
import time

from .cosmos_main import cosmos

GlobalConfig.namespace = cosmos.config.cloud_config.namespace
GlobalConfig.host = cosmos.config.cloud_config.host
GlobalConfig.verify_ssl = False
GlobalConfig.token = cosmos.config.cloud_config.token

class Argo:

    def __init__(self):
        pass

    def submit_template_job(self, workflow_name, model_name, subfolder, scenario, cycle, tilingfolder, webviewerfolder):
        """Submit a template job to Argo.

        Parameters
        ----------
        workflow_name : str
            The name of the workflow template to submit.
        model_name : str
            The name of the model.
        scenario : str
            The name of the scenario.
        cycle : str
            The name of the cycle.
        subfolder : str
            The subfolder to use.
        tilingfolder : str
            The tiling folder to use. This is the folder where the tiling (index and topobathy) files are stored.
        webviewerfolder : str
            The webviewer folder to use. This is 
        """

        wt_ref = WorkflowTemplateRef(name=workflow_name, cluster_scope=False)

        mname = model_name.replace("_","-")

        w = Workflow(
            generate_name=mname+"-",
            workflow_template_ref=wt_ref,
            arguments={"subfolder": subfolder,
                       "scenario": scenario,
                       "cycle": cycle,
                       "tilingfolder": tilingfolder,
                       "webviewerfolder": webviewerfolder}
        )

        cosmos.log("Cloud Workflow started")
        w.create()

        return w

    def submit_merge_tiles_job(
            self,
            s3_bucket,
            scenario,
            cycle,
            variable
            ):
        
        wt_ref = WorkflowTemplateRef(name="merge-tiles-variable", cluster_scope=False)

        mname = variable.replace("_","-")

        w = Workflow(
            generate_name="merge-"+mname+"-",
            workflow_template_ref=wt_ref,
            arguments={
                "s3_bucket": s3_bucket,
                "scenario": scenario,
                "cycle": cycle,
                "variable": variable
                }
        )

        cosmos.log("Cloud Workflow started")
        w.create()

        return w
    
    def submit_single_job(model):
        with Workflow(model.name.replace('_', '-'), generate_name=True, workflow_template_ref="sfincs-workflow-xzv8r") as w:
            Task("sfincs-cpu-argo", image="deltares/sfincs-cpu:latest", command=["/bin/bash", "-c", "--"], args= ["chmod +x /data/run.sh && /data/run.sh"])

        return w.create()

    def get_task_status(workflow):

        status = "Unknown"

        try:
            wf = workflow.workflows_service.get_workflow(workflow.name, namespace=workflow.namespace)
            status = WorkflowStatus.from_argo_status(wf.status.phase)

            cosmos.log("Status of workflow: " + status)

        except BaseException as e:
            cosmos.log("An error occurred while checking status !")
            cosmos.log(str(e))

        return status