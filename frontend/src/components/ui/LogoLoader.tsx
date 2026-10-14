import React from 'react';
import wordmark from '@/assets/brand/wordmark.png';
import { BASE_PATH } from '@/lib/basePath';

// Rendered wordmark height in px; the width follows the lockup's aspect ratio.
const HEIGHTS = { sm: 32, md: 48, lg: 112 } as const;

// ! The wordmark is used as a CSS mask, i.e. a raw URL, so it needs the /admin basePath.
const LOGO_URL = wordmark.src.startsWith(BASE_PATH) ? wordmark.src : `${BASE_PATH}${wordmark.src}`;

interface LogoLoaderProps {
  label?: string;
  size?: keyof typeof HEIGHTS;
  showLabel?: boolean;
  className?: string;
}

// Brand loader: green rises through the Sukoon wordmark, rests, then drains, on a
// slow loop (see `.logo-loader` in globals.css). Replaces the old teal spinners.
export const LogoLoader: React.FC<LogoLoaderProps> = ({
  label = 'جاري التحميل...',
  size = 'md',
  showLabel = false,
  className = '',
}) => {
  const height = HEIGHTS[size];
  const width = Math.round((height * wordmark.width) / wordmark.height);

  return (
    <div role="status" className={`flex flex-col items-center gap-3 ${className}`}>
      <span
        aria-hidden
        className="logo-loader block"
        style={{ width, height, '--logo': `url(${LOGO_URL})` } as React.CSSProperties}
      />
      <span className={showLabel ? 'text-xs font-bold' : 'sr-only'}>{label}</span>
    </div>
  );
};

// Full-screen splash for the first paint. It only shows while html[data-loading]
// is set by the init script in app/layout.tsx, so without JS it never appears.
export const Splash: React.FC = () => (
  <div aria-hidden className="splash fixed inset-0 z-[100] place-items-center bg-[var(--background)]">
    <LogoLoader size="lg" />
  </div>
);
