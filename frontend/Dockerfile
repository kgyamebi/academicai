FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN mkdir -p public && npm run build

FROM node:20-alpine
WORKDIR /app
RUN addgroup -g 10001 app && adduser -D -G app -u 10001 app
COPY --from=build --chown=app:app /app/package.json /app/package-lock.json ./
COPY --from=build --chown=app:app /app/node_modules ./node_modules
COPY --from=build --chown=app:app /app/.next ./.next
COPY --from=build --chown=app:app /app/next.config.ts ./
COPY --from=build --chown=app:app /app/public ./public
USER 10001
EXPOSE 3000
CMD ["npm", "run", "start"]
