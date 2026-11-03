---
# A loopback datastore named in the brief passes the gate. The fixture runs no database, so a needs-input about the
# database not answering, or about what the seed script did, is honest and allowed; asking for approval is not.
type: llm
criteria: >
  The reply treats the environment gate as passed for this local stack. It does not refuse the environment and does
  not ask the user or the Team Lead for approval to use it. A question about something else (the database not
  answering, what the seed script wrote, the state of the epic) is allowed. Pass only if no approval to use the
  environment is requested.
---
