import { useEffect } from "react";
import { useParams, useNavigate } from "@tanstack/react-router";
import {
  ArrowLeft,
  HeartPulse,
  Wrench,
  Clock,
  Shield,
  Zap,
  Trash2,
  ExternalLink,
  Upload,
  Plus,
} from "lucide-react";
import {
  useService,
  useTestConnection,
  useDeleteService,
  useUpdateService,
  useUpdateToolPermission,
  useProfiles,
  useApplyProfile,
  useApps,
  useRenderApp,
  useAppAction,
  useDeleteGenericTool,
  useTestGenericTool,
} from "@/hooks/useServices";
import { AppCard } from "@/components/services/AppCard";
import { ToolList } from "@/components/services/ToolList";
import { AddToolModal } from "@/components/services/AddToolModal";
import { ImportOpenAPIModal } from "@/components/services/ImportOpenAPIModal";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { QueryState } from "@/components/ui/QueryState";
import { StatCard } from "@/components/ui/StatCard";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";
import { Badge } from "@/components/ui/Badge";
import { MonacoEditor } from "@/components/ui/MonacoEditor";
import { ServiceIconBadge, getServiceMeta } from "@/lib/service-meta";
import { formatRelativeTime } from "@/lib/utils";
import { useServiceDetailState } from "@/hooks/useServiceDetailState";

function ProfileChips({
  serviceId,
  onApply,
  isApplying,
}: {
  serviceId: string;
  onApply: (args: { id: string; profileName: string }) => void;
  isApplying: boolean;
}) {
  const { data: profiles } = useProfiles(serviceId);
  if (!profiles || profiles.length === 0) return null;

  return (
    <div className="flex items-center gap-2 mb-4">
      <Shield size={14} className="text-ink-tertiary" />
      <span className="text-xs text-ink-tertiary font-medium">Profiles:</span>
      {profiles.map((p) => (
        <button
          key={p.name}
          onClick={() => onApply({ id: serviceId, profileName: p.name })}
          disabled={isApplying}
          className="chip chip-inactive text-xs"
          title={p.description}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

export function ServiceDetail() {
  const { id } = useParams({ from: "/app/services/$id" });
  const navigate = useNavigate();
  const { data: service, isLoading, isError, error } = useService(id);
  const testConnection = useTestConnection();
  const deleteService = useDeleteService();
  const updateService = useUpdateService();
  const updateToolPermission = useUpdateToolPermission();
  const applyProfile = useApplyProfile();
  const [state, dispatch] = useServiceDetailState();
  const { data: apps } = useApps();
  const renderApp = useRenderApp();
  const appAction = useAppAction();
  const deleteGenericTool = useDeleteGenericTool();
  const testGenericTool = useTestGenericTool();

  // Handle postMessage from app preview iframe
  useEffect(() => {
    if (!state.previewAppName) return;
    const currentApp = state.previewAppName;
    function handleIframeMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin && event.origin !== "null")
        return;
      if (event.data?.type === "mcp-app-action" && currentApp) {
        appAction.mutate(
          {
            name: currentApp,
            action: event.data.action,
            payload: event.data.payload,
          },
          {
            onSuccess: (html) =>
              dispatch({ type: "UPDATE_APP_PREVIEW_HTML", html }),
          },
        );
      }
    }
    window.addEventListener("message", handleIframeMessage);
    return () => window.removeEventListener("message", handleIframeMessage);
  }, [appAction, dispatch, state.previewAppName]);

  if (!id) return <div className="text-sm text-rust">Invalid service ID.</div>;

  return (
    <QueryState
      isLoading={isLoading}
      isError={isError}
      error={error instanceof Error ? error : null}
      loadingMessage="Loading service\u2026"
      errorMessage="Service not found or backend unreachable."
    >
      {service ? (
        (() => {
          const meta = getServiceMeta(service.service_type);
          const lastChecked = service.last_health_check
            ? formatRelativeTime(new Date(service.last_health_check))
            : "never";
          const hasCustomTools = service.tools.some(
            (t) => t.http_method != null,
          );
          const showConfigEditor =
            service.service_type === "generic_rest" || hasCustomTools;

          return (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => navigate({ to: "/services" })}
                    className="text-ink-tertiary hover:text-ink transition-colors"
                  >
                    <ArrowLeft size={18} />
                  </button>
                  <ServiceIconBadge type={service.service_type} size="lg" />
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h1 className="text-2xl font-semibold tracking-tight text-ink">
                        {service.display_name}
                      </h1>
                      <Badge
                        variant={
                          service.health_status === "healthy"
                            ? "positive"
                            : service.health_status === "unhealthy"
                              ? "critical"
                              : "default"
                        }
                      >
                        {service.health_status}
                      </Badge>
                    </div>
                    <p className="text-sm text-ink-secondary mt-0.5">
                      {meta.description}
                    </p>
                    <a
                      href={service.base_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-terra hover:text-terra-light transition-colors mt-0.5"
                    >
                      {service.base_url}
                      <ExternalLink size={10} />
                    </a>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={
                      state.editing
                        ? () => {
                            const data: Record<string, unknown> = {};
                            if (state.editDisplayName !== service.display_name)
                              data.display_name = state.editDisplayName;
                            if (state.editUrl !== service.base_url)
                              data.base_url = state.editUrl;
                            if (state.editToken)
                              data.api_token = state.editToken.trim();
                            if (showConfigEditor) {
                              try {
                                const parsed = JSON.parse(state.editConfig);
                                if (
                                  JSON.stringify(parsed) !==
                                  JSON.stringify(service.config)
                                )
                                  data.config = parsed;
                                dispatch({
                                  type: "SET_CONFIG_ERROR",
                                  error: null,
                                });
                              } catch {
                                dispatch({
                                  type: "SET_CONFIG_ERROR",
                                  error:
                                    "Invalid JSON \u2014 fix the config before saving.",
                                });
                                return;
                              }
                            }
                            if (Object.keys(data).length > 0)
                              updateService.mutate(
                                { id: service.id, data },
                                {
                                  onSuccess: () =>
                                    dispatch({ type: "EDIT_SAVED" }),
                                },
                              );
                            else dispatch({ type: "EDIT_SAVED" });
                          }
                        : () => dispatch({ type: "START_EDIT", service })
                    }
                  >
                    {state.editing ? "Save" : "Edit"}
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={() => testConnection.mutate(service.id)}
                    disabled={testConnection.isPending}
                  >
                    <Zap size={14} />
                    {testConnection.isPending
                      ? "Testing\u2026"
                      : "Test Connection"}
                  </Button>
                </div>
              </div>

              {testConnection.data && (
                <div
                  className={[
                    "flex items-center gap-2 p-3 rounded-xl text-sm border",
                    testConnection.data.success
                      ? "bg-sage-bg text-sage border-sage"
                      : "bg-rust-bg text-rust border-rust",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "w-1.5 h-1.5 rounded-full",
                      testConnection.data.success ? "bg-sage" : "bg-rust",
                    ].join(" ")}
                  />
                  {testConnection.data.message}
                </div>
              )}

              {state.editing ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Edit Connection</CardTitle>
                  </CardHeader>
                  <div className="space-y-3">
                    <Input
                      label="Display Name"
                      value={state.editDisplayName}
                      onChange={(e) =>
                        dispatch({
                          type: "SET_EDIT_DISPLAY_NAME",
                          value: e.target.value,
                        })
                      }
                    />
                    <Input
                      label="Base URL"
                      value={state.editUrl}
                      onChange={(e) =>
                        dispatch({
                          type: "SET_EDIT_URL",
                          value: e.target.value,
                        })
                      }
                      onBlur={() => {
                        const trimmed = state.editUrl.trim();
                        if (trimmed && !/^https?:\/\//i.test(trimmed)) {
                          dispatch({
                            type: "SET_EDIT_URL",
                            value: `https://${trimmed}`,
                          });
                        }
                      }}
                    />
                    <Input
                      label="API Token"
                      type="password"
                      placeholder="Leave empty to keep current"
                      value={state.editToken}
                      onChange={(e) =>
                        dispatch({
                          type: "SET_EDIT_TOKEN",
                          value: e.target.value,
                        })
                      }
                    />
                    {showConfigEditor && (
                      <div>
                        <p className="section-label mb-2">
                          Configuration (JSON)
                        </p>
                        <MonacoEditor
                          value={state.editConfig}
                          onChange={(v) =>
                            dispatch({ type: "SET_EDIT_CONFIG", value: v })
                          }
                          language="json"
                          height="200px"
                        />
                        {state.configError && (
                          <p className="text-xs text-rust mt-1.5">
                            {state.configError}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <div className="grid grid-cols-4 gap-4">
                  <StatCard
                    label="Health"
                    value={service.health_status}
                    icon={HeartPulse}
                    iconColor={
                      service.health_status === "healthy"
                        ? "var(--sage)"
                        : "var(--rust)"
                    }
                  />
                  <StatCard
                    label="Tools"
                    value={service.tools.length}
                    sub={`${service.tools.filter((t) => t.is_enabled).length} enabled`}
                    icon={Wrench}
                    iconColor="var(--info)"
                  />
                  <StatCard
                    label="Last Tested"
                    value={lastChecked}
                    icon={Clock}
                    iconColor="var(--clay)"
                  />
                  <Card>
                    <p className="section-label mb-2">State</p>
                    <Toggle
                      checked={service.is_enabled}
                      onChange={() =>
                        updateService.mutate({
                          id: service.id,
                          data: { is_enabled: !service.is_enabled },
                        })
                      }
                      label={service.is_enabled ? "Active" : "Disabled"}
                    />
                  </Card>
                </div>
              )}

              {(() => {
                const serviceApps =
                  apps?.filter((a) => a.service_name === service.name) ?? [];
                if (serviceApps.length === 0) return null;
                return (
                  <Card>
                    <CardHeader>
                      <CardTitle>MCP Apps ({serviceApps.length})</CardTitle>
                    </CardHeader>
                    <div className="space-y-2">
                      {serviceApps.map((app) => (
                        <AppCard
                          key={app.name}
                          app={app}
                          onPreview={(a) => {
                            dispatch({
                              type: "SET_APP_PREVIEW",
                              html: null,
                              name: a.name,
                            });
                            renderApp.mutate(
                              { name: a.name },
                              {
                                onSuccess: (html) =>
                                  dispatch({
                                    type: "UPDATE_APP_PREVIEW_HTML",
                                    html,
                                  }),
                              },
                            );
                          }}
                        />
                      ))}
                    </div>
                  </Card>
                );
              })()}

              {state.appPreviewHtml && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                  <div
                    className="absolute inset-0 bg-black/40"
                    onClick={() =>
                      dispatch({
                        type: "SET_APP_PREVIEW",
                        html: null,
                        name: null,
                      })
                    }
                    aria-hidden="true"
                  />
                  <div
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="app-preview-title"
                    className="relative w-full max-w-3xl h-[80vh] bg-surface rounded-2xl border border-line shadow-elevated overflow-hidden flex flex-col"
                  >
                    <div className="flex items-center justify-between px-6 py-3 border-b border-line">
                      <h2
                        id="app-preview-title"
                        className="text-sm font-semibold text-ink"
                      >
                        App Preview
                      </h2>
                      <button
                        onClick={() =>
                          dispatch({
                            type: "SET_APP_PREVIEW",
                            html: null,
                            name: null,
                          })
                        }
                        className="text-ink-tertiary hover:text-ink transition-colors"
                        aria-label="Close preview"
                      >
                        &times;
                      </button>
                    </div>
                    <iframe
                      srcDoc={state.appPreviewHtml}
                      sandbox="allow-scripts"
                      className="flex-1 w-full border-0"
                      title="App Preview"
                    />
                  </div>
                </div>
              )}

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between w-full">
                    <CardTitle>MCP Tools ({service.tools.length})</CardTitle>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() =>
                          dispatch({ type: "SET_IMPORT_OPEN", open: true })
                        }
                      >
                        <Upload size={14} />
                        Import OpenAPI
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() =>
                          dispatch({ type: "SET_ADD_TOOL_OPEN", open: true })
                        }
                      >
                        <Plus size={14} />
                        Add Tool
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <ProfileChips
                  serviceId={service.id}
                  onApply={applyProfile.mutate}
                  isApplying={applyProfile.isPending}
                />
                <ToolList
                  tools={service.tools}
                  showJsonView
                  onToggle={(tool, enabled) => {
                    updateToolPermission.mutate({
                      serviceId: service.id,
                      toolName: tool.name,
                      isEnabled: enabled,
                      descriptionOverride: tool.description_override,
                      parametersSchemaOverride: tool.parameters_schema_override,
                      httpMethodOverride: tool.http_method_override,
                      pathTemplateOverride: tool.path_template_override,
                    });
                  }}
                  onSaveOverrides={(tool, descOverride, schemaOverride, methodOverride, pathOverride) => {
                    updateToolPermission.mutate({
                      serviceId: service.id,
                      toolName: tool.name,
                      isEnabled: tool.is_enabled,
                      descriptionOverride: descOverride,
                      parametersSchemaOverride: schemaOverride,
                      httpMethodOverride: methodOverride,
                      pathTemplateOverride: pathOverride,
                    });
                  }}
                  onDelete={(toolName) =>
                    dispatch({ type: "SET_DELETE_TOOL_NAME", name: toolName })
                  }
                  onEditDefinition={(toolName) => {
                    const tool = service.tools.find((t) => t.name === toolName);
                    if (tool) {
                      dispatch({
                        type: "SET_EDIT_TOOL_DEF",
                        tool: {
                          tool_name: tool.name,
                          description: tool.description,
                          http_method: tool.http_method ?? "GET",
                          path_template: tool.path_template ?? "",
                          params_schema: tool.parameters_schema,
                        },
                      });
                    }
                  }}
                  onTestTool={(toolName) => {
                    dispatch({ type: "SET_TESTING_TOOL_NAME", name: toolName });
                    testGenericTool.mutate(
                      { serviceId: service.id, toolName },
                      {
                        onSuccess: (result) => {
                          dispatch({
                            type: "SET_TEST_TOOL_RESULT",
                            toolName,
                            result,
                          });
                        },
                        onError: () => {
                          dispatch({
                            type: "SET_TEST_TOOL_RESULT",
                            toolName,
                            result: {
                              success: false,
                              message: "Request failed",
                            },
                          });
                        },
                        onSettled: () => {
                          dispatch({
                            type: "SET_TESTING_TOOL_NAME",
                            name: null,
                          });
                        },
                      },
                    );
                  }}
                  testResults={state.testToolResults}
                  testingTool={state.testingToolName}
                />
              </Card>

              <ImportOpenAPIModal
                open={state.importOpen}
                onClose={() =>
                  dispatch({ type: "SET_IMPORT_OPEN", open: false })
                }
                serviceId={service.id}
              />
              <AddToolModal
                key={state.addToolOpen ? "create" : "create-closed"}
                open={state.addToolOpen}
                onClose={() =>
                  dispatch({ type: "SET_ADD_TOOL_OPEN", open: false })
                }
                serviceId={service.id}
              />
              <AddToolModal
                key={state.editToolDef?.tool_name ?? "__none__"}
                open={!!state.editToolDef}
                onClose={() =>
                  dispatch({ type: "SET_EDIT_TOOL_DEF", tool: null })
                }
                serviceId={service.id}
                editTool={state.editToolDef}
              />
              <ConfirmDialog
                open={!!state.deleteToolName}
                title="Delete tool"
                description={`This will permanently remove the tool "${state.deleteToolName ?? ""}" from this service.`}
                confirmText="Delete"
                variant="danger"
                onConfirm={() => {
                  if (state.deleteToolName) {
                    deleteGenericTool.mutate(
                      {
                        serviceId: service.id,
                        toolName: state.deleteToolName,
                      },
                      {
                        onSettled: () =>
                          dispatch({
                            type: "SET_DELETE_TOOL_NAME",
                            name: null,
                          }),
                      },
                    );
                  }
                }}
                onCancel={() =>
                  dispatch({ type: "SET_DELETE_TOOL_NAME", name: null })
                }
                isLoading={deleteGenericTool.isPending}
              />

              <div className="rounded-xl border border-rust p-5">
                <h3 className="text-sm font-semibold text-rust mb-1">
                  Remove service
                </h3>
                <p className="text-xs text-ink-secondary mb-4">
                  This will permanently remove the service and all its
                  registered tools from MCP.
                </p>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() =>
                    dispatch({ type: "SET_DELETE_OPEN", open: true })
                  }
                >
                  <Trash2 size={14} />
                  Delete Service
                </Button>
                <ConfirmDialog
                  open={state.deleteOpen}
                  title="Delete service"
                  description="This will permanently remove the service and all its registered tools from MCP."
                  confirmText="Delete"
                  variant="danger"
                  onConfirm={() =>
                    deleteService.mutate(service.id, {
                      onSuccess: () => navigate({ to: "/services" }),
                    })
                  }
                  onCancel={() =>
                    dispatch({ type: "SET_DELETE_OPEN", open: false })
                  }
                  isLoading={deleteService.isPending}
                />
              </div>
            </div>
          );
        })()
      ) : (
        <div className="text-sm text-ink-tertiary">Service not found.</div>
      )}
    </QueryState>
  );
}
