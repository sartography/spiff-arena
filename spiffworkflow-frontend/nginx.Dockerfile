# Use nginx as the base image
FROM nginx:latest

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/*

# Copy the nginx configuration file
COPY prod/nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files into the nginx directory
COPY dist /usr/share/nginx/html

