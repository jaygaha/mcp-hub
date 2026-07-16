import { Check, Minus, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CompatibilityClient } from "@/lib/types";

type CompatibilityStatus = "compatible" | "incompatible" | "untested";

const CLIENT_LABELS: Record<CompatibilityClient, string> = {
  claude: "Claude",
  cursor: "Cursor",
  vscode: "VS Code",
};

export function CompatibilityBadge({
  client,
  status,
}: {
  client: CompatibilityClient;
  status: CompatibilityStatus;
}) {
  const label = CLIENT_LABELS[client];

  if (status === "untested") {
    return (
      <Badge variant="outline" className="gap-1 text-muted-foreground">
        <Minus className="size-3" />
        {label} - untested
      </Badge>
    );
  }

  const isCompatible = status === "compatible";

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1",
        isCompatible
          ? "border-emerald-600/30 text-emerald-700 dark:text-emerald-400"
          : "border-destructive/30 text-destructive",
      )}
    >
      {isCompatible ? <Check className="size-3" /> : <X className="size-3" />}
      {label}
    </Badge>
  );
}
