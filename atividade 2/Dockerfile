FROM node:14-alpine

RUN mkdir /app
WORKDIR /app

RUN npm install moleculer-cli -g

COPY .npmrc package.json package-lock.json ./

RUN npm install --production

RUN apk add htop

COPY . .

CMD ["npm", "start"]
