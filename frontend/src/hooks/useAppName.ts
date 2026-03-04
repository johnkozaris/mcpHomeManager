import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";

const DEFAULT_APP_NAME = "MCP Manager";

export function useAppName(): string {
  const { data } = useQuery({
    queryKey: queryKeys.config(),
    queryFn: api.health.config,
    staleTime: 300_000,
  });
  return data?.app_name || DEFAULT_APP_NAME;
}
