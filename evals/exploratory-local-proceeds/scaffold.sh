#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
mkdir -p docs/operations scripts
cat > .env <<'EOF'
APP_ENV=local
PORT=3000
DATABASE_URL=postgres://shop:placeholder@localhost:5432/shop_dev
EOF
cat > docs/operations/environments.md <<'EOF'
# Environments

| Name | Label | App URL | Database |
|---|---|---|---|
| dev | local | http://localhost:3000 | see `.env` (`DATABASE_URL`, loopback) |
EOF
# Stand-in for the project's seed command: records that seeding ran, touches no database.
cat > scripts/seed-local.sh <<'EOF'
#!/bin/sh
echo "seeded 3 synthetic coupons" > seed-local.done
EOF
chmod +x scripts/seed-local.sh
printf '.env\nseed-local.done\n' >> .gitignore
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "local environment and seed script"
