# Stage 1: Build
FROM node:22-alpine AS builder

# Entra nella cartella del progetto
WORKDIR /app

# Copia il sorgente
COPY . .

# Installa le dipendenze del progetto
RUN npm install

# Esegui il build
RUN npm run build

# Stage 2: Runtime con Nginx
FROM nginx:alpine

COPY config/nginx-reverse-proxy.conf /etc/nginx/conf.d/default.conf
# Copia i file generati dal build nella directory di Nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Espone la porta 80 (default di Nginx)
EXPOSE 80

# Comando per avviare Nginx
CMD ["nginx", "-g", "daemon off;"]