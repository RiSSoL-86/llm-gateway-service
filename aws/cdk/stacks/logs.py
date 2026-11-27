from typing import Final

import aws_cdk as cdk
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from stacks.config import Config

PROXIED_REQUEST: Final = logs.FilterPattern.string_value(
    json_field="$.event", comparison="=", value="proxy"
)
# OpenRouter path of the request: `chat/completions`, `models`...
ENDPOINT: Final = {"Endpoint": "$.endpoint"}

# Metric name, JSON field of the gateway metrics line, unit
REQUEST_METRICS: Final = (
    ("TimeToFirstToken", "$.ttft_ms", cloudwatch.Unit.MILLISECONDS),
    ("TotalTime", "$.total_ms", cloudwatch.Unit.MILLISECONDS),
    ("Overhead", "$.overhead_ms", cloudwatch.Unit.MILLISECONDS),
    ("PromptTokens", "$.prompt_tokens", cloudwatch.Unit.COUNT),
    ("CompletionTokens", "$.completion_tokens", cloudwatch.Unit.COUNT),
    ("Cost", "$.cost", cloudwatch.Unit.NONE),
)

SUMMARY_QUERY: Final = """\
filter event = "proxy"
| stats count() as requests,
    avg(ttft_ms) as avg_ttft_ms, pct(ttft_ms, 95) as p95_ttft_ms,
    avg(total_ms) as avg_total_ms,
    avg(overhead_ms) as avg_overhead_ms, max(overhead_ms) as max_overhead_ms,
    sum(prompt_tokens) as prompt_tokens,
    sum(completion_tokens) as completion_tokens,
    sum(cost) as cost
  by endpoint, model, stream, status
| sort requests desc"""


class LogsStack(cdk.Stack):
    """Log group of the gateway servers, a stream per server."""

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

        log_group = logs.LogGroup(
            scope=self,
            id="LlmGatewayService-servers-logs",
            log_group_name=config.log_group_name,
            retention=config.log_retention,
        )

        # ERROR lines per server, its stream name in the service field
        logs.MetricFilter(
            scope=self,
            id="LlmGatewayService-error-logs",
            log_group=log_group,
            filter_pattern=logs.FilterPattern.string_value(
                json_field="$.level", comparison="=", value="ERROR"
            ),
            metric_namespace=config.metrics_namespace,
            metric_name="ErrorLogs",
            metric_value="1",
            dimensions={"Service": "$.service"},
            unit=cloudwatch.Unit.COUNT,
        )

        # One metrics line per proxied request, metrics per endpoint
        logs.MetricFilter(
            scope=self,
            id="LlmGatewayService-requests",
            log_group=log_group,
            filter_pattern=PROXIED_REQUEST,
            metric_namespace=config.metrics_namespace,
            metric_name="Requests",
            metric_value="1",
            dimensions=ENDPOINT,
            unit=cloudwatch.Unit.COUNT,
        )
        logs.MetricFilter(
            scope=self,
            id="LlmGatewayService-failed-requests",
            log_group=log_group,
            filter_pattern=logs.FilterPattern.all(
                PROXIED_REQUEST,
                logs.FilterPattern.number_value(
                    json_field="$.status", comparison=">=", value=400
                ),
            ),
            metric_namespace=config.metrics_namespace,
            metric_name="FailedRequests",
            metric_value="1",
            dimensions=ENDPOINT,
            unit=cloudwatch.Unit.COUNT,
        )
        for metric_name, field, unit in REQUEST_METRICS:
            logs.MetricFilter(
                scope=self,
                id=f"LlmGatewayService-{metric_name}",
                log_group=log_group,
                # Only lines that have the number: no nulls in the metric
                filter_pattern=logs.FilterPattern.all(
                    PROXIED_REQUEST,
                    logs.FilterPattern.number_value(
                        json_field=field, comparison=">=", value=0
                    ),
                ),
                metric_namespace=config.metrics_namespace,
                metric_name=metric_name,
                metric_value=field,
                dimensions=ENDPOINT,
                unit=unit,
            )

        # Logs Insights: speed, overhead, tokens and cost per model
        logs.CfnQueryDefinition(
            scope=self,
            id="LlmGatewayService-summary-query",
            name=f"{config.resource_prefix}/requests-summary",
            query_string=SUMMARY_QUERY,
            log_group_names=[log_group.log_group_name],
        )

        # Docker awslogs driver on a server: its own stream, write only
        iam.ManagedPolicy(
            scope=self,
            id="LlmGatewayService-servers-logs-write",
            managed_policy_name=config.logs_write_policy_name,
            description="Docker on the gateway servers writes logs",
            statements=[
                iam.PolicyStatement(
                    actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[log_group.log_group_arn],
                ),
            ],
        )
