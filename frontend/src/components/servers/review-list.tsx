import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { formatDate } from "@/lib/utils";
import type { ReviewRead } from "@/lib/types";

export function ReviewList({ reviews }: { reviews: ReviewRead[] }) {
  if (reviews.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No reviews yet. Be the first to write one.
      </p>
    );
  }

  return (
    <ul className="space-y-6">
      {reviews.map((review) => (
        <li key={review.id} className="space-y-1.5 border-b pb-6 last:border-0">
          <div className="flex items-center gap-2">
            <Avatar size="sm">
              <AvatarImage src={review.author_avatar_url ?? undefined} alt={review.author_username} />
              <AvatarFallback>{review.author_username.slice(0, 2).toUpperCase()}</AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium">{review.author_username}</span>
            <span className="text-xs text-muted-foreground">
              {formatDate(review.created_at)}
              {review.updated_at !== review.created_at && " (edited)"}
            </span>
          </div>
          <h3 className="font-semibold">{review.title}</h3>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{review.content}</p>
        </li>
      ))}
    </ul>
  );
}
