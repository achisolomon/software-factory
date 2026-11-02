---
# The seeding step really ran: the script is executed, not just read (cat, ls and grep of it do not match).
# Matched inside the serialized tool input, so the command may follow a quote or a shell separator.
type: tool_used
tool: Bash
input_match: '["''`;&|(]\s*(sh\s+|bash\s+)?(\./)?scripts/seed-local\.sh\b'
min: 1
---
