import { Separator } from "@/components/ui/separator";
import { CompatibilityMatrix } from "@/components/servers/compatibility-matrix";
import { RatingSummary } from "@/components/servers/rating-summary";
import { ServerDetailHeader } from "@/components/servers/server-detail-header";
import { TestResultsPanel } from "@/components/servers/test-results-panel";
import { getServerByNamespace } from "@/lib/api";

export default async function ServerDetailPage({
  params,
}: {
  params: Promise<{ namespace: string[] }>;
}) {
  // Namespaces contain slashes (e.g. "ac.inference.sh/mcp"), matching the backend's {namespace:path} route - hence the catch-all segment here
  // instead of a plain [namespace] one, and the join back into one string.
  const { namespace: segments } = await params;
  const namespace = segments.join("/");

  const { data } = await getServerByNamespace(namespace);

  return (
    <div className="space-y-8">
      <ServerDetailHeader server={data.server} />

      <Separator />

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Rating</h2>
        <RatingSummary averageRating={data.average_rating} />
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Compatibility</h2>
        <CompatibilityMatrix compatibilities={data.compatibilities} />
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Test results</h2>
        <TestResultsPanel testResults={data.test_results} />
      </section>
    </div>
  );
}
