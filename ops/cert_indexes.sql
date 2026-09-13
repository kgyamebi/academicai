CREATE INDEX IF NOT EXISTS ix_citations_document_id_pk ON citations (document_id, id);
CREATE INDEX IF NOT EXISTS ix_references_document_sort ON "references" (document_id, sort_order);
CREATE INDEX IF NOT EXISTS ix_analytics_events_user_event ON analytics_events (user_id, event_name);
ANALYZE citations;
ANALYZE "references";
ANALYZE analytics_events;
