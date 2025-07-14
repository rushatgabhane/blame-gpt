-- Rename cost_usd_cents to cost_usd_thousandths for clarity
-- The column stores cost in 0.001 USD units (1 = 0.001 USD)

ALTER TABLE llm_calls
RENAME COLUMN cost_usd_cents TO cost_usd_thousandths;