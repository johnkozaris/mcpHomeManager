import { useState } from "react";
import { UserPlus, Shield, Trash2, Wrench } from "lucide-react";
import {
  useUsers,
  useCreateUser,
  useDeleteUser,
  useUpdateUser,
  useServices,
} from "@/hooks/useServices";
import { parseApiError } from "@/lib/utils";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Toggle } from "@/components/ui/Toggle";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { QueryState } from "@/components/ui/QueryState";
import { EmptyState } from "@/components/ui/EmptyState";
import { useTranslation } from "react-i18next";

export function Users() {
  const { t } = useTranslation("users", { keyPrefix: "page" });
  const { data: users, isLoading, isError, error } = useUsers();
  const { data: services } = useServices();
  const createUser = useCreateUser();
  const deleteUser = useDeleteUser();
  const updateUser = useUpdateUser();

  const [showForm, setShowForm] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [selfMcpEnabled, setSelfMcpEnabled] = useState(false);
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleCreate = () => {
    const trimmed = username.trim();
    if (!trimmed) return;
    createUser.mutate(
      {
        username: trimmed,
        password: password || undefined,
        email: email || undefined,
        is_admin: isAdmin,
        self_mcp_enabled: selfMcpEnabled,
        allowed_service_ids: isAdmin ? [] : selectedServices,
      },
      {
        onSuccess: () => {
          setUsername("");
          setEmail("");
          setPassword("");
          setIsAdmin(false);
          setSelfMcpEnabled(false);
          setSelectedServices([]);
          setShowForm(false);
        },
      },
    );
  };

  const toggleService = (id: string) => {
    setSelectedServices((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  return (
      <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">{t("title")}</h1>
          <p className="page-description">{t("description")}</p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowForm(!showForm)}
        >
          <UserPlus size={15} />
          {showForm ? t("actions.cancel") : t("actions.createUser")}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{t("form.title")}</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <Input
              label={t("form.fields.username.label")}
              value={username}
              onChange={(e) => setUsername(e.target.value.replace(/\s/g, ""))}
              placeholder={t("form.fields.username.placeholder")}
              maxLength={100}
              error={
                username.length > 0 && username.length < 2
                  ? t("form.fields.username.errors.minLength")
                  : username.length > 100
                    ? t("form.fields.username.errors.maxLength")
                    : undefined
              }
            />
            <Input
              label={t("form.fields.email.label")}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("form.fields.email.placeholder")}
              maxLength={254}
            />
            <Input
              label={t("form.fields.password.label")}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("form.fields.password.placeholder")}
              maxLength={200}
              error={
                password.length > 0 && password.length < 8
                  ? t("form.fields.password.errors.minLength", {
                      current: password.length,
                    })
                  : undefined
              }
            />
            <p className="text-xs text-ink-tertiary -mt-2">
              {t("form.passwordHelp")}
            </p>
            <Toggle
              checked={isAdmin}
              onChange={() => setIsAdmin(!isAdmin)}
              label={t("form.toggles.admin")}
            />
            <Toggle
              checked={selfMcpEnabled}
              onChange={() => setSelfMcpEnabled(!selfMcpEnabled)}
              label={t("form.toggles.selfMcp")}
            />
            {!isAdmin && services && services.length > 0 && (
              <div>
                <p className="section-label mb-2">{t("form.allowedServices")}</p>
                <div className="space-y-1.5">
                  {services.map((svc) => (
                    <label
                      key={svc.id}
                      className="flex items-center gap-2.5 text-sm text-ink-secondary cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedServices.includes(svc.id)}
                        onChange={() => toggleService(svc.id)}
                        className="rounded"
                      />
                      {svc.display_name}
                    </label>
                  ))}
                </div>
              </div>
            )}
            {createUser.isError && (
              <p className="text-sm text-rust">
                {parseApiError(createUser.error, t("errors.createUserFailed"))}
              </p>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreate}
              disabled={
                !username.trim() ||
                username.length < 2 ||
                (password.length > 0 && password.length < 8) ||
                createUser.isPending
              }
            >
              {createUser.isPending ? t("actions.creating") : t("actions.create")}
            </Button>
          </div>
        </Card>
      )}

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage={t("query.loading")}
      >
        {users && users.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>{t("list.count", { count: users.length })}</CardTitle>
            </CardHeader>
            <div className="divide-y divide-line">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between py-3.5"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-terra-bg flex items-center justify-center">
                      <span className="text-sm font-semibold text-terra">
                        {user.username[0]?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <span className="text-base font-medium text-ink">
                        {user.username}
                      </span>
                      {user.is_admin && (
                        <Badge variant="brand" className="ml-2">
                          <Shield size={10} />
                          {t("list.badges.admin")}
                        </Badge>
                      )}
                      {user.self_mcp_enabled && (
                        <Badge variant="positive" className="ml-1">
                          <Wrench size={10} />
                          {t("list.badges.mcp")}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Toggle
                      checked={user.is_admin}
                      onChange={(v) =>
                        updateUser.mutate({
                          userId: user.id,
                          data: { is_admin: v },
                        })
                      }
                      label={t("list.toggles.admin")}
                    />
                    <Toggle
                      checked={user.self_mcp_enabled}
                      onChange={(v) =>
                        updateUser.mutate({
                          userId: user.id,
                          data: { self_mcp_enabled: v },
                        })
                      }
                      label={t("list.toggles.mcp")}
                    />
                    <span className="text-xs text-ink-tertiary">
                      {user.is_admin
                        ? t("list.access.allServices")
                        : t("list.access.serviceCount", {
                            count: user.allowed_service_ids.length,
                          })}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteId(user.id)}
                    >
                      <Trash2 size={14} className="text-rust" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            {updateUser.isError && (
              <p className="text-sm text-rust px-6 pb-3">
                {parseApiError(updateUser.error, t("errors.updateUserFailed"))}
              </p>
            )}
          </Card>
        ) : (
          <EmptyState
            icon={UserPlus}
            title={t("empty.title")}
            description={t("empty.description")}
          />
        )}
      </QueryState>

      <ConfirmDialog
        open={!!deleteId}
        title={t("dialogs.delete.title")}
        description={t("dialogs.delete.description")}
        confirmText={t("dialogs.delete.confirm")}
        variant="danger"
        onConfirm={() => {
          if (deleteId) {
            deleteUser.mutate(deleteId, {
              onSuccess: () => setDeleteId(null),
            });
          }
        }}
        onCancel={() => setDeleteId(null)}
        isLoading={deleteUser.isPending}
      />
    </div>
  );
}
