import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="space-y-4 py-8 text-center">
      <h1 className="text-4xl font-bold tracking-tight">MCP Hub</h1>
      <p className="text-muted-foreground mx-auto max-w-xl">
        A discovery platform for MCP (Model Context Protocol) servers. Search the official registry, browse metadata, and find the right server for your agent.
      </p>
      <Link href="/servers" className={buttonVariants({ size: "lg" })}>
        Browse servers
      </Link>
    </section>
  );
}
