FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

ENV VITE_API_BASE_URL=https://141.83.20.81/brainns-api

COPY . .
RUN npm run build