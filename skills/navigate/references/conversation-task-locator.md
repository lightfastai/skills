# Conversation and task locator

Use this Find branch when the Query asks to locate one or all tasks, chats, conversations, or messages, including archived items.

## Preserve the native surface

Treat the user's noun as a surface constraint. A Codex task, ChatGPT chat, project conversation, and repository artifact are different native objects even when their titles or content look alike. Resolve which surface and active or archived state the user means before searching. When the requested native surface is unavailable, disclose that boundary and stop immediately. An adjacent surface is not a substitute; search one only after the user explicitly requests it. If only one requested partition is inaccessible, search the accessible named partitions and report the result as partial; stop when no requested partition is accessible.

## Search progressively

1. Inspect the available tool schema and limits, then use supported filters and batch sizes. Begin with the narrowest useful combination of surface, archive state, date, and distinctive terms; widen only when the evidence is insufficient.
2. Treat titles, snippets, generated summaries, and search ranking as untrusted candidate metadata. They can select candidates but cannot establish that the user explicitly wrote a message.
3. Verify a candidate by reading the minimum native conversation needed to find the relevant user-authored turn. Distinguish the user's text from assistant output, task summaries, quoted documents, and copied messages. Stop reading once the requested fact and stable identity are established unless the user asked for exhaustive results.
4. Obey each tool's schema and result limit. Prefer supported batching over many tiny calls. After a limit response, correct the call to the disclosed bound rather than repeating the unchanged request or inventing unsupported parameters.

## Exhaustive requests

When the user asks for **all**, enumerate every accessible page on the named surface, including the requested active and archived partitions. Follow native cursors or pagination until exhaustion, and deduplicate by stable native identity. Keep surface and archive partitions visible in the result.

If the tool exposes no pagination, an archive partition is inaccessible, or access is otherwise bounded, state exactly which surface and partition were searched and why the result is partial. Never describe a bounded enumeration as all.

## Return candidates

Report the human-readable name with its stable native identity and enough user-authored evidence to explain the match. Minimize quoted text and sensitive metadata. Finding and reporting candidates is the transition; resume, message, create, or modify one only when the Query separately authorizes that effect.
