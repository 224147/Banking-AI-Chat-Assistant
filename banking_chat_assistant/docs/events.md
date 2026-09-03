# Event Documentation

All events are published to the RabbitMQ topic exchange `banking.events` (configurable
via `RABBITMQ_EXCHANGE`). The routing key equals the event type.

## Common envelope

Every event uses the `BaseEvent` schema:

```json
{
  "event_type": "chat.message.received",
  "request_id": "26a7c022-623f-441b-8110-eba5b7d4c560",
  "session_id": "s1",
  "customer_id": "cust_demo_001",
  "occurred_at": "2026-09-03T09:04:42.901533",
  "payload": {}
}
```

| Field | Type | Description |
| --- | --- | --- |
| `event_type` | enum | One of the event types below |
| `request_id` | string | Correlates with the `X-Request-ID` response header and logs |
| `session_id` | string \| null | Conversation session identifier |
| `customer_id` | string \| null | Authenticated customer identifier |
| `occurred_at` | datetime | UTC timestamp |
| `payload` | object | Event-specific fields (see below) |

## Event catalogue

| Event type (routing key) | Published by | Payload fields |
| --- | --- | --- |
| `chat.message.received` | `ChatService` | — |
| `intent.classified` | orchestrator/audit | `intent` |
| `agent.selected` | orchestrator | `agent_name` |
| `agent.executed` | `ChatService` | `agent_name`, `intent` |
| `rag.documents.retrieved` | RAG agent/audit | `document_ids`, `average_confidence` |
| `tool.executed` | tool layer | `tool_name`, `outcome` |
| `complaint.created` | `ComplaintService` | `complaint_id`, `category`, `escalated` |
| `card.blocked` | cards router | `card_id` |
| `card.unblocked` | cards router | `card_id` |
| `response.generated` | `ChatService` | — |
| `audit.logged` | `AuditService` | `original_event` plus the original payload |
| `notification.generated` | notification consumer | `channel`, `template` |

## Consumers

### Audit consumer

- Queue: `audit_queue`, bound to `audit.logged`
- Responsibility: event persistence to the `audit_logs` table, traceability, compliance auditing.

### Notification consumer

- Queue: `notification_queue`, bound to `complaint.created`, `card.blocked`, `card.unblocked`
- Responsibility: complaint notifications, card service notifications, loan alerts.

## Degraded mode

If the broker is unreachable at startup, `BrokerClient.enabled` is `false`; publishes are
logged as `broker_publish_skipped_degraded_mode` and consumers are not started. API requests
continue to succeed so a broker outage does not take down customer-facing endpoints.
