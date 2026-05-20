FROM nginx:alpine

RUN chmod -R 755 /usr/share/nginx/html

COPY --chown=nginx:nginx . /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
 CMD wget --spider --no-verbose --tries=1 http://localhost:80/healthz | exit 1


ENTRYPOINT ["nginx", "-g","daemon off;"]