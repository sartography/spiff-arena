FROM node:24.18.0-trixie-slim@sha256:366fdef91728b1b7fa18c84fba63b6e79ed77b7e10cc206878e9705da4d7b169 AS base

WORKDIR /app

CMD ["npm", "run", "start"]
