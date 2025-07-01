# Node Builder
FROM node:24 AS node_builder
WORKDIR /app
RUN mkdir -p /app/acerestreamer/static
COPY package.json package-lock.json ./
RUN npm install

# APP
FROM ghcr.io/astral-sh/uv:python3.13-alpine

## Required for psutil
RUN apk add gcc python3-dev musl-dev linux-headers

COPY --from=node_builder /app/acerestreamer/static/* /app/acerestreamer/static/

## Install the project into `/app`
WORKDIR /app

## Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

## Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

## Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-default-groups

## Then, add the rest of the project source code and install it
## Installing separately from its dependencies allows optimal layer caching
ADD acerestreamer acerestreamer

# We don't need this anymore
RUN rm -rf /usr/local/bin/uv*

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

EXPOSE 5100

CMD [ "waitress-serve", "--listen", "0.0.0.0:5100", "--trusted-proxy", "*", "--trusted-proxy-headers", "x-forwarded-for x-forwarded-proto x-forwarded-port", "--log-untrusted-proxy-headers", "--clear-untrusted-proxy-headers", "--threads", "4", "--call", "acerestreamer:create_app" ]
