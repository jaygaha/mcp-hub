import Link from "next/link";

import { LoginButton } from "@/components/auth/login-button";
import { ThemeToggle } from "@/components/theme-toggle";
import { getCurrentUser } from "@/lib/api";
import { LOGOUT_URL } from "@/lib/config";
import { getCookieHeader } from "@/lib/cookies";

export async function SiteHeader() {
  const user = await getCurrentUser(await getCookieHeader());

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
          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-sm">{user.username}</span>
              <a
                href={LOGOUT_URL}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Log out
              </a>
            </div>
          ) : (
            <LoginButton />
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
