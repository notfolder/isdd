# ビルドステージ
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# 本番ステージ - Nginx
FROM nginx:alpine

# Nginxのデフォルト設定を削除
RUN rm /etc/nginx/conf.d/default.conf

# カスタムNginx設定をコピー
COPY nginx.conf /etc/nginx/conf.d/

# ビルドされた静的ファイルをコピー
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
