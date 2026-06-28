# Legacy n8n Workflows

These workflows are preserved for historical reference only.

They belong to the previous architecture, where n8n concentrated part of the agent logic.

Current architecture:

- n8n acts only as message gateway / courier;
- AI Agents are responsible for reasoning and decision-making;
- API Core is the controlled entry point;
- PostgreSQL is the operational memory and audit layer;
- RPA, when used, only executes structured and auditable commands.

Do not treat these workflows as active production workflows.

Active n8n workflows, if any, must remain minimal and should only receive, route, and deliver messages.
