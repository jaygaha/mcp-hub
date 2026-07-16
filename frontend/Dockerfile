FROM node:26-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Set default fallback value - next dev/start read PORT directly, no CLI flag needed
ENV PORT=3000
EXPOSE ${PORT}

CMD ["npm", "run", "dev"]
