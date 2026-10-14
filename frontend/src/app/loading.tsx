import { LogoLoader } from '@/components/ui/LogoLoader';

// Route-level fallback while a dashboard page loads.
export default function Loading() {
  return (
    <div className="flex-1 grid place-items-center p-12 text-[var(--text-subtle)]">
      <LogoLoader size="md" showLabel />
    </div>
  );
}
