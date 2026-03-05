import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";

interface AuthUser {
  username: string;
  is_admin: boolean;
  allowed_service_ids: string[];
  has_api_key: boolean;
  can_reveal_api_key: boolean;
}

export function useCurrentUser() {
  return useQuery<AuthUser>({
    queryKey: queryKeys.authMe(),
    queryFn: () => api.auth.me(),
    staleTime: 60_000,
    retry: false,
  });
}
