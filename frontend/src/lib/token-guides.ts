import { translateList, translateText } from "@/i18n/translate";
import type { BuiltinServiceType } from "./types";

interface TokenGuide {
  steps: string[];
  note?: string;
}

type TokenGuideType = Exclude<BuiltinServiceType, "generic_rest">;

const TOKEN_GUIDE_DEFAULTS: Record<TokenGuideType, TokenGuide> = {
  forgejo: {
    steps: [
      "Open your Forgejo instance and log in with your account",
      'Click your profile avatar in the top-right corner and select "Settings"',
      'In the left sidebar, click "Applications"',
      'Under "Manage Access Tokens", enter a name for your token (e.g., "{appName}")',
      "Select the permissions your token needs — for full access, check all scopes. At minimum you need: read:organization, read:repository, read:issue, write:issue",
      'Click "Generate Token" and copy the token immediately — it won’t be shown again',
      "Paste the token in the field above",
    ],
  },
  homeassistant: {
    steps: [
      "Open your Home Assistant instance and log in",
      "Click your username/profile in the bottom of the left sidebar",
      'Scroll down to the "Long-Lived Access Tokens" section at the bottom of the page',
      'Click "Create Token"',
      'Give it a name like "{appName}" and click OK',
      "Copy the token shown in the dialog — it will only be displayed once",
      "Paste the token in the field above",
    ],
    note: "Home Assistant tokens start with eyJ…",
  },
  paperless: {
    steps: [
      "Open your Paperless-ngx instance and log in as an admin user",
      "Click the gear icon or navigate to Settings in the top navigation",
      'Scroll down or look for the "API" section',
      "Your API token is shown here — click the copy icon to copy it",
      'If no token exists, click "Generate" to create one',
      "Paste the token in the field above",
    ],
  },
  immich: {
    steps: [
      "Open your Immich instance and log in",
      "Click your profile avatar in the top-right corner",
      'Select "Account Settings" from the dropdown',
      'Scroll down to "API Keys"',
      'Click "New API Key", give it a name like "{appName}"',
      "Copy the generated key immediately — it won’t be shown again",
      "Paste the key in the field above",
    ],
  },
  nextcloud: {
    steps: [
      "Open your Nextcloud instance and log in",
      'Click your profile avatar in the top-right corner and select "Settings" (or "Personal settings")',
      'In the left sidebar, click "Security"',
      'Scroll down to the "Devices & sessions" section',
      'Enter "{appName}" as the app name in the text field at the bottom',
      'Click "Create new app password"',
      "Copy the generated password — this is your API token",
      "Paste it in the field above",
    ],
    note: "Format: username:app-password (e.g., admin:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx)",
  },
  uptimekuma: {
    steps: [
      "Open your Uptime Kuma instance and log in",
      'Click "Settings" in the left sidebar',
      'Navigate to the "API Keys" tab',
      'Click "Add API Key" and enter a name like "{appName}"',
      "Set an expiry date or leave it blank for no expiration",
      'Click "Create" and copy the generated API key',
      "Paste the key in the field above",
    ],
  },
  adguard: {
    steps: [
      "AdGuard Home uses basic authentication (username and password) rather than API tokens",
      "Use the same username and password you use to log into the AdGuard web interface",
      "Enter them in the field above in the format: username:password",
    ],
    note: 'For example, if your login is "admin" and password is "mypass", enter admin:mypass',
  },
  nginxproxymanager: {
    steps: [
      "Nginx Proxy Manager uses your login credentials for API access",
      "Enter your email and password in the format: email:password",
      "These are the same credentials you use to log into the NPM web interface",
    ],
    note: "Format: email:password (e.g., admin@example.com:changeme)",
  },
  portainer: {
    steps: [
      "Portainer uses your login credentials for API access",
      "Enter your username and password in the format: username:password",
      "These are the same credentials you use to log into the Portainer web interface",
    ],
    note: "Format: username:password (e.g., admin:mypassword)",
  },
  freshrss: {
    steps: [
      "FreshRSS uses a separate API password for programmatic access",
      "In FreshRSS, go to Settings → Profile → API Management",
      "Enable the “Allow API access” option if not already enabled",
      "Set an API password (this is different from your login password)",
      "Enter your FreshRSS username and API password in the format: username:api_password",
    ],
    note: "Format: username:api_password — the API password is set separately in FreshRSS settings, not your login password",
  },
  wallabag: {
    steps: [
      "Open your Wallabag instance and log in",
      "Go to API clients management (Developer section in settings)",
      'Click "Create a new client" and note the client ID and client secret',
      "Enter all four values in the format: client_id:client_secret:username:password",
    ],
    note: "Format: client_id:client_secret:username:password (4 parts separated by colons)",
  },
  stirlingpdf: {
    steps: [
      "Open your Stirling PDF instance and log in as an administrator",
      "Click the settings cog (⚙️) in the top right corner to open Account Settings",
      "Find or generate your personal API key in the settings panel",
      "Alternatively, use the global API key set via SECURITY_CUSTOMGLOBALAPIKEY environment variable",
      "Paste the API key in the field above",
    ],
    note: "Uses X-API-KEY header. Login must be enabled in Stirling PDF for API key auth to work",
  },
  wikijs: {
    steps: [
      "Open your Wiki.js instance and log in as an administrator",
      "Navigate to Administration → API Access",
      'Click "Create API Key" and set a name (e.g., "{appName}")',
      "Select the appropriate permission group (Full Access recommended)",
      "Set an expiration date or leave blank for no expiry",
      "Copy the generated API key and paste it in the field above",
    ],
  },
  tailscale: {
    steps: [
      "Open the Tailscale admin console at https://login.tailscale.com/admin",
      "Navigate to Settings → Keys",
      'Under "API access tokens", click "Generate access token..."',
      "Set an expiry for the token or leave the default",
      'Click "Generate" and copy the token immediately — it won’t be shown again',
      "Paste the token in the field above",
    ],
    note: "Tailscale API keys start with tskey-api-... and authenticate against the Tailscale API (api.tailscale.com/api/v2)",
  },
  calibreweb: {
    steps: [
      "Calibre-Web uses your login credentials for API access",
      "Enter your Calibre-Web username and password in the format: username:password",
      "These are the same credentials you use to log into the Calibre-Web web interface",
    ],
    note: "Default credentials are admin/admin123 — change them before connecting. Format: username:password",
  },
  cloudflare: {
    steps: [
      "Open the Cloudflare dashboard at https://dash.cloudflare.com",
      'Click your profile icon in the top-right corner and select "My Profile"',
      'In the left sidebar, click "API Tokens"',
      'Click "Create Token"',
      "Use a custom token template and set the following permissions: Zone:DNS:Edit, Zone:Zone:Read, Account:Cloudflare Tunnel:Edit",
      "Optionally restrict the token to specific zones or accounts",
      'Click "Continue to summary" then "Create Token"',
      "Copy the token immediately — it won’t be shown again",
      "Paste the token in the field above",
    ],
    note: "Use https://api.cloudflare.com as the base URL. The token authenticates via Bearer header.",
  },
};

const TOKEN_GUIDE_TYPES = Object.keys(
  TOKEN_GUIDE_DEFAULTS,
) as TokenGuideType[];

export function getTokenGuides(
  appName: string,
): Partial<Record<BuiltinServiceType, TokenGuide>> {
  const guides: Partial<Record<BuiltinServiceType, TokenGuide>> = {};

  for (const type of TOKEN_GUIDE_TYPES) {
    const guide = TOKEN_GUIDE_DEFAULTS[type];
    if (!guide) {
      continue;
    }

    const guideKey = `tokenGuides:guides.${type}`;
    const fallbackSteps = guide.steps.map((step) =>
      step.replaceAll("{appName}", appName),
    );
    const translatedGuide: TokenGuide = {
      steps: translateList(`${guideKey}.steps`, fallbackSteps, { appName }),
    };

    if (guide.note) {
      translatedGuide.note = translateText(
        `${guideKey}.note`,
        guide.note.replaceAll("{appName}", appName),
        {
          appName,
        },
      );
    }

    guides[type] = translatedGuide;
  }

  return guides;
}
