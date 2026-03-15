import { useState, useRef } from "react";

interface DataPoint {
  label: string;
  value: number;
}

interface Props {
  data: DataPoint[];
  height?: number;
  color?: string;
}

export function MiniAreaChart({ data, height = 192, color = "var(--terra)" }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; point: DataPoint } | null>(null);

  if (data.length === 0) return null;

  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const padTop = 8;
  const padBottom = 24;
  const padLeft = 32;
  const padRight = 8;
  const chartH = height - padTop - padBottom;

  function xPos(i: number, width: number) {
    const usable = width - padLeft - padRight;
    return padLeft + (data.length === 1 ? usable / 2 : (i / (data.length - 1)) * usable);
  }

  function yPos(v: number) {
    return padTop + chartH - (v / maxVal) * chartH;
  }

  function buildPath(width: number) {
    const pts = data.map((d, i) => ({ x: xPos(i, width), y: yPos(d.value) }));
    const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
    const last = pts[pts.length - 1]!;
    const first = pts[0]!;
    const area = `${line} L${last.x},${padTop + chartH} L${first.x},${padTop + chartH} Z`;
    return { line, area };
  }

  // Y-axis ticks (3-4 nice values)
  const tickCount = 3;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) =>
    Math.round((maxVal / tickCount) * i),
  );

  // X-axis labels — show every Nth to avoid overlap
  const labelStep = Math.max(1, Math.ceil(data.length / 6));

  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const width = rect.width;

    let closest = 0;
    let closestDist = Infinity;
    for (let i = 0; i < data.length; i++) {
      const dist = Math.abs(xPos(i, width) - mx);
      if (dist < closestDist) {
        closestDist = dist;
        closest = i;
      }
    }
    const point = data[closest]!;
    setTooltip({ x: xPos(closest, width), y: yPos(point.value), point });
  }

  // Use a viewBox-less SVG so it fills the container and we can compute positions from actual width
  // We render with a default width=600 for the path, and use CSS width:100%
  const W = 600;
  const { line, area } = buildPath(W);

  return (
    <div className="relative" style={{ height }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${height}`}
        className="w-full h-full"
        preserveAspectRatio="none"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setTooltip(null)}
      >
        <defs>
          <linearGradient id="miniAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* Y grid lines */}
        {ticks.map((t) => (
          <line
            key={t}
            x1={padLeft}
            x2={W - padRight}
            y1={yPos(t)}
            y2={yPos(t)}
            stroke="var(--line)"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        ))}

        {/* Area fill */}
        <path d={area} fill="url(#miniAreaGrad)" />

        {/* Line */}
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
        />

        {/* Y-axis labels */}
        {ticks.map((t) => (
          <text
            key={t}
            x={padLeft - 6}
            y={yPos(t) + 3}
            textAnchor="end"
            fontSize={10}
            fill="var(--ink-tertiary)"
          >
            {t}
          </text>
        ))}

        {/* X-axis labels */}
        {data.map((d, i) =>
          i % labelStep === 0 ? (
            <text
              key={i}
              x={xPos(i, W)}
              y={height - 4}
              textAnchor="middle"
              fontSize={10}
              fill="var(--ink-tertiary)"
            >
              {d.label}
            </text>
          ) : null,
        )}

        {/* Tooltip crosshair */}
        {tooltip && (
          <>
            <line
              x1={tooltip.x}
              x2={tooltip.x}
              y1={padTop}
              y2={padTop + chartH}
              stroke="var(--line-strong)"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              strokeDasharray="3,3"
            />
            <circle
              cx={tooltip.x}
              cy={tooltip.y}
              r={4}
              fill={color}
              stroke="var(--surface)"
              strokeWidth={2}
              vectorEffect="non-scaling-stroke"
            />
          </>
        )}
      </svg>

      {/* Tooltip popover */}
      {tooltip && (
        <div
          className="absolute pointer-events-none px-3 py-1.5 rounded-xl border border-line bg-surface shadow-elevated text-xs text-ink"
          style={{
            left: `${(tooltip.x / W) * 100}%`,
            top: tooltip.y - 40,
            transform: "translateX(-50%)",
          }}
        >
          <span className="font-semibold">{tooltip.point.value}</span>{" "}
          <span className="text-ink-tertiary">{tooltip.point.label}</span>
        </div>
      )}
    </div>
  );
}
