# Legacy n8n Agent Documentation

These documents are preserved for historical reference only.

They describe the previous architecture, where n8n workflows concentrated part of the agent logic.

Current architecture:

- WhatsApp is the operational field communication channel;
- Telegram is the executive channel for Eng. Renato;
- API Core is the controlled entry point;
- AI Agents are the reasoning layer;
- PostgreSQL is the operational memory and audit layer;
- execution must occur through structured and auditable commands.

Do not treat these documents as active implementation specifications.

New active agent documentation must be created under `docs/agents/`.
