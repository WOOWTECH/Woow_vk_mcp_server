FROM node:22-slim AS node-base
RUN npm install -g supergateway

FROM python:3.12-slim

# Copy Node.js runtime
COPY --from=node-base /usr/local/bin/node /usr/local/bin/node
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules

# Create proper bin links for npm global packages
RUN ln -s /usr/local/lib/node_modules/supergateway/dist/index.js /usr/local/bin/supergateway-js || true
RUN echo '#!/bin/sh\nexec /usr/local/bin/node /usr/local/lib/node_modules/supergateway/dist/index.js "$@"' > /usr/local/bin/supergateway && chmod +x /usr/local/bin/supergateway

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl bash && \
    rm -rf /var/lib/apt/lists/*

# Copy vibe-kanban-mcp binary
COPY vibe-kanban-mcp /usr/local/bin/vibe-kanban-mcp
RUN chmod +x /usr/local/bin/vibe-kanban-mcp

# Install Python deps
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic python-multipart sse-starlette pyjwt kubernetes pyyaml aiofiles

# Copy source
COPY mcp_admin_core/ ./mcp_admin_core/
COPY vk_mcp_admin/ ./vk_mcp_admin/
COPY frontend/ ./frontend/

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app
EXPOSE 8080 8000

CMD ["/app/entrypoint.sh"]
