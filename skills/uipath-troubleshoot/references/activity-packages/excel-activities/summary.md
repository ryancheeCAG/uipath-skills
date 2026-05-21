# Excel Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Excel Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Read Range — File In Use By Another Process | Medium | Workbook held open by another process (user Excel UI, orphan `EXCEL.EXE`, network-share lock on a different host) so the activity cannot acquire the file (`System.IO.IOException: The process cannot access the file '<path>' because it is being used by another process.`) | [read-range-file-locked.md](./playbooks/read-range-file-locked.md) |
