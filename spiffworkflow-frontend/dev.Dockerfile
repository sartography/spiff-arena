FROM node:20.8.1-bookworm-slim AS base

WORKDIR /app

CMD ["npm", "run", "start"]
