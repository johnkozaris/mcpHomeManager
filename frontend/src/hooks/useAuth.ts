import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, hasSessionToken, onAuthStateChanged } from "@/lib/api";

interface AuthUser {
  username: string;
  is_admin: boolean;
  allowed_service_ids: string[];
  has_api_key: boolean;
}

/**
 * Fetch the current user from /api/auth/me.
 * Only enabled when a session token exists.
 */
export function useCurrentUser() {
  const [enabled, setEnabled] = useState(() => hasSessionToken());

  useEffect(() => {
    return onAuthStateChanged(() => setEnabled(hasSessionToken()));
  }, []);

  return useQuery<AuthUser>({
    queryKey: ["auth", "me"],
    queryFn: () => api.auth.me(),
    staleTime: 60_000,
    retry: false,
    enabled,
  });
}
