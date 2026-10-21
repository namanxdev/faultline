# Base image for exported Harbor tasks: the tools sidecar and the separate verifier.
# Never used for the agent's container. Build from the repository root:
#   uv build --wheel && docker build -t faultline-harbor:0.1.0 -f harbor/Dockerfile .
FROM python:3.12-slim
COPY dist/faultline-0.1.0-py3-none-any.whl /tmp/
# The tools server, oracle, and grader import mcp but never LiteLLM.
RUN pip install --no-cache-dir --no-deps /tmp/faultline-0.1.0-py3-none-any.whl \
 && pip install --no-cache-dir "mcp==2.3.0" \
 && rm /tmp/faultline-0.1.0-py3-none-any.whl
