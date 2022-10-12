### STAGE 1: Build ###
FROM quay.io/sartography/node:latest
RUN mkdir /app
WORKDIR /app
ADD package.json /app/
ADD package-lock.json /app/
COPY . /app/

# npm ci because it respects the lock file.
# --ignore-scripts because authors can do bad things in postinstall scripts.
# https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html
# npx can-i-ignore-scripts can check that it's safe to ignore scripts.
RUN npm ci --ignore-scripts && npm run build

ENTRYPOINT ["/app/bin/boot_server_in_docker"]
