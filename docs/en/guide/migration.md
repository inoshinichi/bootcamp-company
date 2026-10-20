# Updating from a previous version

If you already installed an earlier version (1.0.x / 1.1.x), run these two lines in your terminal (PowerShell on Windows):

```bash
claude plugin marketplace update bootcamp-company
claude plugin update company@bootcamp-company
```

Then quit Claude Code, start it again in your company folder, and type `/company`.

Your existing `.company/` is kept. If it was created by an earlier version, the secretary adds the missing files (`secretary/work-log.md`, `.company/flow-map.md`, each department's `manuals/INDEX.md`) without overwriting anything, and appends the "absolute rules" section to the CLAUDE.md files.

Since 1.1.0, Google and Microsoft 365 are connected with Claude's official connectors. If you connected them the old way (Google Cloud / Azure), the secretary will tell you once how to reconnect.
