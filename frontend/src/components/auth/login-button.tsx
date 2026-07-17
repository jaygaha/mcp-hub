import { buttonVariants } from "@/components/ui/button";
import { GITHUB_LOGIN_URL } from "@/lib/config";
import { cn } from "@/lib/utils";

// A plain anchor, not a client component with an onClick - logging in is a
// top-level redirect to GitHub, not a fetch, so no client JS is needed here.
export function LoginButton({ className }: { className?: string }) {
  return (
    <a
      href={GITHUB_LOGIN_URL}
      className={cn(buttonVariants({ variant: "outline", size: "sm" }), className)}
    >
      Log in with GitHub
    </a>
  );
}
