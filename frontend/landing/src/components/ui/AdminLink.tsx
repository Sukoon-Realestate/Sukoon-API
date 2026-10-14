'use client';

import NextLink from 'next/link';
import type { ComponentProps } from 'react';
import { adminPath } from '@/lib/basePath';

// Dashboard links are relative to /admin, including dynamic and breadcrumb links.
export default function AdminLink({ href, ...props }: ComponentProps<typeof NextLink>) {
  const target = typeof href === 'string'
    ? adminPath(href)
    : { ...href, pathname: href.pathname ? adminPath(href.pathname) : href.pathname };

  return <NextLink {...props} href={target} />;
}
