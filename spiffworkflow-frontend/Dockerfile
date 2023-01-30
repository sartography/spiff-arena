# Base image to share ENV vars that activate VENV.
FROM quay.io/sartography/node:latest AS base

RUN mkdir /app
WORKDIR /app

# this matches total memory on spiffworkflow-demo
ENV NODE_OPTIONS=--max_old_space_size=2048

# Setup image for installing JS dependencies.
FROM base AS setup

COPY . /app/

# npm ci because it respects the lock file.
# --ignore-scripts because authors can do bad things in postinstall scripts.
# https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html
# npx can-i-ignore-scripts can check that it's safe to ignore scripts.
RUN npm ci --ignore-scripts

RUN npm run build

# Final image without setup dependencies.
FROM base AS final

LABEL source="https://github.com/sartography/spiff-arena"
LABEL description="Software development platform for building, running, and monitoring executable diagrams"

# WARNING: On localhost frontend assumes backend is one port lowe.
ENV PORT0=7001

COPY --from=setup /app/build /app/build

ENTRYPOINT ["/app/bin/boot_server_in_docker"]
