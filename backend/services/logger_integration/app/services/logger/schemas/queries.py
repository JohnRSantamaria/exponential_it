INSERT_SQL = """
INSERT INTO invoice_events (
  event_id, ts, invoice_id, step, status, service, request_id, "user",
  "date", file_name, partner_cif, partner_name, amount_total, amount_tax,
  time_process, error, recommendations, meta
) VALUES (
  $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18
)
ON CONFLICT (event_id) DO NOTHING;
"""

SELECT_TIMELINE_SQL = """
SELECT
  ts, step, status, service, request_id, "user", "date",
  file_name, partner_cif, partner_name, amount_total, amount_tax,
  time_process, error, recommendations, meta
FROM invoice_events
WHERE invoice_id = $1
ORDER BY ts ASC;
"""

INIT_SQL = """
CREATE TABLE IF NOT EXISTS invoice_events (
  event_id        uuid PRIMARY KEY,
  ts              timestamptz NOT NULL DEFAULT now(),
  invoice_id      varchar(128) NOT NULL,
  step            varchar(64)  NOT NULL,
  status          varchar(16)  NOT NULL CHECK (status IN ('completed','failed')),
  service         varchar(64)  NOT NULL,
  request_id      varchar(128) NOT NULL,
  "user"          varchar(128),
  "date"          date,
  file_name       varchar(256),
  partner_cif     varchar(64),
  partner_name    varchar(256),
  amount_total    numeric(18,2),
  amount_tax      numeric(18,2),
  time_process    integer,
  error           text,
  recommendations text,
  meta            jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_ie_invoice_ts ON invoice_events(invoice_id, ts);
CREATE INDEX IF NOT EXISTS idx_ie_status     ON invoice_events(status);
CREATE INDEX IF NOT EXISTS idx_ie_step       ON invoice_events(step);

CREATE OR REPLACE FUNCTION notif_invoice_event() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('invoice_events', row_to_json(NEW)::text);
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_notif_invoice_event ON invoice_events;
CREATE TRIGGER trg_notif_invoice_event
AFTER INSERT ON invoice_events
FOR EACH ROW EXECUTE FUNCTION notif_invoice_event();
"""
