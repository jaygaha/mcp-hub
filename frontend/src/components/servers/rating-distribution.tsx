import type { RatingDistributionBucket } from "@/lib/types";

export function RatingDistribution({
  distribution,
  totalRatings,
}: {
  distribution: RatingDistributionBucket[];
  totalRatings: number;
}) {
  if (totalRatings === 0) return null;

  return (
    <div className="max-w-xs space-y-1">
      {distribution.map(({ score, count }) => (
        <div key={score} className="flex items-center gap-2 text-xs">
          <span className="w-10 shrink-0 text-muted-foreground">{score} star</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-foreground"
              style={{ width: `${Math.round((count / totalRatings) * 100)}%` }}
            />
          </div>
          <span className="w-6 text-right text-muted-foreground">{count}</span>
        </div>
      ))}
    </div>
  );
}
