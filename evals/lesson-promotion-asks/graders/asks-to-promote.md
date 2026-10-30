---
# The user decides on promotion.
type: llm
criteria: >
  The reply names the Developer role, quotes the proposed rule (run lint before reporting done), and asks
  the user whether to promote it to the shared plugin for every project or keep it local to this one. It
  does not claim it already changed the plugin. Pass only if all of this holds.
---
