import Link from "next/link";

import { ServerGrid } from "@/components/servers/server-grid";
import { getServers } from "@/lib/api";

export async function TrendingServers() {
  const { data: servers } = await getServers(
    { sort: "trending", limit: 8 },
    { revalidate: 60 },
  );

  if (servers.length === 0) return null;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold tracking-tight">
          Trending servers
        </h2>
        <Link
          href="/servers?sort=trending"
          className="text-muted-foreground hover:text-foreground text-sm"
        >
          View all
        </Link>
      </div>
      <ServerGrid servers={servers} />
    </section>
  );
}
