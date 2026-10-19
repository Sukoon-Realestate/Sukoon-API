This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### 1. Environment Variables Configuration

Use `.env.example` for a real backend connection. Browser API requests default to the frontend origin. Set the server-only `SOKOUN_API_PROXY_URL` to the Django origin (for example `http://127.0.0.1:8000` locally); Next forwards `/api/v1/*` and preserves methods, request bodies, response headers and status. Do not include credentials or a path in this value. Keep `NEXT_PUBLIC_API_URL` empty for this mode. Deploy both the frontend process and the backend; the Django `/admin/` is a separate interface.

An explicit `NEXT_PUBLIC_API_URL` retains direct cross-origin access only when that backend explicitly allows the frontend origin, credentials and required pagination headers. Do not disable browser security or enable wildcard credentialed CORS to make it work.

Live backend mode is the default. Demo fixtures require explicit `NEXT_PUBLIC_ENABLE_BACKEND=false`; their results do not verify real operations.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
