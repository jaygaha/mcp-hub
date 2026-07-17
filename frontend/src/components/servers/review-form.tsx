"use client";

import { useActionState } from "react";

import { submitReview, type ActionResult } from "@/app/servers/[...namespace]/actions";
import { LoginButton } from "@/components/auth/login-button";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ReviewRead } from "@/lib/types";

const initialState: ActionResult = { ok: true };

export function ReviewForm({
  namespace,
  isLoggedIn,
  existingReview,
}: {
  namespace: string;
  isLoggedIn: boolean;
  existingReview: ReviewRead | null;
}) {
  const [state, formAction, isPending] = useActionState(
    submitReview.bind(null, namespace),
    initialState,
  );

  if (!isLoggedIn) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Log in to write a review.</span>
        <LoginButton />
      </div>
    );
  }

  return (
    <form action={formAction} className="max-w-lg space-y-3">
      <div className="space-y-1.5">
        <Label htmlFor="title">Title</Label>
        <Input id="title" name="title" defaultValue={existingReview?.title} required maxLength={200} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="content">Review</Label>
        <Textarea
          id="content"
          name="content"
          defaultValue={existingReview?.content}
          required
          rows={4}
          maxLength={10_000}
        />
      </div>
      <Button type="submit" disabled={isPending}>
        {existingReview ? "Update review" : "Submit review"}
      </Button>
      {!state.ok && <p className="text-sm text-destructive">{state.error}</p>}
    </form>
  );
}
