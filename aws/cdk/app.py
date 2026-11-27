import aws_cdk as cdk

from stacks.config import Config
from stacks.logs import LogsStack
from stacks.servers import ServersStack

app = cdk.App()
config = Config()

logs_stack = LogsStack(
    scope=app,
    construct_id=f"{config.resource_prefix}-logs",
    config=config,
    description="Gateway logs: log group, request metrics, Insights query",
)
servers_stack = ServersStack(
    scope=app,
    construct_id=f"{config.resource_prefix}-servers",
    config=config,
    description="Gateway servers: EC2 with Docker, HTTPS by Caddy, CD role",
)
servers_stack.add_stack_dependency(logs_stack)

app.synth()
