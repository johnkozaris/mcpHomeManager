export type BuiltinServiceType =
  | "generic_rest"
  | "forgejo"
  | "homeassistant"
  | "paperless"
  | "immich"
  | "nextcloud"
  | "uptimekuma"
  | "adguard"
  | "nginxproxymanager"
  | "portainer"
  | "freshrss"
  | "wallabag"
  | "stirlingpdf"
  | "wikijs"
  | "calibreweb"
  | "tailscale"
  | "cloudflare";
export type ServiceType = BuiltinServiceType | (string & {});

export const BUILTIN_SERVICE_TYPES: BuiltinServiceType[] = [
  "generic_rest",
  "forgejo",
  "homeassistant",
  "paperless",
  "immich",
  "nextcloud",
  "uptimekuma",
  "adguard",
  "nginxproxymanager",
  "portainer",
  "freshrss",
  "wallabag",
  "stirlingpdf",
  "wikijs",
  "calibreweb",
  "tailscale",
  "cloudflare",
];
export type HealthStatus = "healthy" | "unhealthy" | "unknown";

export interface ServiceConnection {
  id: string;
  name: string;
  display_name: string;
  service_type: ServiceType;
  base_url: string;
  is_enabled: boolean;
  health_status: HealthStatus;
  last_health_check: string | null;
  tool_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ServiceDetail extends ServiceConnection {
  config: Record<string, unknown>;
  tools: ToolDefinition[];
}

export interface ToolDefinition {
  name: string;
  service_type: ServiceType;
  service_id: string | null;
  service_name: string | null;
  description: string;
  parameters_schema: Record<string, unknown>;
  is_enabled: boolean;
  description_override: string | null;
  parameters_schema_override: Record<string, unknown> | null;
  http_method: string | null;
  path_template: string | null;
  http_method_override: string | null;
  path_template_override: string | null;
  is_user_defined?: boolean;
}

export interface AuditEntry {
  id: string;
  service_name: string;
  tool_name: string;
  input_summary: string;
  status: "success" | "error";
  duration_ms: number;
  error_message: string | null;
  client_name: string | null;
  created_at: string | null;
}

export interface AuditListResponse {
  items: AuditEntry[];
  total: number;
}

export interface CreateServiceRequest {
  name: string;
  display_name: string;
  service_type: ServiceType;
  base_url: string;
  api_token: string;
  config?: Record<string, unknown>;
}

export interface UpdateServiceRequest {
  display_name?: string;
  base_url?: string;
  api_token?: string;
  is_enabled?: boolean;
  config?: Record<string, unknown>;
}

export interface BackendMessageCodeFields {
  code?: string | null;
  message_code?: string | null;
}

export interface TestResult extends BackendMessageCodeFields {
  success: boolean;
  message: string;
}

export interface HealthResponse {
  status: string;
  database: string;
  mcp_server: string;
  services_healthy: number;
  services_total: number;
}

export interface DiscoveredService {
  service_type: ServiceType;
  display_name: string;
  container_name: string;
  image: string;
  suggested_url: string;
  ports: string[];
}

export interface PermissionProfile {
  name: string;
  label: string;
  description: string;
  tool_states: Record<string, boolean>;
}

export interface ApplyProfileResult extends BackendMessageCodeFields {
  status: string;
  profile: string;
}

export interface ImportResult {
  created: string[];
  skipped: string[];
  errors: string[];
}

export interface User {
  id: string;
  username: string;
  email: string | null;
  is_admin: boolean;
  self_mcp_enabled: boolean;
  allowed_service_ids: string[];
  created_at: string | null;
}

export interface CreateUserRequest {
  username: string;
  password?: string;
  email?: string;
  is_admin?: boolean;
  self_mcp_enabled?: boolean;
  allowed_service_ids?: string[];
}

export interface AppConfig {
  setup_required: boolean;
  smtp_enabled: boolean;
  mcp_server_name: string;
  self_mcp_enabled: boolean;
  app_name: string;
}

export interface SmtpConfigResponse {
  host: string;
  port: number;
  username: string | null;
  has_password: boolean;
  from_email: string;
  use_tls: boolean;
  is_enabled: boolean;
}

export interface SmtpTestResult extends BackendMessageCodeFields {
  success: boolean;
  message: string;
}

export interface AuthStatusResponse extends BackendMessageCodeFields {
  status: string;
}

export interface SetupResponse {
  token: string;
  username: string;
  is_admin: boolean;
  api_key: string;
}

export interface GenericToolDefinition {
  tool_name: string;
  description: string;
  http_method: string;
  path_template: string;
  params_schema: Record<string, unknown>;
}

export interface GenericToolResult extends BackendMessageCodeFields {
  status: string;
  tool_name: string;
  tools_count: number;
}

export interface OpenAPIImportResult extends BackendMessageCodeFields {
  status: string;
  imported: string[];
  skipped: string[];
  warnings: string[];
  tools_count: number;
}

export interface AppDefinition {
  name: string;
  service_type: string;
  service_name: string;
  title: string;
  description: string;
  parameters_schema: Record<string, unknown>;
}
