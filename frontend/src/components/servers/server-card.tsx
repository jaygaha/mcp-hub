import { Package } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ServerRead } from "@/lib/types";

export function ServerCard({ server }: { server: ServerRead }) {
  return (
    <Link href={`/servers/${server.namespace}`} className="block h-full">
      <Card className="h-full transition-colors hover:border-foreground/30">
        <CardHeader>
          <CardTitle className="line-clamp-1">{server.name}</CardTitle>
          <CardDescription className="line-clamp-1 font-mono text-xs">
            {server.namespace}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-muted-foreground line-clamp-2 min-h-10 text-sm">
            {server.description || "No description provided."}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {server.version && (
              <Badge variant="secondary">v{server.version}</Badge>
            )}
            {server.author && (
              <Badge variant="outline" className="line-clamp-1">
                {server.author}
              </Badge>
            )}
            {server.docker_image && (
              <Badge variant="outline" className="gap-1">
                <Package className="size-3" />
                Docker
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
