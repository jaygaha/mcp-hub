import { Star } from "lucide-react";

export function RatingSummary({
  averageScore,
  totalRatings,
}: {
  averageScore: number;
  totalRatings: number;
}) {
  if (totalRatings === 0) {
    return (
      <div className="text-muted-foreground flex items-center gap-2 text-sm">
        <Star className="size-4" />
        No ratings yet
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <Star className="size-4 fill-current" />
      <span className="font-medium">{averageScore.toFixed(1)}</span>
      <span className="text-muted-foreground">
        average rating ({totalRatings} {totalRatings === 1 ? "rating" : "ratings"})
      </span>
    </div>
  );
}
