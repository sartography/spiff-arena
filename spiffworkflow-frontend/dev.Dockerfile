FROM node:22.3.0-bookworm-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]
