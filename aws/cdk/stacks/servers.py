import textwrap
from typing import Final

import aws_cdk as cdk
from aws_cdk import aws_dlm as dlm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from stacks.config import Config


class ServersStack(cdk.Stack):
    """EC2 per gateway server: Docker, HTTPS by Caddy, own IP."""

    # First boot: Docker with compose and buildx, git, 2 GB swap for builds.
    SETUP_COMMANDS: Final = textwrap.dedent("""\
        dnf install -y docker git
        systemctl enable --now docker

        plugins=/usr/local/lib/docker/cli-plugins
        mkdir -p "$plugins"
        curl -fsSL -o "$plugins/docker-compose" \\
            https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-linux-aarch64
        curl -fsSL -o "$plugins/docker-buildx" \\
            https://github.com/docker/buildx/releases/download/v0.23.0/buildx-v0.23.0.linux-arm64
        chmod +x "$plugins/docker-compose" "$plugins/docker-buildx"

        dd if=/dev/zero of=/swapfile bs=1M count=2048
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile swap swap defaults 0 0' >> /etc/fstab""")

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        description: str,
    ) -> None:
        super().__init__(
            scope=scope,
            id=construct_id,
            description=description,
        )

        # Own VPC, public subnets: out via Internet Gateway, no NAT to pay for
        vpc = ec2.Vpc(
            scope=self,
            id="LlmGatewayService-vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        # Docker awslogs driver writes to the servers log group
        logs_write_policy = iam.ManagedPolicy.from_managed_policy_name(
            scope=self,
            id="LlmGatewayService-servers-logs-write",
            managed_policy_name=config.logs_write_policy_name,
        )

        # CD: GitHub Actions runs the update over SSM
        github = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            scope=self,
            id="LlmGatewayService-github-oidc-provider",
            open_id_connect_provider_arn=(
                f"arn:aws:iam::{self.account}"
                ":oidc-provider/token.actions.githubusercontent.com"
            ),
        )
        deploy_role = iam.Role(
            scope=self,
            id="LlmGatewayService-servers-deploy-role",
            role_name=f"{config.resource_prefix}-servers-deploy",
            description="CD of llm-gateway-service over SSM Run Command",
            assumed_by=iam.WebIdentityPrincipal(
                identity_provider=github.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": (
                            "sts.amazonaws.com"
                        ),
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": (
                            config.deploy_subjects
                        ),
                    },
                },
            ),
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParametersByPath"],
                resources=[
                    self.format_arn(
                        service="ssm",
                        resource="parameter",
                        resource_name=config.servers_prefix.lstrip("/"),
                    )
                ],
            )
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:SendCommand"],
                resources=[
                    self.format_arn(
                        service="ssm",
                        resource="document",
                        resource_name="AWS-RunShellScript",
                        account="",
                    )
                ],
            )
        )
        deploy_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetCommandInvocation"],
                resources=["*"],
            )
        )

        ssm.StringParameter(
            scope=self,
            id="LlmGatewayService-servers-deploy-role-arn",
            parameter_name=f"/{config.resource_prefix}/deploy-role-arn",
            string_value=deploy_role.role_arn,
        )

        # Daily snapshots of every server tagged for backup, 7 kept
        backup_tag = cdk.CfnTag(
            key="Backup", value=f"{config.resource_prefix}-servers"
        )
        backup_role = iam.Role(
            scope=self,
            id="LlmGatewayService-servers-backup-role",
            assumed_by=iam.ServicePrincipal(service="dlm.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name=(
                        "service-role/AWSDataLifecycleManagerServiceRole"
                    )
                )
            ],
        )
        dlm.CfnLifecyclePolicy(
            scope=self,
            id="LlmGatewayService-servers-backup",
            description="Daily snapshots of the gateway servers",
            state="ENABLED",
            execution_role_arn=backup_role.role_arn,
            policy_details=dlm.CfnLifecyclePolicy.PolicyDetailsProperty(
                policy_type="EBS_SNAPSHOT_MANAGEMENT",
                resource_types=["INSTANCE"],
                target_tags=[backup_tag],
                schedules=[
                    dlm.CfnLifecyclePolicy.ScheduleProperty(
                        name="daily",
                        copy_tags=True,
                        create_rule=dlm.CfnLifecyclePolicy.CreateRuleProperty(
                            interval=24,
                            interval_unit="HOURS",
                            times=["00:00"],
                        ),
                        retain_rule=dlm.CfnLifecyclePolicy.RetainRuleProperty(
                            count=7
                        ),
                    )
                ],
            ),
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(self.SETUP_COMMANDS)

        for number in config.servers:
            server = f"gateway-{number}"

            # Security Group: Caddy on 80 (certificate) and 443 (API)
            security_group = ec2.SecurityGroup(
                scope=self,
                id=f"LlmGatewayService-{server}-security-group",
                vpc=vpc,
                description=f"Gateway {server}: HTTPS by Caddy",
                allow_all_outbound=True,
            )
            security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(port=80),
                description="Lets Encrypt HTTP challenge, redirect to HTTPS",
            )
            security_group.add_ingress_rule(
                peer=ec2.Peer.any_ipv4(),
                connection=ec2.Port.tcp(port=443),
                description="OpenRouter-compatible API under the gateway key",
            )

            # Server
            server_instance = ec2.Instance(
                scope=self,
                # Short id: the launch template name it makes is 128 chars max.
                id=f"LlmGatewayService-{server}",
                instance_name=f"{config.resource_prefix}-{number}",
                instance_type=ec2.InstanceType.of(
                    instance_class=ec2.InstanceClass.BURSTABLE4_GRAVITON,
                    instance_size=config.server_size,
                ),
                machine_image=ec2.MachineImage.generic_linux(
                    ami_map={config.server_region: config.server_image}
                ),
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                security_group=security_group,
                ssm_session_permissions=True,
                require_imdsv2=True,
                block_devices=[
                    ec2.BlockDevice(
                        device_name="/dev/xvda",
                        volume=ec2.BlockDeviceVolume.ebs(
                            volume_size=20,
                            volume_type=ec2.EbsDeviceVolumeType.GP3,
                            encrypted=True,
                            delete_on_termination=False,
                        ),
                    )
                ],
                user_data=user_data,
            )
            cdk.Tags.of(server_instance).add(
                key=backup_tag.key, value=backup_tag.value
            )
            server_instance.role.add_managed_policy(logs_write_policy)
            deploy_role.add_to_policy(
                iam.PolicyStatement(
                    actions=["ssm:SendCommand"],
                    resources=[
                        self.format_arn(
                            service="ec2",
                            resource="instance",
                            resource_name=server_instance.instance_id,
                        )
                    ],
                )
            )

            # Elastic IP: the address and its sslip.io host stay on restarts
            elastic_ip = ec2.CfnEIP(
                scope=self,
                id=f"LlmGatewayService-{server}-ip",
                domain="vpc",
                instance_id=server_instance.instance_id,
            )

            ssm.StringParameter(
                scope=self,
                id=f"LlmGatewayService-{server}-instance-id",
                parameter_name=f"{config.servers_prefix}/{number}/instance-id",
                string_value=server_instance.instance_id,
            )
            ssm.StringParameter(
                scope=self,
                id=f"LlmGatewayService-{server}-host",
                parameter_name=f"{config.servers_prefix}/{number}/host",
                string_value=cdk.Fn.join(
                    delimiter="",
                    list_of_values=[
                        cdk.Fn.join(
                            delimiter="-",
                            list_of_values=cdk.Fn.split(
                                delimiter=".",
                                source=elastic_ip.attr_public_ip,
                            ),
                        ),
                        ".sslip.io",
                    ],
                ),
            )
