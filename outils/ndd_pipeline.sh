#!/usr/bin/env bash
# Pré-remplit la note de dimensionnement MaPrime Facile d'un dossier PAC et la dépose
# dans le dossier Drive du client, sans qu'aucun octet ne passe par une conversation.
#
# Usage :
#   KARE_SECRET=... KARE_WEBHOOK_REPRISE=https://hook.eu2.make.com/... KARE_WEBHOOK_RECEPTION=https://hook.eu2.make.com/... \
#   bash ndd_pipeline.sh <id Drive de la fiche .json> "<NOM Prénom du client tel que dans Axonaut>" ["<nom du fichier de sortie>"]
#
# Étapes : télécharge le gabarit et la fiche par le scénario Make « reprise au bureau »
# (action lire_fichier, base64), remplit les cases variables (ndd_remplir.py, gabarit intact),
# puis pousse le .xlsx par le scénario « réception des fiches » (route photo) dans le dossier
# du client, retrouvé par son nom. Le nom du fichier porte « brouillon à vérifier » : Rémi relit.
set -euo pipefail
FICHE_ID="${1:?id Drive de la fiche json}"
CLIENT="${2:?nom du client}"
SORTIE="${3:-NDD - ${CLIENT} - brouillon a verifier.xlsx}"
GABARIT_ID="${KARE_NDD_GABARIT_ID:-1vEtj1c8b4N5KTgLkb4-vrW-IHMWf0N8u}"   # NDD MPF 171-172.xlsx, Drive KA-RÉ
: "${KARE_SECRET:?KARE_SECRET manquant}" "${KARE_WEBHOOK_REPRISE:?}" "${KARE_WEBHOOK_RECEPTION:?}"
ICI="$(cd "$(dirname "$0")" && pwd)"
W="$(mktemp -d)"

lire(){  # <id Drive> <fichier de sortie>  — télécharge par Make, décode le base64
  python3 -c "import json,sys,urllib.parse; print('payload='+urllib.parse.quote(json.dumps({'secret':sys.argv[1],'action':'lire_fichier','file_id':sys.argv[2]})))" "$KARE_SECRET" "$1" > "$W/corps.txt"
  curl -sS --max-time 120 -o "$W/rep.b64" -X POST -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" --data-binary @"$W/corps.txt" "$KARE_WEBHOOK_REPRISE"
  if [ "$(head -c 8 "$W/rep.b64")" = "Accepted" ]; then echo "Make n'a pas renvoyé le fichier $1 (id faux ou clé refusée)" >&2; exit 2; fi
  python3 -c "import base64,sys; open(sys.argv[2],'wb').write(base64.b64decode(open(sys.argv[1],'rb').read().strip()))" "$W/rep.b64" "$2"
}

lire "$GABARIT_ID" "$W/gabarit.xlsx"
lire "$FICHE_ID"   "$W/fiche.json"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); n=d.get('note_de_dimensionnement'); sys.exit(0 if n else 3)" "$W/fiche.json" \
  || { echo "Cette fiche n'a pas de note de dimensionnement (pas de lot PAC ou pas d'aides)" >&2; exit 3; }
python3 "$ICI/ndd_remplir.py" "$W/gabarit.xlsx" "$W/fiche.json" "$W/ndd.xlsx"

python3 - "$W/ndd.xlsx" "$KARE_SECRET" "$CLIENT" "$SORTIE" > "$W/envoi.txt" <<'EOF'
import base64, json, sys, urllib.parse, datetime
xlsx, secret, client, sortie = sys.argv[1:5]
p = {"secret": secret, "type": "photo", "statut": "finale", "client": client,
     "date": datetime.date.today().isoformat(), "source": "Note de dimensionnement", "etiquette": "NDD",
     "nom_fichier": sortie, "image_base64": base64.b64encode(open(xlsx, "rb").read()).decode()}
print("payload=" + urllib.parse.quote(json.dumps(p, ensure_ascii=False)))
EOF
REP="$(curl -sS --max-time 120 -X POST -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" --data-binary @"$W/envoi.txt" "$KARE_WEBHOOK_RECEPTION")"
echo "Réponse Make : $REP"
echo "Déposé : « $SORTIE » dans le dossier Drive de « $CLIENT » (ou dans CLIENTS/2026 si le dossier n'a pas été trouvé)."
rm -rf "$W"
