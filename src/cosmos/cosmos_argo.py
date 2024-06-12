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

    def submit_template_job(self, workflow_name, job_name, subfolder, scenario, cycle, webviewerfolder=None, tilingfolder=None):
        """Submit a template job to Argo.

        Parameters
        ----------
        workflow_name : str
            The name of the Argo workflow template to submit.
        job_name : str
            The name of the model/varaible for which you are submitting the job.
        subfolder : str
            The subfolder on S3 that needs to be copied to the compute instance as input
        scenario : str
            The name of the scenario.
        cycle : str
            The name of the cycle.
        webviewerfolder : str, optional
            The name of the webviewer folder to use. This is the folder where the webviewer files are stored.
        tilingfolder : str, optinal
            The tiling folder to use. This is the folder where the tiling (index and topobathy) files are stored.
        """

        # Get the workflow template reference
        wt_ref = WorkflowTemplateRef(name=workflow_name, cluster_scope=False)

        # Replace underscores with dashes in the job name
        mname = job_name.replace("_","-")

        # Gather the arguments
        arguments={"subfolder": subfolder, "scenario": scenario, "cycle": cycle}
        if webviewerfolder is not None:
            arguments["webviewerfolder"] = webviewerfolder
        if tilingfolder is not None:
            arguments["tilingfolder"] = tilingfolder

        # Create the workflow
        w = Workflow(
            generate_name=mname+"-",
            workflow_template_ref=wt_ref,
            arguments=arguments
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