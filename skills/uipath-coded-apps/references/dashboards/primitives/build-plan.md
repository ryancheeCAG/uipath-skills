# Plan Generation + Approval Gate

## Plan Format
Render as a numbered markdown list in chat. No code blocks, no JSON.
Each line: `N. <Widget name> (<time frame>) [SDK | Insights] — <chart type>, <aggregation>`

Example output to show the user:
```
Here's what I'll build. Confirm to proceed, or tell me what to change.

1. Agent Success Rate (last 7 days)      [Insights] — area chart, daily % success
2. Active Queue Items by folder          [SDK]      — bar chart, snapshot count
3. P95 Process Execution Time            [Insights] — KPI card, weekly avg ms
4. Pending Action Center Tasks           [SDK]      — KPI card, live count
5. Governance Violations (last 30 days)  [Insights] — line chart, daily count
6. Maestro Flow Runs by status           [SDK]      — donut chart, snapshot
```

## Approval Gate Rules
- ANY positive response → proceed to scaffold
  (yes, looks good, do it, go ahead, 👍, confirmed, ship it)
- Widget edit request → update that line only, re-show ONLY the changed lines, re-ask
- "Remove X" → strike item from list, show updated list, re-ask
- "Add X" → derive route via data-router.md, append item, show updated list, re-ask
- Rejection without edit → ask: "What would you like to change?"
- Never re-show the full plan after partial edits — show diffs only

## Four-Axis Metric Decomposition
For each metric mentioned in the NLP prompt, derive:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95 | p99`
- **Service**: `SDK` or `Insights` (resolve via data-router.md)

## Anti-patterns
- Do NOT start scaffolding before explicit approval
- Do NOT infer approval from silence or a question ("which folder?")
- Do NOT re-derive the entire plan if only one widget changes
- Do NOT show code or file paths in the plan — plain language only
