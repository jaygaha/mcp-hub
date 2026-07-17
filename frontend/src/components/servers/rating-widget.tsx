"use client";

import { Star } from "lucide-react";
import { useState, useTransition } from "react";

import { submitRating } from "@/app/servers/[...namespace]/actions";
import { LoginButton } from "@/components/auth/login-button";
import { cn } from "@/lib/utils";

export function RatingWidget({
  namespace,
  myScore,
  isLoggedIn,
}: {
  namespace: string;
  myScore: number | null;
  isLoggedIn: boolean;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  if (!isLoggedIn) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Log in to rate this server.</span>
        <LoginButton />
      </div>
    );
  }

  const displayScore = hovered ?? myScore ?? 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1" role="radiogroup" aria-label="Your rating">
        {[1, 2, 3, 4, 5].map((score) => (
          <button
            key={score}
            type="button"
            disabled={isPending}
            role="radio"
            aria-checked={myScore === score}
            aria-label={`Rate ${score} star${score > 1 ? "s" : ""}`}
            onMouseEnter={() => setHovered(score)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => {
              setError(null);
              startTransition(async () => {
                const result = await submitRating(namespace, score);
                if (!result.ok) setError(result.error);
              });
            }}
            className="disabled:opacity-50"
          >
            <Star
              className={cn(
                "size-5 transition-colors",
                displayScore >= score
                  ? "fill-current text-foreground"
                  : "text-muted-foreground",
              )}
            />
          </button>
        ))}
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
