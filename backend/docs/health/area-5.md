# Area 5 — Communication
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (`core_apps/chat/`, `core_apps/notifications/`, `core_apps/support/`)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S5-N1 | low | maintainability | Notification copy translation helper has 312 lines with extensive conditional branching | `core_apps/features/services/planning_notifications_parts/event_copy.py:7` | Refactor into structured translation mapping dictionary | verified |
| S5-N2 | low | performance | Support ticket detail serializer loads full message thread without default cursor pagination | `core_apps/support/services/ticket_service_parts/get_ticket_detail.py:42` | Add cursor pagination for long support ticket conversations (>100 messages) | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| WebSocket authentication & connection closure | pass | `core_apps/chat/consumers.py:29` (rejects unauthenticated sockets with code 4401) | None |
| WebSocket session revocation propagation | pass | `core_apps/chat/consumers.py:59` (`session_revoked` handler closes socket immediately) | None |
| Conversation & workspace membership | pass | `core_apps/chat/group_consumer.py:44` (verifies membership before joining channel groups) | None |
| Support ticket & staff role isolation | pass | `core_apps/support/views/attachments.py:36` (restricts attachment access to ticket creator or authorized staff) | None |
| Private support media storage | pass | `core_apps/support/views/attachments.py:45` (private storage backend, 404 on unauthorized) | None |
| Chat moderation visibility | pass | `core_apps/chat/views.py:80` (moderation status masks flagged messages) | None |
| Push notification token scoping & device retries | pass | `core_apps/notifications/services/` (validates device tokens, workspace scoping) | None |
| Unread badge count performance | pass | `core_apps/profiles/services/profile_service_parts/profile_unread.py:15` (scoped unread query indexed by recipient) | None |

