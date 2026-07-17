import { Separator } from "@/components/ui/separator";
import { CompatibilityMatrix } from "@/components/servers/compatibility-matrix";
import { RatingDistribution } from "@/components/servers/rating-distribution";
import { RatingSummary } from "@/components/servers/rating-summary";
import { RatingWidget } from "@/components/servers/rating-widget";
import { ReviewForm } from "@/components/servers/review-form";
import { ReviewList } from "@/components/servers/review-list";
import { ServerDetailHeader } from "@/components/servers/server-detail-header";
import { TestResultsPanel } from "@/components/servers/test-results-panel";
import {
  getCurrentUser,
  getMyReview,
  getRatingSummary,
  getReviews,
  getServerByNamespace,
} from "@/lib/api";
import { getCookieHeader } from "@/lib/cookies";

export default async function ServerDetailPage({
  params,
}: {
  params: Promise<{ namespace: string[] }>;
}) {
  // Namespaces contain slashes (e.g. "ac.inference.sh/mcp"), matching the backend's {namespace:path} route - hence the catch-all segment here
  // instead of a plain [namespace] one, and the join back into one string.
  const { namespace: segments } = await params;
  const namespace = segments.join("/");

  const cookieHeader = await getCookieHeader();
  const [{ data }, ratingSummary, currentUser, reviews, myReview] = await Promise.all([
    getServerByNamespace(namespace),
    getRatingSummary(namespace, cookieHeader),
    getCurrentUser(cookieHeader),
    getReviews(namespace),
    getMyReview(namespace, cookieHeader),
  ]);

  return (
    <div className="space-y-8">
      <ServerDetailHeader server={data.server} />

      <Separator />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Rating</h2>
        <RatingSummary
          averageScore={ratingSummary.average_score}
          totalRatings={ratingSummary.total_ratings}
        />
        <RatingDistribution
          distribution={ratingSummary.distribution}
          totalRatings={ratingSummary.total_ratings}
        />
        <RatingWidget
          namespace={namespace}
          myScore={ratingSummary.my_score}
          isLoggedIn={!!currentUser}
        />
      </section>

      <Separator />

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Compatibility</h2>
        <CompatibilityMatrix compatibilities={data.compatibilities} />
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Test results</h2>
        <TestResultsPanel testResults={data.test_results} />
      </section>

      <Separator />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Reviews</h2>
        <ReviewForm
          key={myReview?.id ?? "new"}
          namespace={namespace}
          isLoggedIn={!!currentUser}
          existingReview={myReview}
        />
        <ReviewList reviews={reviews.data} />
      </section>
    </div>
  );
}
