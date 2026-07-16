import { CompatibilityBadge } from "@/components/servers/compatibility-badge";
import type { CompatibilityClient, CompatibilityRead } from "@/lib/types";

// Always show all three known clients, even when nothing has been tested
// yet - absence of data is "untested", not "incompatible".
const KNOWN_CLIENTS: CompatibilityClient[] = ["claude", "cursor", "vscode"];

export function CompatibilityMatrix({
  compatibilities,
}: {
  compatibilities: CompatibilityRead[];
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {KNOWN_CLIENTS.map((client) => {
        const result = compatibilities.find((c) => c.client === client);
        const status =
          result === undefined
            ? "untested"
            : result.compatible
              ? "compatible"
              : "incompatible";

        return (
          <CompatibilityBadge key={client} client={client} status={status} />
        );
      })}
    </div>
  );
}
