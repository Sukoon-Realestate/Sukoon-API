'use client';

import React from 'react';

interface SkeletonLoaderProps {
  variant?: 'card' | 'table-row' | 'metric' | 'text';
  count?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'card',
  count = 1,
}) => {
  const items = Array.from({ length: count });

  if (variant === 'metric') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((_, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-[var(--card-bg)] border border-[var(--card-border)] space-y-3 animate-pulse"
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-[var(--card-hover)]"></div>
              <div className="w-12 h-5 rounded-full bg-[var(--card-hover)]"></div>
            </div>
            <div className="w-24 h-7 rounded-lg bg-[var(--card-hover)]"></div>
            <div className="w-32 h-4 rounded bg-[var(--card-hover)]"></div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'table-row') {
    return (
      <div className="divide-y divide-[var(--divider)]">
        {items.map((_, idx) => (
          <div key={idx} className="p-4 flex items-center justify-between animate-pulse gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[var(--card-hover)] shrink-0"></div>
              <div className="space-y-1.5">
                <div className="w-36 h-4 rounded bg-[var(--card-hover)]"></div>
                <div className="w-24 h-3 rounded bg-[var(--card-hover)]"></div>
              </div>
            </div>
            <div className="w-20 h-6 rounded-full bg-[var(--card-hover)]"></div>
            <div className="w-16 h-8 rounded-lg bg-[var(--card-hover)]"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((_, idx) => (
        <div
          key={idx}
          className="p-6 rounded-2xl bg-[var(--card-bg)] border border-[var(--card-border)] space-y-4 animate-pulse"
        >
          <div className="w-full h-36 rounded-xl bg-[var(--card-hover)]"></div>
          <div className="w-3/4 h-5 rounded bg-[var(--card-hover)]"></div>
          <div className="w-1/2 h-4 rounded bg-[var(--card-hover)]"></div>
        </div>
      ))}
    </div>
  );
};
