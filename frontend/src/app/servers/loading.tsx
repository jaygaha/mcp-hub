import { ServerCardSkeleton } from "@/components/servers/server-card-skeleton";

export default function ServersLoading() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <ServerCardSkeleton key={index} />
      ))}
    </div>
  );
}
