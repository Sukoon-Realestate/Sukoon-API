This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### 1. Environment Variables Configuration

Copy `.env.example` to `.env.local` to configure whether to connect to a live backend or use local static dummy data:

```bash
cp .env.example .env.local
```

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_ENABLE_BACKEND` | `false` | Set to `true` to connect to the live Django backend API, or `false` to use static dummy JSON data files in `src/data/mock/`. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | The live Django backend API URL (active when `NEXT_PUBLIC_ENABLE_BACKEND=true`). |

> **Note:** If backend is not deployed yet or you are running locally without Django running, keep `NEXT_PUBLIC_ENABLE_BACKEND=false`. All pages, authentication, search, metrics, and actions will run offline using the static dummy JSON files.

### 2. Run the Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
