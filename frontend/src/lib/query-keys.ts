export const queryKeys = {
  services: () => ["services"] as const,
  service: (id: string) => ["services", id] as const,
  tools: () => ["tools"] as const,
  audit: (args: {
    limit: number;
    offset: number;
    serviceName?: string;
    toolName?: string;
    status?: string;
  }) =>
    [
      "audit",
      args.limit,
      args.offset,
      args.serviceName,
      args.toolName,
      args.status,
    ] as const,
  health: () => ["health"] as const,
  profiles: (serviceId: string) => ["profiles", serviceId] as const,
  users: () => ["users"] as const,
  apps: () => ["apps"] as const,
  config: () => ["config"] as const,
  authMe: () => ["auth", "me"] as const,
  adminSmtp: () => ["admin", "smtp"] as const,
};

