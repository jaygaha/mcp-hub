import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";

export function SiteHeader() {
  return (
    <header className="border-b">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="font-semibold tracking-tight">
          MCP Hub
        </Link>
        <nav className="flex items-center gap-4">
          <Link
            href="/servers"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Browse servers
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
