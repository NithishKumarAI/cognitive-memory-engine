FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG ALLOW_LOCAL_API_ORIGIN=0
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL ALLOW_LOCAL_API_ORIGIN=$ALLOW_LOCAL_API_ORIGIN NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build --chown=node:node /app/.next ./.next
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/next.config.ts ./next.config.ts
COPY --from=build --chown=node:node /app/lib/api-origin.mjs ./lib/api-origin.mjs
COPY --from=build --chown=node:node /app/scripts/start.mjs ./scripts/start.mjs
USER node
EXPOSE 3000
CMD ["npm", "start"]
