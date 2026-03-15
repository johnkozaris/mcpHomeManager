export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`bg-canvas-secondary animate-pulse rounded-xl ${className}`}
    />
  );
}
