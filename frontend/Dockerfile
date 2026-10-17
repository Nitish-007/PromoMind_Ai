# ==============================================================================
# Google Cloud Run Optimized Dockerfile for PromoMind AI Frontend (Next.js)
# ==============================================================================

# Stage 1: Dependencies & Build
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments for backend URL
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application source and build production bundle
COPY . .
RUN npm run build

# Stage 2: Production Runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

# Copy runtime assets and built application
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.mjs ./next.config.mjs

EXPOSE 3000

# Start Next.js server on Cloud Run PORT
CMD ["npm", "start"]

