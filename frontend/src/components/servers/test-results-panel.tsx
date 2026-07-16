import { formatDate } from "@/lib/utils";
import type { TestResultRead } from "@/lib/types";

export function TestResultsPanel({
  testResults,
}: {
  testResults: TestResultRead[];
}) {
  if (testResults.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No automated test results yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted-foreground border-b text-left">
            <th className="py-2 pr-4 font-medium">Version</th>
            <th className="py-2 pr-4 font-medium">Speed</th>
            <th className="py-2 pr-4 font-medium">Memory</th>
            <th className="py-2 pr-4 font-medium">Success rate</th>
            <th className="py-2 pr-4 font-medium">Errors</th>
            <th className="py-2 font-medium">Tested</th>
          </tr>
        </thead>
        <tbody>
          {testResults.map((result) => (
            <tr key={result.id} className="border-b last:border-0">
              <td className="py-2 pr-4 font-mono">{result.version}</td>
              <td className="py-2 pr-4">{result.speed_ms.toFixed(0)} ms</td>
              <td className="py-2 pr-4">{result.memory_mb.toFixed(0)} MB</td>
              <td className="py-2 pr-4">
                {(result.success_rate * 100).toFixed(0)}%
              </td>
              <td className="py-2 pr-4">{result.error_count}</td>
              <td className="py-2 text-muted-foreground">
                {formatDate(result.tested_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
