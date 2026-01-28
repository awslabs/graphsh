"""Stack manager for integration test infrastructure."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

INFRA_DIR = Path(__file__).parent / "infra"
STACK_PREFIX = "graphsh-integ-"


class StackManager:
    """Manages CloudFormation stacks for integration tests."""

    def __init__(self, region: str = None):
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.cfn = boto3.client("cloudformation", region_name=self.region)
        self.ec2 = boto3.client("ec2", region_name=self.region)

    def _get_default_vpc_and_subnets(self):
        """Get default VPC and public subnets in AZs that support t3."""
        vpcs = self.ec2.describe_vpcs(
            Filters=[{"Name": "is-default", "Values": ["true"]}]
        )
        if not vpcs["Vpcs"]:
            raise RuntimeError("No default VPC found")
        vpc_id = vpcs["Vpcs"][0]["VpcId"]

        # Get subnets, preferring AZs that typically support t3 instances
        subnets = self.ec2.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        # Sort by AZ name to prefer a, b, c, d over e, f (e often has limited instance types)
        sorted_subnets = sorted(subnets["Subnets"], key=lambda s: s["AvailabilityZone"])
        # Filter out us-east-1e which often lacks instance type support
        filtered = [
            s for s in sorted_subnets if not s["AvailabilityZone"].endswith("e")
        ]
        if not filtered:
            filtered = sorted_subnets
        subnet_ids = [s["SubnetId"] for s in filtered[:2]]
        return vpc_id, subnet_ids

    def deploy(self, db_type: str) -> dict:
        """Deploy stack for given database type. Returns connection info."""
        stack_name = f"{STACK_PREFIX}{db_type}"
        template_path = INFRA_DIR / f"{db_type}.yaml"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        vpc_id, subnet_ids = self._get_default_vpc_and_subnets()

        params = []
        if db_type == "neo4j":
            params = [
                {"ParameterKey": "VpcId", "ParameterValue": vpc_id},
                {"ParameterKey": "SubnetId", "ParameterValue": subnet_ids[0]},
            ]
        elif db_type == "neptune":
            params = [
                {"ParameterKey": "VpcId", "ParameterValue": vpc_id},
                {"ParameterKey": "SubnetIds", "ParameterValue": ",".join(subnet_ids)},
            ]
        # neptune-analytics needs no VPC params

        try:
            self.cfn.create_stack(
                StackName=stack_name,
                TemplateBody=template_path.read_text(),
                Parameters=params,
                Capabilities=["CAPABILITY_IAM"],
                OnFailure="DELETE",
            )
        except ClientError as e:
            if "AlreadyExistsException" in str(e):
                pass  # Stack exists, wait for it
            else:
                raise

        return self._wait_and_get_outputs(stack_name)

    def _wait_and_get_outputs(self, stack_name: str, timeout: int = 1800) -> dict:
        """Wait for stack completion and return outputs."""
        waiter = self.cfn.get_waiter("stack_create_complete")
        try:
            waiter.wait(
                StackName=stack_name, WaiterConfig={"MaxAttempts": timeout // 30}
            )
        except Exception:
            # Check if already complete
            pass

        resp = self.cfn.describe_stacks(StackName=stack_name)
        stack = resp["Stacks"][0]
        if stack["StackStatus"] not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
            raise RuntimeError(f"Stack {stack_name} in state {stack['StackStatus']}")

        return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}

    def teardown(self, db_type: str):
        """Delete stack for given database type."""
        stack_name = f"{STACK_PREFIX}{db_type}"
        try:
            self.cfn.delete_stack(StackName=stack_name)
            waiter = self.cfn.get_waiter("stack_delete_complete")
            waiter.wait(StackName=stack_name, WaiterConfig={"MaxAttempts": 60})
        except ClientError as e:
            if "does not exist" not in str(e):
                raise

    def get_outputs(self, db_type: str) -> Optional[dict]:
        """Get outputs from existing stack, or None if not exists."""
        stack_name = f"{STACK_PREFIX}{db_type}"
        try:
            resp = self.cfn.describe_stacks(StackName=stack_name)
            stack = resp["Stacks"][0]
            if stack["StackStatus"] in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
                return {
                    o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])
                }
        except ClientError:
            pass
        return None
