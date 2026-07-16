import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { ServerRead } from "@/lib/types";

export function ServerDetailHeader({ server }: { server: ServerRead }) {
  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{server.name}</h1>
        <p className="text-muted-foreground font-mono text-sm">
          {server.namespace}
        </p>
      </div>

      {server.description && (
        <p className="text-muted-foreground max-w-2xl">{server.description}</p>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {server.version && <Badge variant="secondary">v{server.version}</Badge>}
        {server.author && <Badge variant="outline">{server.author}</Badge>}
        {server.docker_image && (
          <Badge variant="outline" className="font-mono">
            {server.docker_image}
          </Badge>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-4 text-sm">
        {server.repository_url && (
          <a
            href={server.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-foreground underline-offset-4 hover:underline"
          >
            Repository
            <ExternalLink className="size-3.5" />
          </a>
        )}
        <span className="text-muted-foreground">
          Added {formatDate(server.created_at)}
        </span>
        <span className="text-muted-foreground">
          Updated {formatDate(server.updated_at)}
        </span>
      </div>
    </div>
  );
}
