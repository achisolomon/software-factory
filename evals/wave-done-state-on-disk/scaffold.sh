#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Every lane of the workflow has now reported back.
cat >> .factory-run/wf_demo-001/journal.jsonl <<'EOF'
{"type":"result","key":"v2:k21","agentId":"a21c0up0n5dev0001","result":{"status":"done","commit":"1a2b3c4","issue":"https://github.com/acme/shop/issues/21","summary":"Coupon redeem route built; tests pass"}}
{"type":"result","key":"v2:k23","agentId":"a23ana1yt1c50003","result":{"status":"done","commit":"5d6e7f8","issue":"https://github.com/acme/shop/issues/23","summary":"Daily analytics route built; tests pass"}}
{"type":"result","key":"v2:k22r","agentId":"a22rev1ew5ec0004","result":{"status":"done","verdict":"pass","issue":"https://github.com/acme/shop/issues/22","summary":"Security review passed, no findings"}}
{"type":"finished"}
EOF
