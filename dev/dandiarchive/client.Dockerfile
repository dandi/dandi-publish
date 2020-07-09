FROM node

WORKDIR /client

RUN git clone https://github.com/dandi/dandiarchive

WORKDIR /client/dandiarchive/web

RUN yarn install --frozen-lockfile
RUN ls /client/dandiarchive/web
RUN yarn run build --mode docker

FROM nginx
RUN rm -rf /usr/share/nginx/html/*
COPY --from=0 /client/dandiarchive/web/dist /usr/share/nginx/html
