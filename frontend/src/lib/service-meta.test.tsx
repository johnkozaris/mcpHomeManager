import { render } from "@testing-library/react";
import {
  SERVICE_META,
  getServiceMeta,
  ServiceIcon,
  ServiceIconBadge,
} from "./service-meta";
import { BUILTIN_SERVICE_TYPES, type ServiceType } from "./types";

describe("SERVICE_META", () => {
  const expectedTypes: ServiceType[] = [
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
    "cloudflare",
    "tailscale",
    "generic_rest",
  ];

  it("has an entry for every expected service type", () => {
    for (const type of expectedTypes) {
      expect(SERVICE_META[type]).toBeDefined();
      expect(SERVICE_META[type].label).toBeTruthy();
      expect(SERVICE_META[type].description).toBeTruthy();
      expect(SERVICE_META[type].color).toMatch(/^var\(--brand-/);
      expect(SERVICE_META[type].icon).toBeDefined();
    }
  });

  it("has no extra entries beyond expected types", () => {
    expect(Object.keys(SERVICE_META).sort()).toEqual([...expectedTypes].sort());
  });

  it("prioritizes custom api first in onboarding order", () => {
    expect(BUILTIN_SERVICE_TYPES[0]).toBe("generic_rest");
  });
});

describe("getServiceMeta", () => {
  it("returns metadata for a known type", () => {
    const meta = getServiceMeta("forgejo");
    expect(meta.label).toBe("Forgejo");
  });

  it("returns a fallback for an unknown type", () => {
    const meta = getServiceMeta("nonexistent" as ServiceType);
    expect(meta).toBeDefined();
    expect(meta.label).toBe("Unknown");
  });
});

describe("ServiceIcon", () => {
  it("renders an SVG icon", () => {
    const { container } = render(<ServiceIcon type="forgejo" />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});

describe("ServiceIconBadge", () => {
  it("renders at sm size", () => {
    const { container } = render(
      <ServiceIconBadge type="paperless" size="sm" />,
    );
    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass("w-7", "h-7");
  });

  it("renders at md size by default", () => {
    const { container } = render(<ServiceIconBadge type="immich" />);
    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass("w-9", "h-9");
  });

  it("renders at lg size", () => {
    const { container } = render(
      <ServiceIconBadge type="nextcloud" size="lg" />,
    );
    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass("w-11", "h-11");
  });

  it("applies the service color with transparency as background", () => {
    const { container } = render(<ServiceIconBadge type="forgejo" />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper?.style.backgroundColor).toBeTruthy();
  });
});
