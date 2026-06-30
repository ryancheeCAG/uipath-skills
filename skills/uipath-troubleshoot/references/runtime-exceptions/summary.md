# Runtime Exceptions Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — scope check, data correlation rules, local log paths, and source code analysis for runtime exception investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Null Reference Exception | Medium | `System.NullReferenceException` in workflow code — uninitialized variable, null activity output, missing data, or unguarded conditional path | [null-reference-exception.md](./playbooks/null-reference-exception.md) |
| Argument Null Exception | Medium | `System.ArgumentNullException` in workflow code — null value passed to activity or method that requires non-null | [argument-null-exception.md](./playbooks/argument-null-exception.md) |
| Expression requires compilation | Medium | `Expression Activity type 'VisualBasicValue`1' / 'CSharpValue`1' requires compilation in order to run` — an expression failed to AOT-compile (invalid/smart quotes, expression-language mismatch, or post-Legacy-migration loose syntax) and modern .NET runtime JIT is disabled | [visualbasicvalue-requires-compilation.md](./playbooks/visualbasicvalue-requires-compilation.md) |
