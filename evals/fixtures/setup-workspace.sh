#!/bin/sh
# Scaffold for multi-repo cases: the session starts in a workspace folder, and the factory project is a repo two
# levels down (like pushapp/Projects/pushapp project/), next to a second repo without the factory.
# Usage from a case's scaffold.sh: . "$(dirname "$0")/../fixtures/setup-workspace.sh"
set -e
FIXTURES="$(cd "$(dirname "$0")/../fixtures" && pwd)"
WORKSPACE="$PWD"
mkdir -p "Projects/shop project" "Projects/infra" handovers
cd "Projects/shop project"
. "$FIXTURES/setup.sh"
cd "$WORKSPACE/Projects/infra"
git init -q -b main
echo "# Infra (Terraform)" > README.md
cd "$WORKSPACE"
