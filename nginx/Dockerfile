FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY 404.html /usr/share/nginx/html/404.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
