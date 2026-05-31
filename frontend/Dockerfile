FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM alpine:latest
COPY --from=builder /app/dist /app/dist
VOLUME /app/dist
CMD ["sh", "-c", "cp -r /app/dist/* /shared/ 2>/dev/null; echo done"]
