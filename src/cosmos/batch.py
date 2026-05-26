"""AWS Batch job submission for CoSMoS (``run_mode = "batch"``).

Replaces the Argo Workflows path (`argo.py`) with direct AWS Batch submission.
CoSMoS remains the top-level scheduler — it resolves the inter-model nesting
DAG and decides which model is ready — and Batch runs each model job.

Two job shapes, both driven by a single job definition with the command
overridden at submit time (so adding a model/arch doesn't need a new job def):

* **Deterministic model** → one job that runs prepare → simulate → tile inside
  the (fat) model image.
* **Ensemble model** → a 2-job chain that lets AWS Batch do the fan-out/fan-in
  natively, without a babysitter container:

      sim   = array job, size N   (GPU queue)   each element runs member i
      merge = single job          (CPU queue)   dependsOn=sim; merges + tiles

  CoSMoS submits both and polls only ``merge``: because ``merge`` depends on the
  whole array, a SUCCEEDED merge means the chain finished, and a failed array
  element fails ``merge`` too — so one job id captures the outcome.

The container's S3 staging and the mapping of these command tokens to the
``run_job_2.py`` steps live in the model image (the aws_batch repo), not here.
This module only submits and polls.
"""

import re
from typing import Dict, List, Optional

import boto3

from .cosmos import cosmos

# AWS Batch job names must match ^[A-Za-z0-9][A-Za-z0-9_-]{1,127}$ (no dots).
_INVALID_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")

# Terminal job states.
_FINISHED = ("SUCCEEDED", "FAILED")


def _job_name(name: str) -> str:
    """Sanitise a model name into a valid Batch job name."""
    cleaned = _INVALID_NAME_CHARS.sub("-", name)
    # Must start with an alphanumeric character.
    if cleaned and not cleaned[0].isalnum():
        cleaned = "j" + cleaned
    return cleaned[:128]


class Batch:
    """Thin client for submitting and polling AWS Batch jobs."""

    def __init__(self) -> None:
        """Create a Batch client.

        Uses the explicit access/secret keys from ``cloud_config`` when present
        (CoSMoS running on a local machine); otherwise falls back to the default
        boto3 credential chain (CoSMoS running on an EC2 instance with a role —
        the stage-2 setup).
        """
        cc = cosmos.config.cloud_config
        bc = cosmos.config.batch
        region = bc.region or cc.region

        session_kwargs = {"region_name": region}
        if cc.access_key and cc.secret_key:
            session_kwargs["aws_access_key_id"] = cc.access_key
            session_kwargs["aws_secret_access_key"] = cc.secret_key

        self.client = boto3.Session(**session_kwargs).client("batch")

    def submit_job(
        self,
        job_name: str,
        queue: str,
        command: List[str],
        environment: Optional[Dict[str, str]] = None,
        depends_on: Optional[List[str]] = None,
        array_size: Optional[int] = None,
        job_definition: Optional[str] = None,
        vcpus: Optional[int] = None,
        memory: Optional[int] = None,
        gpus: Optional[int] = None,
    ) -> str:
        """Submit a single (optionally array) Batch job.

        Parameters
        ----------
        job_name : str
            Human-readable job name (sanitised to Batch's allowed charset).
        queue : str
            Target job queue (hardware selection).
        command : list of str
            Container command override — the step token(s) the model image maps
            to a ``run_job_2.py`` invocation.
        environment : dict, optional
            Environment variables passed to the container (S3 keys, scenario,
            cycle, webviewer/tiling folders, …).
        depends_on : list of str, optional
            Job ids this job must wait for (used for the merge step).
        array_size : int, optional
            If > 1, submit as an array job of this size. Each element receives
            ``AWS_BATCH_JOB_ARRAY_INDEX`` (0…N-1) to select its ensemble member.
        job_definition : str, optional
            Job definition to use; falls back to the ``[batch]`` config value.
            (The image is pinned in the definition, so it varies per model type.)
        vcpus, memory, gpus : int, optional
            Container resource overrides. Fall back to the ``[batch]`` config
            defaults, and then to the job definition's own values.

        Returns
        -------
        str
            The submitted job id.
        """
        bc = cosmos.config.batch

        container: Dict = {"command": command}
        if environment:
            container["environment"] = [
                {"name": k, "value": str(v)} for k, v in environment.items()
            ]

        resource_reqs = []
        n_vcpus = vcpus if vcpus is not None else bc.vcpus
        n_memory = memory if memory is not None else bc.memory
        n_gpus = gpus if gpus is not None else bc.gpus
        if n_vcpus is not None:
            resource_reqs.append({"type": "VCPU", "value": str(n_vcpus)})
        if n_memory is not None:
            resource_reqs.append({"type": "MEMORY", "value": str(n_memory)})
        if n_gpus is not None:
            resource_reqs.append({"type": "GPU", "value": str(n_gpus)})
        if resource_reqs:
            container["resourceRequirements"] = resource_reqs

        kwargs: Dict = {
            "jobName": _job_name(job_name),
            "jobQueue": queue,
            "jobDefinition": job_definition or bc.job_definition,
            "containerOverrides": container,
        }
        if array_size and array_size > 1:
            kwargs["arrayProperties"] = {"size": array_size}
        if depends_on:
            kwargs["dependsOn"] = [{"jobId": j} for j in depends_on]

        response = self.client.submit_job(**kwargs)
        job_id = response["jobId"]
        cosmos.log(f"Submitted Batch job {kwargs['jobName']} → {job_id} (queue {queue})")
        return job_id

    def get_job_status(self, job_id: str) -> str:
        """Return the current status of a Batch job.

        One of: SUBMITTED, PENDING, RUNNABLE, STARTING, RUNNING, SUCCEEDED,
        FAILED, or UNKNOWN if the job can't be described.
        """
        try:
            jobs = self.client.describe_jobs(jobs=[job_id])["jobs"]
            if not jobs:
                return "UNKNOWN"
            return jobs[0]["status"]
        except Exception as e:
            cosmos.log(f"Error checking Batch job {job_id}: {e}")
            return "UNKNOWN"

    @staticmethod
    def is_finished(status: str) -> bool:
        """True once the job has reached a terminal state."""
        return status in _FINISHED

    @staticmethod
    def is_failed(status: str) -> bool:
        """True if the job ended in failure."""
        return status == "FAILED"
