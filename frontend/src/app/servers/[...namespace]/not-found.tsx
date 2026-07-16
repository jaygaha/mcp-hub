import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function ServerNotFound() {
  return (
    <div className="space-y-4 py-12 text-center">
      <h1 className="text-xl font-semibold">Server not found</h1>
      <p className="text-muted-foreground">
        This server couldn&apos;t be found; it may have been removed, or the link is wrong.
      </p>
      <Link href="/servers" className={buttonVariants({ variant: "outline" })}>
        Back to all servers
      </Link>
    </div>
  );
}
