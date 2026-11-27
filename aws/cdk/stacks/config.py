from dataclasses import dataclass

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_logs as logs


@dataclass(frozen=True)
class Config:
    """Resource names and SSM prefixes shared by every stack."""

    resource_prefix: str = "llm-gateway-service"
    metrics_namespace: str = "LlmGatewayService"
    log_retention: logs.RetentionDays = logs.RetentionDays.ONE_MONTH
    github_owner: str = "RiSSoL-86"
    github_owner_id: int = 110422516
    github_repository: str = "llm-gateway-service"
    server_region: str = "us-east-1"
    # Amazon Linux 2023 arm64: pinned, a new image must not replace servers
    server_image: str = "ami-09609e4587bf4f83e"
    servers: tuple[int, ...] = (1,)
    # Graviton t4g, bigger for the load; resizing keeps the disk and address
    server_size: ec2.InstanceSize = ec2.InstanceSize.MICRO

    @property
    def deploy_subjects(self) -> list[str]:
        """GitHub OIDC `sub` of production deploys from this repo only."""
        suffix = "environment:production"
        return [
            f"repo:{self.github_owner}/{self.github_repository}:{suffix}",
            # Subject with immutable ids, if the account enables it
            f"repo:{self.github_owner}@{self.github_owner_id}/"
            f"{self.github_repository}@*:{suffix}",
        ]

    @property
    def servers_prefix(self) -> str:
        return f"/{self.resource_prefix}/servers"

    @property
    def log_group_name(self) -> str:
        return f"/{self.resource_prefix}/servers"

    @property
    def logs_write_policy_name(self) -> str:
        return f"{self.resource_prefix}-servers-logs-write"
