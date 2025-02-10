# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app

# Installa le dipendenze di sviluppo
RUN apk update && apk add --no-cache curl gcompat build-base git
RUN npm install -g create-react-app tailwindcss

# Installa Create React App e crea il progetto
RUN npx create-react-app tuya-ui

# Entra nella cartella del progetto
WORKDIR /app/tuya-ui

# Installa le dipendenze necessarie
RUN npm install axios web-vitals react-spinners
RUN npm install -D @tailwindcss/postcss postcss postcss-loader autoprefixer

# Installa le dipendenze del progetto
RUN npm install

# Copia il resto del codice
COPY . .

# Esegui il build
RUN npm run build

# Stage 2: Runtime con Nginx
FROM nginx:alpine

# Copia i file generati dal build nella directory di Nginx
COPY --from=builder /app/tuya-ui/build /usr/share/nginx/html

# Espone la porta 80 (default di Nginx)
EXPOSE 80

# Comando per avviare Nginx
CMD ["nginx", "-g", "daemon off;"]