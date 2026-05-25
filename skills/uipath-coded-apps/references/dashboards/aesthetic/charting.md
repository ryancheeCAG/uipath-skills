# Charting Guide

How to pick chart types, configure colors, and avoid common mistakes.

---

## Chart Type Selection

| User's metric | Use this | Why |
|---|---|---|
| Single number at a point in time | `kpi-card` | No trend needed |
| Single number + recent trend | `kpi-with-sparkline` | Compact trend context |
| One metric over time (count, sum) | `area-chart` | Shows volume and trend |
| One metric over time (rate, %) | `line-chart` | Rates don't have fill area |
| Comparing categories (bars) | `bar-chart` | Items to compare |
| Ranked list with a score | `ranked-table` | 5+ items, sortable |
| Part-of-whole proportions (≤5 categories) | `donut-chart` | Parts sum to 100% |
| Part-of-whole proportions (5+ categories) | `progress-bar-list` | Donut with 5+ slices is unreadable |
| Two metrics on the same time axis | `multi-line-chart` | Comparison over time |
| Raw records, drill-down detail | `data-table` | Operational view |

---

## Color Rules

### Always use CSS variable tokens

```tsx
// Correct
fill="hsl(var(--chart-1))"
stroke="hsl(var(--chart-2))"

// Wrong — hardcoded hex
fill="#FA4616"
stroke="#0066CC"
```

### Chart color series meaning

| Token | Color | Semantic use |
|---|---|---|
| `--chart-1` | UiPath orange | Primary data series, main metric |
| `--chart-2` | UiPath blue | Secondary series (e.g., P95 alongside P50) |
| `--chart-3` | Success green | "Up is good" deltas, completion rates |
| `--chart-4` | Warning amber | Approaching threshold, mid-risk |
| `--chart-5` | Error red | Errors, failures, "down is good" |

For multi-line charts (P50/P95):
- P50 → `--chart-1` (orange, primary)
- P95 → `--chart-2` (blue, secondary)

---

## Area vs Line

- **Area chart** (`area-chart`) → for volume metrics (count, invocations, AGU consumed)
  - Always use `fillOpacity={0.2}` to keep the area subtle
  - Fill and stroke use `--chart-1`

- **Line chart** (`line-chart`) → for rate/percentage metrics (error rate %, P95 latency)
  - No fill area — rates don't accumulate visually
  - `dot={false}` for smooth trend reading
  - `strokeWidth={2}` minimum

---

## DeltaBadge Direction Guide

The `direction` prop means: which direction is good for this metric?

| Metric | Direction when value goes UP |
|---|---|
| Success rate, health score | `up-good` |
| Error count, failure rate | `up-bad` |
| Latency (lower is faster) | `up-bad` |
| AGU consumed (cost) | `up-bad` |
| Invocations (activity proxy) | `up-good` |
| Agent count (fleet growing) | `up-good` |
| Incidents | `up-bad` |
| Unknown / neutral | `neutral` |

Examples:
```tsx
// Success rate went up → good
<DeltaBadge direction="up-good" text="+3.2% vs last week" />

// Error rate went up → bad
<DeltaBadge direction="up-bad" text="+12 errors vs yesterday" />

// Unknown trend
<DeltaBadge direction="neutral" text="12.4s avg" />
```

---

## Recharts Configuration Standards

```tsx
// XAxis — always small font
<XAxis dataKey="date" tick={{ fontSize: 11 }} />

// YAxis — always small font, no label
<YAxis tick={{ fontSize: 11 }} />

// Tooltip — default, no custom content unless specific need
<Tooltip />

// ResponsiveContainer — standard heights
// KPI sparkline: height={48}
// Chart row widget: height={180}
// Full-width chart: height={240}
```

---

## Anti-patterns

- Donut chart with >5 slices → use `progress-bar-list` instead
- Line chart with <4 data points → use `bar-chart` instead (clearer)
- Stacked bar unless values are genuinely parts-of-whole
- Sparkline without a primary number above it
- Hardcoded hex colors anywhere in chart config
- `fillOpacity={1}` on area charts — too heavy
- `dot={true}` on line charts with >30 data points — too noisy
- XAxis with long date strings — format with `tickFormatter`

---

## Axis Date Formatting

When x-axis is a date/time:

```tsx
// For hourly data (24h):
<XAxis
  dataKey="timeSlice"
  tick={{ fontSize: 11 }}
  tickFormatter={(v: string) => new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
/>

// For daily data (7d, 30d):
<XAxis
  dataKey="date"
  tick={{ fontSize: 11 }}
  tickFormatter={(v: string) => new Date(v).toLocaleDateString([], { month: 'short', day: 'numeric' })}
/>
```
