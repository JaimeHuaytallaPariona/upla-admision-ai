#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Script para publicar este repo en GitHub la primera vez.
# Uso:   bash scripts/setup-github.sh <tu-usuario-github> [<nombre-repo>]
# Ej:    bash scripts/setup-github.sh jhuaytalla upla-admision-ai
# ─────────────────────────────────────────────────────────────
set -euo pipefail

USER="${1:-}"
REPO="${2:-upla-admision-ai}"

if [ -z "$USER" ]; then
  echo "Falta el usuario de GitHub."
  echo "Uso: bash scripts/setup-github.sh <tu-usuario-github> [<nombre-repo>]"
  exit 1
fi

echo "─── Publicando $REPO bajo @$USER ───"

# Verifica gh autenticado
if ! command -v gh &> /dev/null; then
  echo "✗ gh CLI no encontrado. Instálalo: https://cli.github.com/"
  exit 1
fi

if ! gh auth status &> /dev/null; then
  echo "✗ gh no autenticado. Ejecuta: gh auth login"
  exit 1
fi

# Crear repo si no existe
if gh repo view "$USER/$REPO" &> /dev/null; then
  echo "✓ Repo $USER/$REPO ya existe"
else
  echo "→ Creando repo $USER/$REPO en GitHub…"
  gh repo create "$USER/$REPO" --public \
    --description "Sistema multiagente para la gestión dinámica de admisión UPLA" \
    --homepage "https://admision.upla.edu.pe" \
    --disable-wiki
fi

# Agregar remote si falta
if ! git remote get-url origin &> /dev/null; then
  git remote add origin "git@github.com:$USER/$REPO.git"
fi

# Push inicial
git branch -M main
git push -u origin main

# Tag de versión
git tag -a v0.1.0 -m "v0.1.0 — Prototipo funcional end-to-end"
git push origin v0.1.0

# Proteger main (soft rule)
gh api "repos/$USER/$REPO/branches/main/protection" \
  --method PUT \
  --field "required_status_checks[strict]=true" \
  --field "required_status_checks[contexts][]=Backend (lint + test)" \
  --field "required_status_checks[contexts][]=Frontend (lint + build)" \
  --field "enforce_admins=false" \
  --field "required_pull_request_reviews[required_approving_review_count]=1" \
  --field "restrictions=null" 2>/dev/null || echo "  (protección de main omitida — requiere plan de pago en repos privados)"

echo ""
echo "✓ Listo. Repo publicado en: https://github.com/$USER/$REPO"
echo "  Primer tag: v0.1.0"
echo ""
echo "Próximos pasos sugeridos:"
echo "  1. Agregar secrets en Settings → Secrets:"
echo "     - ANTHROPIC_API_KEY (para el entorno de staging/CI)"
echo "  2. Habilitar Actions en Settings → Actions"
echo "  3. Invitar colaboradores (TI UPLA, Oficina de Admisión)"
