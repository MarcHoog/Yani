FROM node:24-alpine AS build
RUN npm install -g pnpm@11
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY ui/package.json ui/
COPY portal/package.json portal/
RUN pnpm install --frozen-lockfile
COPY ui ui
COPY portal portal
RUN pnpm --filter @yani/portal build

FROM nginx:1.29-alpine
COPY portal/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/portal/dist /usr/share/nginx/html
EXPOSE 80
