FROM node:24.15.0-trixie-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]
