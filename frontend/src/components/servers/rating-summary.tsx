import { Star } from "lucide-react";

export function RatingSummary({ averageRating }: { averageRating: number }) {
  // A real average can never be exactly 0 (ratings are constrained 1-5 in the DB), so 0 unambiguously means "no ratings recorded yet" - render
  // that honestly instead of a misleading "0.0 stars".
  if (averageRating === 0) {
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
      <span className="font-medium">{averageRating.toFixed(1)}</span>
      <span className="text-muted-foreground">average rating</span>
    </div>
  );
}
