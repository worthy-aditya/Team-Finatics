# Team-Finatics
This repository is made for the codequest project

## Week 3 CLI Workflows

Read Security events on Windows (administrator access may be required):

```bash
sentinelai logs --hours 24
sentinelai logs --event-ids 4625 --json
sentinelai logs --sample --analyze --json
```

Scans can request operator approval before Nmap starts. Use `--yes` only for
explicitly approved automation:

```bash
sentinelai scan --target 127.0.0.1 --confirm
sentinelai scan --target 127.0.0.1 --confirm --yes
```
