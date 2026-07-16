import { ServerCard } from "@/components/servers/server-card";
import type { ServerRead } from "@/lib/types";

export function ServerGrid({ servers }: { servers: ServerRead[] }) {
  // Empty-state copy lives in ResultsSummary, which every caller of this
  // grid already renders alongside it - no need to say "no results" twice.
  if (servers.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {servers.map((server) => (
        <ServerCard key={server.namespace} server={server} />
      ))}
    </div>
  );
}
