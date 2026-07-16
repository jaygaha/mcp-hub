import { Hero } from "@/components/home/hero";
import { TrendingServers } from "@/components/home/trending-servers";

export default function Home() {
  return (
    <div className="space-y-12">
      <Hero />
      <TrendingServers />
    </div>
  );
}
