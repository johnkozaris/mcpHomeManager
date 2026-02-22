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

export function Users() {
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
          <h1 className="page-header">Users</h1>
          <p className="page-description">
            Manage user access to your homelab services
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowForm(!showForm)}
        >
          <UserPlus size={15} />
          {showForm ? "Cancel" : "Create User"}
        </Button>
      </div>

      {/* Create form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create User</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <Input
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value.replace(/\s/g, ""))}
              placeholder="e.g. alice"
              maxLength={100}
              error={
                username.length > 0 && username.length < 2
                  ? "Username must be at least 2 characters"
                  : username.length > 100
                    ? "Username must be 100 characters or less"
                    : undefined
              }
            />
            <Input
              label="Email (optional — for password recovery)"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alice@example.com"
              maxLength={254}
            />
            <Input
              label="Password (for web login)"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              maxLength={200}
              error={
                password.length > 0 && password.length < 8
                  ? `Password must be at least 8 characters (${password.length}/8)`
                  : undefined
              }
            />
            <p className="text-xs text-ink-tertiary -mt-2">
              Password is for web dashboard login. An MCP API key will also be
              generated automatically.
            </p>
            <Toggle
              checked={isAdmin}
              onChange={() => setIsAdmin(!isAdmin)}
              label="Admin (full access to all services)"
            />
            <Toggle
              checked={selfMcpEnabled}
              onChange={() => setSelfMcpEnabled(!selfMcpEnabled)}
              label="Self-MCP access (agent can manage services via MCP)"
            />
            {!isAdmin && services && services.length > 0 && (
              <div>
                <p className="section-label mb-2">Allowed Services</p>
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
                {parseApiError(createUser.error, "Failed to create user")}
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
              {createUser.isPending ? "Creating…" : "Create"}
            </Button>
          </div>
        </Card>
      )}

      {/* User list */}
      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage="Loading users…"
      >
        {users && users.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>
                {users.length} User{users.length !== 1 ? "s" : ""}
              </CardTitle>
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
                          Admin
                        </Badge>
                      )}
                      {user.self_mcp_enabled && (
                        <Badge variant="positive" className="ml-1">
                          <Wrench size={10} />
                          MCP
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
                      label="Admin"
                    />
                    <Toggle
                      checked={user.self_mcp_enabled}
                      onChange={(v) =>
                        updateUser.mutate({
                          userId: user.id,
                          data: { self_mcp_enabled: v },
                        })
                      }
                      label="MCP"
                    />
                    <span className="text-xs text-ink-tertiary">
                      {user.is_admin
                        ? "All services"
                        : `${user.allowed_service_ids.length} service${user.allowed_service_ids.length !== 1 ? "s" : ""}`}
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
                {parseApiError(updateUser.error, "Failed to update user")}
              </p>
            )}
          </Card>
        ) : (
          <div className="text-center py-12 text-ink-tertiary">
            <UserPlus size={32} className="mx-auto mb-3 opacity-40" />
            <p className="text-base">No users yet</p>
            <p className="text-sm mt-1">
              Create a user to get started with multi-user access control.
            </p>
          </div>
        )}
      </QueryState>

      <ConfirmDialog
        open={!!deleteId}
        title="Delete user"
        description="This will permanently remove the user and revoke their API key."
        confirmText="Delete"
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
