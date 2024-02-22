FROM node:20.8.1-bookworm-slim AS base

WORKDIR /app

COPY . /app/

RUN npm i

CMD ["npm", "run", "docker:start"]
