"""
Register a CoSMoS fat-image AWS Batch job definition.

One definition per model+arch (it pins the image); CoSMoS overrides the command
(step token), queue, and GPU requirement at submit time, so a single definition
serves all three steps (run_all / prepare_and_simulate / merge_and_tile).

The definition declares NO GPU by default so the CPU-only merge+tile step can
schedule on a CPU queue; CoSMoS adds the GPU requirement only for the
simulation steps.

By default the name matches the CoSMoS template `cosmos-{model}-fat`. If you
register both CPU and GPU variants, give the second one a distinct name with
--name and point `config.batch.job_definition` at it for CPU runs.

Needs iam:PassRole (passes BatchSimJobRole) -> run under an ADMIN profile:
    aws sso login --profile sfincs-admin
    python register_jobdef.py --model sfincs --arch gpu
"""

import argparse

import boto3

REGION   = "eu-west-1"
PROFILE  = "sfincs-admin"
ACCOUNT  = "012053003218"
JOB_ROLE = f"arn:aws:iam::{ACCOUNT}:role/BatchSimJobRole"
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com"

# CPU/MEMORY defaults (overridable per job). No GPU here on purpose.
DEFAULT_VCPU = "4"
DEFAULT_MEMORY = "14000"  # MiB


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a fat-image job definition.")
    parser.add_argument("--model", required=True, choices=["sfincs", "hurrywave"])
    parser.add_argument("--arch", required=True, choices=["cpu", "gpu"])
    parser.add_argument("--name", default=None, help="Job definition name (default: cosmos-<model>-fat)")
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--region", default=REGION)
    args = parser.parse_args()

    jobdef = args.name or f"cosmos-{args.model}-fat"
    image = f"{REGISTRY}/{args.model}:{args.arch}-fat-batch"

    batch = boto3.Session(profile_name=args.profile, region_name=args.region).client("batch")
    resp = batch.register_job_definition(
        jobDefinitionName=jobdef,
        type="container",
        platformCapabilities=["EC2"],
        containerProperties={
            "image": image,
            "jobRoleArn": JOB_ROLE,
            "resourceRequirements": [
                {"type": "VCPU", "value": DEFAULT_VCPU},
                {"type": "MEMORY", "value": DEFAULT_MEMORY},
            ],
            # Default command; CoSMoS overrides it with the step token at submit.
            "command": ["run_all"],
        },
    )
    print(f"Registered {resp['jobDefinitionName']}:{resp['revision']}  ({image})")


if __name__ == "__main__":
    main()
