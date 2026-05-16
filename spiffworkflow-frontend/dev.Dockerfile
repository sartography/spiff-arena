FROM node:24.13.0-trixie-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]
