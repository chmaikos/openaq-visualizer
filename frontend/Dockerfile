FROM node:24-alpine
WORKDIR /app
# Copy manifest and config
COPY package.json tsconfig.json index.html ./
# Install dependencies
RUN yarn install --frozen-lockfile
# Copy source code
COPY src/ ./src/
# Build the app
RUN yarn build
# Serve the built app
CMD ["yarn","preview","--host","0.0.0.0","--port","3000"]