# Agent Compatibility

## Support tiers

| Agent | Status | Integration |
| --- | --- | --- |
| Codex | First class | portable `.agents/skills` entry, `agents/openai.yaml`, `$build-route-map-video` |
| Claude Code | First class | portable `.claude/skills` entry, `CLAUDE.md`, `/build-route-map-video` |
| Agent Skills compatible tools | Best effort | canonical `skills/build-route-map-video/SKILL.md` |
| Tools reading `AGENTS.md` | Best effort | root workflow pointer and test rules |
| Other vendor-specific agents | Not duplicated | use `AGENTS.md` or add a thin pointer locally |

Codex skills follow OpenAI's [Build skills](https://learn.chatgpt.com/docs/build-skills) guidance. Claude Code supports project skills at `.claude/skills/<name>/SKILL.md` per Anthropic's [skills documentation](https://code.claude.com/docs/en/skills). Both build on the Agent Skills open standard.

For intake decisions, use each product's native structured-choice UI when available. Ask one question per interaction. On agents without a choice UI, fall back to a short numbered list with the recommended option first and a free-form alternative.

## Why not copy everything

Maintaining a Codex Skill, Claude-only Skill, Copilot prompt, Cursor rule, Gemini instruction file, and Aider convention as independent full documents would create behavioral drift. RouteFilm keeps one canonical `SKILL.md` and exposes it through small, cross-platform discovery entry points. These are regular files rather than symbolic links so GitHub archives and Windows checkouts work consistently.

Add a new vendor adapter only when it provides a capability that cannot discover the canonical Skill or `AGENTS.md`, and keep that adapter as a pointer rather than a second workflow.
