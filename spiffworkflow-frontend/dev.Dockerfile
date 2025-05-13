FROM node:20.8.1-bookworm-slim AS base

WORKDIR /app

COPY --from=python . /python

CMD ["npm", "run", "start"]
