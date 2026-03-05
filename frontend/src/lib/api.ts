import type {
  AppConfig,
  AppDefinition,
  ApplyProfileResult,
  AuthStatusResponse,
  AuditListResponse,
  CreateServiceRequest,
  CreateUserRequest,
  DiscoveredService,
  GenericToolResult,
  GenericToolDefinition,
  HealthResponse,
  ImportResult,
  OpenAPIImportResult,
  PermissionProfile,
  ServiceConnection,
  ServiceDetail,
  SmtpTestResult,
  SetupResponse,
  SmtpConfigResponse,
  TestResult,
  ToolDefinition,
  UpdateServiceRequest,
  User,
} from "./types";

const BASE = "/api";

class UnauthorizedError extends Error {
  readonly status = 401;

  constructor(message: string) {
    super(message);
    this.name = "UnauthorizedError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    // On 401, throw typed error; route loaders and UI handle the redirect.
    if (res.status === 401 && !path.startsWith("/auth/")) {
      throw new UnauthorizedError(text || "Unauthorized");
    }
    throw new Error(`${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<{ token: string; username: string; is_admin: boolean }>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ username, password }),
        },
      ),
    logout: () => request<void>("/auth/logout", { method: "DELETE" }),
    me: () =>
      request<{
        username: string;
        is_admin: boolean;
        allowed_service_ids: string[];
        has_api_key: boolean;
        can_reveal_api_key: boolean;
      }>("/auth/me"),
    createApiKey: () =>
      request<{ api_key: string }>("/auth/api-key", { method: "POST" }),
    revokeApiKey: () => request<void>("/auth/api-key", { method: "DELETE" }),
    getApiKey: () => request<{ api_key: string }>("/auth/api-key"),
    forgotPassword: (email: string) =>
      request<AuthStatusResponse>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    resetPassword: (token: string, password: string) =>
      request<AuthStatusResponse>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      }),
  },

  setup: {
    status: () => request<{ setup_required: boolean }>("/setup/status"),
    create: (data: { username: string; password: string; email?: string }) =>
      request<SetupResponse>("/setup/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  services: {
    list: () => request<ServiceConnection[]>("/services/"),
    get: (id: string) => request<ServiceDetail>(`/services/${id}`),
    create: (data: CreateServiceRequest) =>
      request<ServiceConnection>("/services/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: UpdateServiceRequest) =>
      request<ServiceConnection>(`/services/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/services/${id}`, { method: "DELETE" }),
    test: (id: string) =>
      request<TestResult>(`/services/${id}/test`, { method: "POST" }),
    getProfiles: (id: string) =>
      request<PermissionProfile[]>(`/services/${id}/profiles`),
    applyProfile: (id: string, profileName: string) =>
      request<ApplyProfileResult>(
        `/services/${id}/apply-profile`,
        {
          method: "POST",
          body: JSON.stringify({ profile_name: profileName }),
        },
      ),
    exportYaml: async () => {
      const res = await fetch(`${BASE}/services/export`, {
        credentials: "same-origin",
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      return res.text();
    },
    importYaml: (yamlContent: string, tokenMap: Record<string, string>) =>
      request<ImportResult>("/services/import", {
        method: "POST",
        body: JSON.stringify({
          yaml_content: yamlContent,
          token_map: tokenMap,
        }),
      }),
  },

  tools: {
    list: () => request<ToolDefinition[]>("/tools/"),
    updatePermission: (
      serviceId: string,
      toolName: string,
      data: {
        is_enabled: boolean;
        description_override?: string | null;
        parameters_schema_override?: Record<string, unknown> | null;
        http_method_override?: string | null;
        path_template_override?: string | null;
      },
    ) =>
      request<ToolDefinition>(`/tools/${serviceId}/${toolName}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },

  audit: {
    list: (params?: {
      limit?: number;
      offset?: number;
      service_name?: string;
      tool_name?: string;
      status?: string;
      created_after?: string;
      created_before?: string;
    }) => {
      const search = new URLSearchParams();
      if (params?.limit != null) search.set("limit", String(params.limit));
      if (params?.offset != null) search.set("offset", String(params.offset));
      if (params?.service_name) search.set("service_name", params.service_name);
      if (params?.tool_name) search.set("tool_name", params.tool_name);
      if (params?.status) search.set("status", params.status);
      if (params?.created_after)
        search.set("created_after", params.created_after);
      if (params?.created_before)
        search.set("created_before", params.created_before);
      const qs = search.toString();
      return request<AuditListResponse>(`/audit/${qs ? `?${qs}` : ""}`);
    },
  },

  health: {
    check: () => request<HealthResponse>("/health/"),
    config: () => request<AppConfig>("/health/config"),
  },

  admin: {
    getSmtp: () => request<SmtpConfigResponse>("/admin/smtp"),
    updateSmtp: (data: {
      host: string;
      port: number;
      username?: string | null;
      password?: string | null;
      from_email: string;
      use_tls: boolean;
      is_enabled: boolean;
    }) =>
      request<SmtpConfigResponse>("/admin/smtp", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    testSmtp: () =>
      request<SmtpTestResult>("/admin/smtp/test", {
        method: "POST",
      }),
    getSelfMcp: () => request<{ enabled: boolean }>("/admin/self-mcp"),
    setSelfMcp: (enabled: boolean) =>
      request<{ enabled: boolean }>("/admin/self-mcp", {
        method: "PUT",
        body: JSON.stringify({ enabled }),
      }),
  },

  discovery: {
    scan: () => request<DiscoveredService[]>("/discovery/"),
  },

  users: {
    list: () => request<User[]>("/users/"),
    create: (data: CreateUserRequest) =>
      request<User>("/users/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) => request<void>(`/users/${id}`, { method: "DELETE" }),
    update: (
      id: string,
      data: {
        is_admin?: boolean;
        self_mcp_enabled?: boolean;
        allowed_service_ids?: string[];
      },
    ) =>
      request<User>(`/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },

  genericTools: {
    create: (serviceId: string, data: GenericToolDefinition) =>
      request<GenericToolResult>(
        `/services/${serviceId}/tools`,
        { method: "POST", body: JSON.stringify(data) },
      ),
    importOpenapi: (serviceId: string, spec: string) =>
      request<OpenAPIImportResult>(`/services/${serviceId}/import-openapi`, {
        method: "POST",
        body: JSON.stringify({ spec }),
      }),
    delete: (serviceId: string, toolName: string) =>
      request<void>(
        `/services/${serviceId}/tools/${encodeURIComponent(toolName)}`,
        { method: "DELETE" },
      ),
    update: (
      serviceId: string,
      toolName: string,
      data: Record<string, unknown>,
    ) =>
      request<GenericToolResult>(
        `/services/${serviceId}/tools/${encodeURIComponent(toolName)}`,
        { method: "PATCH", body: JSON.stringify(data) },
      ),
    testTool: (serviceId: string, toolName: string) =>
      request<TestResult>(
        `/services/${serviceId}/tools/${encodeURIComponent(toolName)}/test`,
        { method: "POST" },
      ),
  },

  apps: {
    list: () => request<AppDefinition[]>("/tools/apps"),
    render: (name: string, args: Record<string, unknown> = {}) =>
      fetch(`${BASE}/tools/apps/${encodeURIComponent(name)}/render`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
      }).then(async (res) => {
        if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
        return res.text();
      }),
    action: (
      name: string,
      action: string,
      payload: Record<string, unknown> = {},
    ) =>
      fetch(`${BASE}/tools/apps/${encodeURIComponent(name)}/action`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, payload }),
      }).then(async (res) => {
        if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
        return res.text();
      }),
  },
};
