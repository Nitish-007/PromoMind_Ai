/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8080";

const nextConfig = {
    /* config options here */
    experimental: {
        agentFeedback: true,
    },
    cacheComponents: true,
    partialPrefetching: true,
    turbopack: {
        rules: {
            "*.css": {
                loaders: ["@tailwindcss/turbopack"],
                as: "*.css",
            },
        },
    },
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: `${backendUrl}/api/:path*`,
            },
            {
                source: "/problem-statement",
                destination: "/problem_statement.html",
            },
            {
                source: "/deck",
                destination: "/presentation_deck.html",
            },
        ];
    },
};

export default nextConfig;
