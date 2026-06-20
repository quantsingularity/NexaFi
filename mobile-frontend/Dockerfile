# Multi-stage build: compile the Vite app, then serve the static output.
FROM node:22-slim AS build
WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
# The API base URL is baked in at build time. Through the compose reverse proxy
# the gateway is reachable at /api/v1.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN pnpm build

FROM nginx:1.27-alpine AS serve
COPY --from=build /app/dist /usr/share/nginx/html
# SPA fallback so client-side routes resolve to index.html.
RUN printf 'server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  location / { try_files $uri $uri/ /index.html; }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
