import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type {
  CreateServiceRequest,
  CreateUserRequest,
  GenericToolDefinition,
  ServiceConnection,
  UpdateServiceRequest,
} from "@/lib/types";

export function useServices() {
  return useQuery({
    queryKey: queryKeys.services(),
    queryFn: api.services.list,
  });
}

export function useService(id: string) {
  const qc = useQueryClient();
  return useQuery({
    queryKey: queryKeys.service(id),
    queryFn: () => api.services.get(id),
    enabled: !!id,
    placeholderData: () => {
      // Show list-level data instantly while full detail (with tools/config) loads
      const services = qc.getQueryData<ServiceConnection[]>(queryKeys.services());
      const match = services?.find((s) => s.id === id);
      if (!match) return undefined;
      return { ...match, config: {}, tools: [] };
    },
  });
}

export function useCreateService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateServiceRequest) => api.services.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.services() }),
  });
}

export function useUpdateService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateServiceRequest }) =>
      api.services.update(id, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.services() });
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.id) });
    },
  });
}

export function useDeleteService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.services.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.services() }),
  });
}

export function useTestConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.services.test(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: queryKeys.service(id) });
      qc.invalidateQueries({ queryKey: queryKeys.services() });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useTools() {
  return useQuery({
    queryKey: queryKeys.tools(),
    queryFn: api.tools.list,
  });
}

export function useUpdateToolPermission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      serviceId,
      toolName,
      isEnabled,
      descriptionOverride,
      parametersSchemaOverride,
      httpMethodOverride,
      pathTemplateOverride,
    }: {
      serviceId: string;
      toolName: string;
      isEnabled: boolean;
      descriptionOverride?: string | null;
      parametersSchemaOverride?: Record<string, unknown> | null;
      httpMethodOverride?: string | null;
      pathTemplateOverride?: string | null;
    }) =>
      api.tools.updatePermission(serviceId, toolName, {
        is_enabled: isEnabled,
        description_override: descriptionOverride,
        parameters_schema_override: parametersSchemaOverride,
        http_method_override: httpMethodOverride,
        path_template_override: pathTemplateOverride,
      }),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
      qc.invalidateQueries({ queryKey: queryKeys.services() });
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.serviceId) });
    },
  });
}

export function useDiscoverServices() {
  return useMutation({
    mutationFn: () => api.discovery.scan(),
  });
}

export function useAuditLog(filters?: {
  limit?: number;
  offset?: number;
  serviceName?: string;
  toolName?: string;
  status?: string;
}) {
  const limit = filters?.limit ?? 50;
  const offset = filters?.offset ?? 0;
  return useQuery({
    queryKey: queryKeys.audit({
      limit,
      offset,
      serviceName: filters?.serviceName,
      toolName: filters?.toolName,
      status: filters?.status,
    }),
    queryFn: () =>
      api.audit.list({
        limit,
        offset,
        service_name: filters?.serviceName,
        tool_name: filters?.toolName,
        status: filters?.status,
      }),
  });
}

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: api.health.check,
    refetchInterval: 30_000,
  });
}

export function useProfiles(serviceId: string) {
  return useQuery({
    queryKey: queryKeys.profiles(serviceId),
    queryFn: () => api.services.getProfiles(serviceId),
    enabled: !!serviceId,
  });
}

export function useApplyProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, profileName }: { id: string; profileName: string }) =>
      api.services.applyProfile(id, profileName),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.services() });
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.id) });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useImportServices() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      yamlContent,
      tokenMap,
    }: {
      yamlContent: string;
      tokenMap: Record<string, string>;
    }) => api.services.importYaml(yamlContent, tokenMap),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.services() });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useCreateGenericTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      serviceId,
      data,
    }: {
      serviceId: string;
      data: GenericToolDefinition;
    }) => api.genericTools.create(serviceId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.serviceId) });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useImportOpenapi() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ serviceId, spec }: { serviceId: string; spec: string }) =>
      api.genericTools.importOpenapi(serviceId, spec),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.serviceId) });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useDeleteGenericTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      serviceId,
      toolName,
    }: {
      serviceId: string;
      toolName: string;
    }) => api.genericTools.delete(serviceId, toolName),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.serviceId) });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useUpdateGenericTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      serviceId,
      toolName,
      data,
    }: {
      serviceId: string;
      toolName: string;
      data: Record<string, unknown>;
    }) => api.genericTools.update(serviceId, toolName, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.service(variables.serviceId) });
      qc.invalidateQueries({ queryKey: queryKeys.tools() });
    },
  });
}

export function useTestGenericTool() {
  return useMutation({
    mutationFn: ({
      serviceId,
      toolName,
    }: {
      serviceId: string;
      toolName: string;
    }) => api.genericTools.testTool(serviceId, toolName),
  });
}

export function useUsers() {
  return useQuery({
    queryKey: queryKeys.users(),
    queryFn: api.users.list,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateUserRequest) => api.users.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.users() }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.users.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.users() }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string;
      data: {
        is_admin?: boolean;
        self_mcp_enabled?: boolean;
        allowed_service_ids?: string[];
      };
    }) => api.users.update(userId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}

export function useApps() {
  return useQuery({
    queryKey: queryKeys.apps(),
    queryFn: api.apps.list,
  });
}

export function useRenderApp() {
  return useMutation({
    mutationFn: ({
      name,
      args,
    }: {
      name: string;
      args?: Record<string, unknown>;
    }) => api.apps.render(name, args),
  });
}

export function useAppAction() {
  return useMutation({
    mutationFn: ({
      name,
      action,
      payload,
    }: {
      name: string;
      action: string;
      payload?: Record<string, unknown>;
    }) => api.apps.action(name, action, payload),
  });
}
