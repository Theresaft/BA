FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

ENV VITE_API_BASE_URL=https://challenger.imi.uni-luebeck.de/brainns/

COPY . .
RUN npm run build