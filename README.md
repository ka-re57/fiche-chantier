# Fiche chantier KA-RÉ — v2.7

Appli tablette de relevé de RDV devis. Fonctionne hors connexion, s'installe comme une appli.
Même socle que la fiche terrain d'entretien, mais dépôt et webhooks **séparés** : on ne touche à rien de ce qui tourne.

---

## 1 · Mettre l'appli en ligne (10 minutes)

1. Sur GitHub, créer un dépôt **public** nommé `fiche-chantier` sur le compte `ka-re57`.
2. `Add file → Upload files`, déposer les 5 fichiers : `index.html`, `sw.js`, `manifest.webmanifest`,
   `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`. Commit.
3. `Settings → Pages` : Source = `Deploy from a branch`, Branch = `main`, dossier `/ (root)`. Save.
4. Au bout d'une minute, l'appli est sur **https://ka-re57.github.io/fiche-chantier/**
5. Sur la tablette : ouvrir l'adresse, menu du navigateur → **Ajouter à l'écran d'accueil**.

L'icône reprend le vrai logo KA-RÉ sur fond blanc, en carré. Le logo est aussi dans la barre de
l'appli et en tête de l'écran client — il est intégré au fichier, il n'y a rien à faire.

---

## 2 · Les trois scénarios Make à créer

**Nouveaux scénarios. Ne modifier aucun scénario existant.**
La clé partagée à mettre partout : invente-la, mets-la dans les réglages de l'appli, et fais-la
vérifier en premier filtre dans chaque scénario.

### A · Liste des chantiers → tablette

| Module | Réglage |
|---|---|
| 1. Webhooks › Custom webhook | Nom : `Fiche chantier — liste` |
| 2. Filtre | `secret` = ta clé |
| 3. Axonaut › liste des opportunités | Comme le scénario 9598035 déjà en place |
| 4. Filtre | `pipe_step_name` ∈ `contact_recu`, `a_chiffrer` |
| 5. Tools › Array aggregator | Agrège les opportunités |
| 6. Webhooks › Webhook response | Status **200**, Body = `{"chantiers": {{tableau}}}` |

**Le point qui fait tout échouer si on l'oublie** : dans le module 6, ouvrir
*Show advanced settings → Custom headers* et ajouter :

```
Access-Control-Allow-Origin : *
```

Sans cet en-tête, le navigateur de la tablette refuse de lire la réponse et la liste reste vide.
En secours, l'appli a un bouton **Coller la liste à la main** dans les réglages : le résultat brut
de l'outil « lister opportunités » y est accepté tel quel.

L'appli n'a besoin que de : `id`, `name`, `pipe_step_name`, `company.id`, `company.name`,
`comments`, `creation_date`. Elle sait lire les demandes du formulaire de contact directement
dans `comments` (nom, e-mail, téléphone, adresse, ville, type de logement, propriétaire/locataire,
description, dossier Drive).

### B · Réception des fiches

| Module | Réglage |
|---|---|
| 1. Webhooks › Custom webhook | Nom : `Fiche chantier — réception` |
| 2. JSON › Parse JSON | Sur le champ `payload` |
| 3. Filtre | `secret` = ta clé **et** `test` n'existe pas |
| 4. Routeur | Voie **photo** si `type` = `photo`, voie **fiche** sinon |

**Voie fiche.** Le champ `statut` vaut `brouillon` ou `finale` : sur un brouillon, on classe et on notifie,
mais on ne crée ni page de chiffrage ni opportunité — c'est une fiche que Rémi va reprendre au bureau.

1. Drive → chercher/créer `CLIENTS / 2026 / NOM Prénom Ville Objet`
   *(mettre un Array aggregator après la recherche, sinon la branche « créer » ne se déclenche jamais — même piège que sur le scénario des relevés terrain)*
2. Drive → déposer `resume` en `.txt` : `fiche_<client>_<date>.txt`
3. Notion → créer une page **Brouillon de devis** avec `resume`, `points_a_confirmer`,
   `postes_obligatoires` et `prompt_select_clim`
   *(utiliser les modules natifs Create a Database Item, pas un appel API à la main : ils échappent les guillemets tout seuls)*
4. Axonaut → chercher la société par `societe.id`, créer contact et adresse de chantier si besoin
5. **Ne pas créer de devis.** L'opportunité existe déjà ; au besoin la faire passer d'étape.
6. Mail à Rémi : client, lots, points à confirmer, lien du dossier Drive

**Voie photo :** un POST par photo, avec `image_base64`, `nom_fichier`, `source`, `etiquette`.
Drive → Upload a file, en convertissant le base64 (`toBinary(base64(...))`), dans le dossier du chantier.

### C · Mail « liste des pièces » au client

Sur la voie fiche, ajouter une branche conditionnée par `aides.envoyer_liste_pieces = true`.
Elle envoie au client (`client.email`) le mail dont le texte est en fin de ce document.

---

## 3 · Réglages de l'appli

Engrenage en haut à droite :

- **Webhook — envoi des fiches** : l'adresse du scénario B
- **Webhook — liste des chantiers** : l'adresse du scénario A
- **Webhook — photos** : laisser vide pour tout envoyer sur B (le routeur trie)
- **Clé partagée** : la même que dans les filtres Make
- **Code de retour du mode client** : 4 chiffres, `1234` par défaut — à changer
- **Tester l'envoi** avant le premier chantier réel

---

## 4 · Comment on s'en sert

1. Dans le camion : ouvrir l'appli, choisir le chantier dans la liste. L'heure d'arrivée se note toute seule.
   Lancer Plaud, dire la phrase d'ouverture, entrer.
2. Cocher les lots. Chaque lot ajoute son onglet en haut.
3. Sur chaque question : **✓ dit** quand c'est dans l'enregistrement Plaud, **? à voir** quand ce n'est pas tranché,
   **— non** quand ça ne concerne pas le chantier. Le champ à côté sert aux cotes, diamètres, marques —
   tout ce qui doit être exact. Le bouton **✓ Tout marquer « dit »** en haut du lot va vite quand
   la conversation a tout couvert.

   Les questions s'adaptent : en clim, le choix gainable / split / les deux / indécis en tête du lot
   masque ou fait apparaître le reste. Un lot ajouté par erreur se supprime en bas de page,
   par deux appuis sur le bouton rouge.
4. Onglet **Maison** : forme, mitoyenneté, niveaux, isolation — renseigné une fois, appliqué partout.
5. Onglet **Pièces** : longueur et largeur suffisent, la surface et les quatre murs se calculent tout seuls.
   La surface pleine de chaque mur se déduit de la hauteur sous plafond moins le vitrage saisi.
   Plusieurs émetteurs par pièce, et un bouton **⇊ Appliquer à toutes les pièces** quand ils sont identiques :
   le volume d'eau du circuit et le nombre de bidons d'inhibiteur se calculent à partir de là.
6. **Client** : lui passer la tablette pour vérifier ses coordonnées, et pour les deux questions
   d'aides s'il en veut. Retour par le code.
7. En repartant : onglet **Notes**, deux champs libres, l'heure de départ.
8. **Vérifier et envoyer** : l'appli liste ce qui manque, puis deux boutons —
   **Garder en brouillon** (tu finis au bureau, la fiche reste dans « Mes fiches ») ou
   **Fiche terminée** (elle part au chiffrage). Sans réseau, tout est gardé et part quand le signal revient.

---

## 4 quater · Les lots

Dix lots écrits, chacun avec ses questions et ses pièges : chaudière gaz, PAC air/eau et hybride,
climatisation, chaudière fioul, chauffe-eau thermodynamique, ventilation, traitement d'eau,
électricité ponctuelle, salle de bain, et un lot générique pour le reste.

Les cinq derniers arrivés valent d'être connus pour ce qu'ils évitent d'oublier :

**Fioul** — le sort de la cuve est une question à part entière, avec le volume et le fioul restant :
neutralisée sur place ou dégazée et enlevée, ce n'est pas le même prix, et l'accès pour la sortir
n'est demandé que si tu choisis de l'enlever. L'appli rappelle aussi qu'un remplacement fioul par
fioul n'ouvre pas droit à la prime, contrairement à une sortie du fioul.

**Chauffe-eau thermodynamique** — le volume du local (20 m³ minimum sur air ambiant), la hauteur sous
plafond, et surtout la largeur du passage pour amener le ballon. C'est ce qui bloque le jour de la
pose, et personne n'y pense au rendez-vous.

**Ventilation** — le rejet extérieur est la question qui coûte : une sortie de toiture à créer, ce
n'est pas une grille en façade. Les entrées d'air aux menuiseries sont demandées, et disparaissent en
double flux.

**Traitement d'eau** — la dureté relevée, et l'évacuation à moins de deux mètres : sans elle, la
régénération est impossible et la pose ne se fait pas.

**Électricité** — le différentiel 30 mA, la mise à la terre, et l'attestation Consuel.

## 4 quinquies · Les photos qu'on regrette

L'écran de fin liste les photos qui manquent, par lot : la plaque signalétique et la cuve sur un
fioul, l'emplacement du groupe et le tableau sur une PAC, le caisson et la sortie de toiture sur une
VMC. Ce sont celles qu'on cherche au bureau et qu'on n'a pas.

## 5 · Ce que l'appli sait déjà

- Chaudière gaz à condensation déposée → **pas de Coup de pouce CEE**, alerte immédiate à l'écran
- Lot gaz coché → rappel que **toute l'opération** bascule à 20 % (travaux accessoires)
- Clim + aménagement de combles → rappel du seuil des **10 % de surface de plancher**
- Une pièce au-delà de **3,5 kW de froid** → le multisplit échouera, prévoir 2 UI ou du gainable
- Les postes qu'on oublie : certificat gaz, disconnecteur, traitement d'eau, dépose, goulotte,
  CF00574, colonne de chute, rejet de VMC — sortis automatiquement selon les lots cochés,
  sur l'écran de fin et dans le compte rendu. Aucun prix n'apparaît pendant le relevé.

**Le coefficient G reproduit celui de Projipack.** Le modèle a été reconstitué à partir de onze
relevés faits dans le logiciel : une courbe par année de construction, un gain par paroi rénovée
proportionnel à l'écart entre cette courbe et 0,69, et une synergie quand plusieurs parois sont
rénovées. Il retombe sur les onze mesures à ±0,01, et sur un douzième point qui n'a servi à aucun
calage il donne 0,98 contre 0,99 affiché par Projipack. L'année de construction est donc devenue
indispensable : sans elle, aucune puissance ne s'affiche.

Projipack ne tient pas compte de la mitoyenneté : sur un logement mitoyen, l'appli le signale mais
ne corrige pas, pour que les deux chiffres restent comparables. Le vrai G se saisit toujours à la
main dans l'onglet Maison une fois le logiciel passé.

Le **prompt Select Clim** n'apparaît que sur un chantier clim, le **prompt Projipack** que sur un
chantier PAC. Celui de Projipack est maintenant figé sur le parcours réel de l'outil : ordre de
saisie écran par écran, les trois listes d'isolation pré-remplies au pire cas, la température de
confort qui repasse à 19 °C dès qu'on change de tuile, la température de départ affichée en gris
tant qu'elle n'est pas validée, la machine sélectionnée d'office qui n'est pas la mieux
dimensionnée, la fiche produit à recopier avant de quitter l'écran des résultats, et le point
d'arrêt avant tout bouton qui engage.

## 3 bis · L'écran ne bouge plus sous les doigts

L'appli reconstruit son écran à chaque appui — c'est ce qui lui permet de faire apparaître et
disparaître les questions selon ce que tu réponds. L'effet de bord, c'est que tout ce qui était
déplié se refermait et que la page remontait : tu perdais ta place à chaque choix.

Corrigé. Les blocs dépliés restent dépliés, les détails d'une pièce aussi, et la position dans la
page est reprise à l'identique après chaque appui — mesuré à zéro pixel d'écart. Seul un changement
d'onglet ramène en haut, ce qui est le comportement attendu.

## 4 · Aucun champ n'est obligatoire

Rien dans cette appli ne refuse un envoi. Pas un champ requis, pas un lot imposé, pas même le nom du
client — une fiche vide part si tu décides qu'elle doit partir, et elle arrive sous « sans nom ».

L'écran de fin **signale**, il ne barre pas la route : ce qui manque est listé pour que tu décides en
connaissance de cause, et les deux boutons d'envoi restent actifs quoi qu'il arrive. Même sans adresse
d'envoi renseignée, la fiche est gardée en file d'attente et partira dès que le réglage sera fait —
plutôt que d'être refusée.

C'est une position assumée : sur un chantier, celui qui sait ce qui compte, c'est celui qui est
devant le client. Une appli qui bloque, c'est une appli qu'on contourne.

## 4 bis · Ce que l'appli fait pour toi sans qu'on le lui demande

**L'écran reste allumé** pendant tout le relevé. Plus de tablette qui s'éteint pendant qu'on mesure.
Réglable dans l'engrenage si tu préfères la veille normale.

**Le bouton retour d'Android ne quitte plus l'appli.** Il ferme d'abord ce qui est ouvert : un
dialogue, puis le croquis, puis l'écran en cours. En mode client il ne fait rien — le code reste la
seule sortie. Ce n'est qu'à l'accueil qu'il quitte.

**La mémoire est visible.** Dans l'engrenage, une jauge dit combien de place prennent les fiches sur
les 5 Mo disponibles, et quelles fiches pèsent le plus. Au-delà de 80 % elle te dit d'envoyer et de
purger avant de repartir en chantier. C'est la panne qui arrive toujours chez un client, jamais au
bureau.

**Rien ne se perd sur une erreur.** Si un bout de l'appli plante, un message le dit, le relevé reste
enregistré, et l'incident part dans un journal technique consultable dans l'engrenage — à me copier
tel quel quand quelque chose cloche.

**L'accueil alerte.** Envois en attente avec un bouton pour relancer, et fiches jamais envoyées
depuis plus de deux jours, nommées, avec leur âge. Un relevé qui ne quitte pas la tablette n'existe
nulle part ailleurs.

**L'écart de surface est signalé.** Si la somme des pièces relevées s'écarte de plus de 20 % de la
surface habitable annoncée, l'écran de fin le dit et précise le sens : pièces manquantes, ou cotes à
revoir. C'est l'erreur qui fausse tout le dimensionnement.

**L'échéance PAC est décomptée.** Sur un chantier PAC, l'écran de fin rappelle le nouvel agrément
ADEME du 1er septembre 2026 pour la prime CEE bonifiée, avec le nombre de jours restants. Ce qui
compte est la **date de signature du devis** : un devis signé avant le 31 août échappe à
l'obligation. Après, il faut un modèle de la liste `bonus-pac.ademe.fr` et son numéro d'agrément sur
la facture et sur l'attestation sur l'honneur.

## 4 ter · Reprendre au bureau, et chiffrer

**Le brief de chiffrage**, en un bouton sur l'écran de fin. Un seul texte qui contient tout : le
relevé complet, le métré, la note de dimensionnement, les postes à ne pas oublier, les points à
confirmer, les prompts Select Clim ou Projipack — et en tête les consignes de chiffrage KA-RÉ
(checklist Notion d'abord, devis en forfaits plus décompte interne, TVA dans le titre de section,
prime en ligne négative, rien dans Axonaut avant validation). À coller directement dans une
conversation.

**La fiche se transporte.** « ⤓ Enregistrer la fiche » produit un fichier, « ⧉ Copier le code » le
met dans le presse-papier. À l'accueil de l'autre appareil, « ⤒ Reprendre » rouvre le relevé là où
il s'est arrêté, croquis, métré et photos compris. Si la fiche existe des deux côtés, la plus
récente gagne et l'appli refuse d'écraser une version plus neuve.

**Les pièces courantes en un appui.** Dans l'onglet Pièces, un bouton propose séjour, cuisine,
chambres, salle de bain, WC, dégagement, garage, cave, combles — cochées d'un coup, avec leur niveau
déjà rempli. Celles qui existent déjà sont grisées.

## 5 bis · La note de dimensionnement

Quand la case « le client souhaite obtenir des aides » est cochée **et** qu'un lot PAC est présent,
un onglet **Note dim.** apparaît. Il prépare la note de dimensionnement du dossier MaPrime Facile.

Ce que l'appli calcule : le cran de la grille à 7 crans déduit de la description de l'isolation
(épaisseur des murs, des combles, du plancher bas, âge du vitrage) — c'est la paroi la plus mauvaise
qui commande, et c'est le seul raisonnement défendable devant un contrôleur ; la surface chauffée
par la PAC, somme des pièces raccordées ; le volume ; le besoin `P = G × V × ΔT` avec les 19 °C
imposés par l'article R.241-26 ; et les deux fourchettes — 60 à 130 % pour la note, 70 à 100 % pour
le DTU 65.16. Quand la machine passe la note mais sort du DTU, l'appli le dit.

Ce qu'il reste à saisir : la civilité, le n° de parcelle si l'adresse est un lieu-dit, la
température d'arrêt de la PAC et sa puissance — ces deux dernières se recopient de la fiche produit
Projipack, et c'est la puissance à T base qui prédomine.

**Au bureau** : le gabarit `NDD MPF` est copié dans le dossier Drive du chantier et rempli avec ces
valeurs. Le modèle d'origine n'est jamais modifié. La fiche technique du matériel est à joindre —
elle se retrouve sur `base-de-donnees-cee.programme-oscar-cee.fr`.

## 5 quater · L'onglet Croquis

Un croquis au stylet, avec le rejet de paume : quand tu dessines au stylet, la main posée sur
l'écran est ignorée. Le trait suit l'appui si le stylet remonte la pression.

**Les symboles.** Vingt-cinq symboles métier à poser d'un appui plutôt qu'à dessiner : radiateur,
sèche-serviettes, plancher chauffant, groupe extérieur, unité intérieure, gainable, module PAC,
chaudière, ballon, tampon, WC, lavabo, douche, baignoire, évier, lave-linge, lave-vaisselle, VMC,
compteur d'eau, arrivée gaz, tableau, nourrice, vanne, percement, nord. Une fois posé, un symbole
se fait glisser, pivoter par pas de 15°, agrandir, et recevoir une étiquette — la marque, une cote,
un diamètre.

**L'échelle.** Tu traces un trait sur un mur dont tu connais la longueur, tu tapes la cote une seule
fois, et toutes les cotes suivantes s'affichent en mètres pendant que tu les tires. L'outil Cote pose
un trait coté ; l'outil Liaison trace un cheminement en plusieurs segments et affiche le total.

**Le plan de masse en un appui.** Le bouton « Poser les pièces à l'échelle » reprend les longueurs et
largeurs déjà saisies dans l'onglet Pièces et les sort en rectangles à la bonne échelle, avec leur nom
et leurs cotes. Il ne reste qu'à les faire glisser à leur place. L'échelle du croquis est posée au
passage.

**Ce qui remonte au chiffrage.** Une liaison mesurée peut se reporter d'un appui dans le champ
« distance jusqu'au groupe extérieur » de la pièce. Les percements relevés au croquis sortent
automatiquement dans les postes obligatoires, avec leur diamètre — c'est la grille carottage.
Et le compte rendu ne reçoit pas qu'une image : il reçoit la description, « 3 radiateurs · 1 liaison
(12,4 m) · 2 percements Ø160, Ø80 ».

**Le bâti se décrit en deux lignes.** « Niveaux habitables » reste un choix unique — plain-pied, R+1,
R+2, R+3 — parce que c'est bien une seule valeur. Mais tout ce qui s'y ajoute est à choix multiple :
sous-sol ou cave, vide sanitaire, combles aménagés, combles perdus, garage attenant, véranda. Un R+1
avec une cave et des combles perdus, c'est trois appuis.

Ce qui est coché là commande le reste : les niveaux proposés sur chaque pièce et ceux qui
apparaissent dans le croquis s'y limitent. Sur un plain-pied on ne propose que le RDC ; sur un R+2
avec cave, cinq niveaux. Tant que le bâti n'est pas renseigné, tous restent proposés — pour ne
jamais bloquer un relevé commencé par les pièces.

**Les pièces ne sont pas forcément rectangulaires.** Une pièce sélectionnée propose **⬡ Découper** :
elle devient un polygone dont on tire les coins, et un appui sur un côté ajoute un angle. De quoi
faire une pièce en L, un pan coupé, un sous-pente. La surface réelle se recalcule à chaque
déformation et s'affiche dans la pièce ; **⇥ Reporter la surface** la recopie dans l'onglet Pièces —
et crée la pièce si elle n'existait pas encore. **⬛ Redevenir rectangle** annule le découpage.

**Le dégagement se déduit.** Le bouton **⬚ Dégagement**, dans la barre du haut du croquis, quadrille
l'emprise des pièces posées, repère ce qui est vide, et garde ce qui est cerné par des pièces sur au
moins trois côtés — c'est ce qui distingue un couloir de l'extérieur du bâtiment. Chaque zone
devient une pièce en trait tireté orange, avec sa surface. Tu tires sur les coins pour ajuster.
Relancer le bouton efface les dégagements précédents du niveau et recommence, donc tu peux poser des
pièces, redéduire, reposer.

Deux limites à connaître : un couloir qui ne touche des pièces que sur deux côtés opposés n'est pas
détecté — c'est volontaire, le critère plus large découpait le vide en morceaux inutilisables. Et si
la surface habitable est renseignée dans l'onglet Maison, l'appli te dit combien de mètres carrés le
plan couvre par rapport à ce qui est annoncé : c'est ce qui révèle une pièce oubliée.

**Les étages.** Un croquis porte cinq niveaux — sous-sol, RDC, 1er étage, 2e étage, combles : sous-sol, RDC, étage, combles. On bascule d'un
— et on bascule de l'un à l'autre par la barre du haut. **Le niveau du dessous reste visible en
filigrane**, ce qui permet d'aligner un percement, une gaine ou une colonne d'un étage sur l'autre. Chaque niveau
part avec la même échelle, donc les plans se superposent vraiment. « Poser les pièces » range chaque
pièce sur son niveau, d'après ce qui est coché dans l'onglet Pièces. À l'envoi, un croquis à plusieurs
niveaux part en une image par niveau.

**Les montées et les descentes.** Vu de dessus, un tronçon vertical mesure zéro alors qu'il fait deux
mètres cinquante de gaine. L'outil **↕ Dénivelé** se pose sur n'importe quel point d'une liaison :
montée ou descente, avec des raccourcis pour la hauteur sous plafond, un étage, les combles, un
sous-sol. Une flèche apparaît sur le plan avec sa cote, et le métré affiche « 8,1 m dont 2,8 m en
vertical ». C'est ce total-là qui se reporte dans la pièce.

**La direction au stylet, la cote au clavier.** S'arrêter pile sur 4,20 m à main levée est illusoire.
Le bouton **⌨ Saisir la cote** change la façon de tracer : tu donnes la direction au stylet, tu
relâches, et l'appli te demande la longueur au clavier numérique, la mesure déjà pré-remplie. Le
trait s'ajuste à ce que tu tapes en gardant son point de départ et son angle — au dixième de
millimètre près.

Deux conséquences pratiques : la règle s'active toute seule avec ce mode, et si l'échelle n'est pas
encore posée, **la première cote que tu tapes la pose pour tout le croquis**. Tu traces un mur, tu
tapes 4,20, et le reste suit. N'importe quel trait déjà tracé se rattrape ensuite — sélectionne-le
avec Déplacer, puis **⌨ Ajuster à une cote**.

**Le trait droit.** Le bouton **📐 Règle** contraint le trait à une droite : il se cale tout seul sur
l'horizontale, la verticale et les 45°, et il s'accroche aux extrémités déjà tracées, ce qui ferme les
murs proprement. Chaque trait droit affiche sa longueur, et le bouton **↔ Cotes** garde ces longueurs
visibles en permanence. Une réglette d'échelle se dessine en bas du plan, pour rester lisible une fois
imprimé.

**L'échelle se corrige.** Un appui sur **📐 Échelle** quand une échelle existe déjà ouvre de quoi
rectifier la valeur — le mur mesurait 4,20 m et pas 4 m — ou la retracer, ou la supprimer. Toutes les
cotes du croquis suivent.

**Le zoom.** Pincement à deux doigts, molette, ou les trois boutons en bas à droite du plan. Le
pincement à deux doigts ne dessine jamais, même en plein tracé : il déplace et agrandit.

**Le croquis d'une pièce arrive déjà tracé.** Le bouton croquis, dans l'onglet Pièces, ouvre un plan
où le rectangle de la pièce est déjà là, à ses cotes et à l'échelle. Il ne reste qu'à poser dessus les
portes, fenêtres, portes-fenêtres, placards et trémies — cinq symboles de menuiserie ont été ajoutés
pour ça — puis les équipements. Le bouton **⇥ Reporter sur le plan** recopie ensuite la pièce et tout
ce qu'elle porte sur le plan d'ensemble, à la bonne échelle, sur le bon niveau. S'il y avait déjà un
rectangle du même nom sur le plan, il est remplacé au même endroit. On peut reporter autant de fois
qu'on veut : le report précédent est écrasé, jamais empilé.

**Ce qui est posé sur une pièce lui appartient.** « Poser les pièces à l'échelle » ne ramène pas
seulement les rectangles : pour chaque pièce qui a un croquis, il rapatrie aussi tout ce qui a été
posé dessus. Et sur le plan, déplacer un rectangle de pièce emmène avec lui les portes, fenêtres,
équipements et tracés qui sont dedans — l'appli le dit au moment où on l'attrape.

**Viser ce qu'on veut, pas la pièce en dessous.** Un rectangle de pièce se sélectionne par son trait,
pas par sa surface : une liaison tracée en plein milieu d'une pièce s'attrape et se gomme normalement.
Avec l'outil Déplacer, un appui dans le vide à l'intérieur d'une pièce l'attrape quand même, pour
pouvoir la faire glisser. Et la gomme ne supprime jamais une pièce : ça passe par Déplacer, puis
« Supprimer », avec le choix entre la pièce seule et la pièce avec tout ce qu'elle porte.

**Cinq natures de réseau.** Le tracé n'est plus seulement une liaison frigorifique : liaison
frigorifique, alimentation électrique, gaine de ventilation, réseau hydraulique, évacuation. Chacune
a sa couleur, son style de trait et sa liste de sections — du 1/4-3/8 au 3G2,5, du Ø125 au
multicouche 20. La section s'affiche sur le tracé et se retrouve dans le métré.

**Le cheminement proposé.** L'outil **⚡ Chemin** demande d'abord comment ça passe — par les combles
ou le faux plafond, en apparent sous goulotte, encastré dans les murs et le sol, ou par le vide
sanitaire — puis un appui sur le départ et un sur l'arrivée suffisent. Le tracé sort avec ses montées
et ses descentes déjà posées : par les combles on monte au plafond, on traverse en direct et on
redescend ; sous goulotte on longe les murs à angle droit et on descend vers le groupe. L'appui
s'accroche au symbole s'il y en a un, donc on part de l'unité intérieure et on arrive sur le groupe
extérieur sans viser.

Le choix du contournement est une heuristique : l'appli essaie les deux angles droits possibles et
garde celui qui longe le plus les murs des pièces posées. Elle ne connaît ni les poutres, ni les
gaines existantes, ni la cheminée. **C'est une proposition, pas un relevé** — d'où le point suivant.

**Le tracé se corrige en tirant dessus.** Avec l'outil Déplacer : un appui sur un sommet le déplace,
un appui n'importe où sur le tracé crée un point à cet endroit et le tire dans la foulée — c'est le
geste pour contourner ce que l'appli ne pouvait pas deviner. Un point sélectionné se supprime, ou
reçoit sa propre montée ou descente. Avec la règle active, le point tiré se cale à angle droit sur
le précédent.

**Un tracé peut changer d'étage.** Quand tu poses une montée ou une descente sur un point, l'appli
te demande aussi si ça change de niveau : monte d'un niveau, descend d'un niveau, ou reste au même.
Une gaine qui monte au plafond et redescend dans la même pièce ne change pas d'étage ; une gaine qui
traverse le plancher, si. À partir de ce point, la suite du tracé appartient au niveau d'arrivée : tu
la vois en plein sur ce niveau, et le morceau resté à l'étage d'avant reste visible en filigrane, avec
un double chevron sur le point de traversée. Le métré, lui, reste unique — c'est bien une seule
liaison.

**Le mode de passage se règle par tronçon.** Un vrai cheminement n'est jamais d'un seul tenant : trois
mètres en apparent dans la pièce, une traversée de mur, huit mètres le long de la façade, une descente
au groupe. Sélectionne un point avec l'outil Déplacer et **⌗ Mode du tronçon suivant** donne à ce
segment son propre mode. Un cinquième mode a été ajouté pour ça : **en façade, à l'extérieur** —
tracé en brun, motif différent, étiqueté sur le plan.

Le métré ventile en conséquence, et les postes suivent : « Goulotte de finition intérieure » d'un
côté, « Goulotte extérieure, fixations et protection UV » de l'autre. Les montées et descentes se
rattachent au mode du tronçon qui les suit — une descente le long de la façade compte en façade.

**Le mode de passage se chiffre.** Les mètres tracés en apparent ressortent en poste « Goulotte de
finition » avec leur longueur. Attention : c'est la longueur totale du tracé, traversées de murs
comprises — à dégrossir avant de chiffrer.

**Le métré.** En haut de l'onglet Croquis, le total par nature, tous croquis et tous niveaux
confondus : « Alimentation électrique — 18,4 m dont 5,6 m de montées et descentes · 18,4 m en
3G2,5 ». Il tient compte des dénivelées et ne compte jamais deux fois ce qui a été reporté d'un
croquis de pièce sur le plan d'ensemble. Le même métré part dans le compte rendu et dans les données
envoyées, et l'écran de fin signale les tracés dont la section n'a pas été précisée. Les longueurs
sont brutes : elles restent à majorer des chutes et des raccordements avant de chiffrer.

**Le fond.** Feuille quadrillée, page blanche, ou une photo prise sur place qu'on annote — flécher un
passage, coter un mur, entourer une arrivée. Le format bascule paysage/portrait. Chaque pièce a son
propre bouton croquis, en plus des croquis d'ensemble.

Les croquis partent avec la fiche comme des images, par le même circuit que les photos, dans le même
dossier Drive. Ils sont gardés en traits et pas en image tant qu'ils sont sur la tablette : l'annulation
est propre et ça ne pèse presque rien.

Ce qu'il ne fait pas : pas de reconnaissance de formes, pas de cotation automatique des murs.
C'est un croquis — mais avec la règle et l'échelle, les longueurs se lisent toutes seules.

## 5 ter · Le vase d'expansion

Sous le volume d'eau du circuit, quatre champs : hauteur statique, température de départ maxi,
tarage de la soupape, volume du vase intégré au générateur. L'appli applique la NF EN 12828
(`Vn = Vu × (Pf+1)/(Pf−Pi)`, réserve d'eau comprise) et sort la taille commerciale au-dessus.
Trois réponses possibles : le vase intégré suffit, il est juste à la limite — le cas qui se
termine par une soupape qui crache —, ou il faut un complément, et l'appli dit lequel.

---

## 6 · Le mail « liste des pièces » — à valider avant de le brancher

> **Objet : Votre projet — les documents à réunir pour vos aides**
>
> Bonjour,
>
> Suite à notre rendez-vous, vous m'avez indiqué souhaiter bénéficier des aides à la rénovation
> énergétique. Pour vérifier votre éligibilité et monter le dossier, j'aurai besoin des éléments suivants :
>
> - Votre dernier **avis d'imposition** (celui portant le revenu fiscal de référence), pour toutes les
>   personnes qui occupent le logement
> - Votre **numéro fiscal** et le numéro de votre avis d'imposition
> - Le **nombre de personnes** composant votre foyer
> - Un **justificatif de propriété** : titre de propriété ou dernier avis de taxe foncière
> - L'**année d'achèvement** du logement
> - La liste des **autres aides** déjà demandées ou perçues pour ces travaux (prime énergie,
>   aide d'une collectivité, aide de votre employeur) — leur déclaration est obligatoire
> - Une **adresse e-mail** que vous consultez régulièrement : toutes les notifications passent par là
>
> Deux points importants sur l'ordre des opérations :
>
> - Les **travaux ne doivent pas commencer** avant l'accord écrit de l'organisme. Je vous préviendrai
>   dès que le feu vert sera arrivé.
> - Le montant des aides dépend de vos revenus et de l'équipement retenu. Je vous le confirmerai
>   par écrit avec le devis, une fois ces éléments en main.
>
> Vous pouvez me renvoyer ces documents en réponse à ce message.
>
> Cordialement,
> Rémi KATA – KA-RÉ
> 06.80.80.50.01

---

## 7 · Ajouter un lot plus tard

Dans `index.html`, le tableau `LOTS` en haut du script. Un lot = un objet, une question = une ligne :

```js
{k:"cle_interne", l:"La question telle qu'elle s'affiche", i:"Précision en petit, facultatif",
 t:"chx", opts:["Choix 1","Choix 2"], u:"unité"}
```

`t` vaut `"txt"` (défaut), `"num"`, `"chx"` ou `"long"`. Ajouter ensuite l'entrée correspondante
dans `TUILES` pour qu'elle apparaisse au choix des lots. Rien d'autre à toucher.

Les tuiles qui n'ont pas encore de module dédié (PAC air/eau, gainable, salle de bain, VMC…)
ouvrent le lot générique avec le bon nom : rien ne bloque sur le terrain en attendant.

---

## 8 · Diagnostic

Depuis la console du navigateur : `KARE.payload()` montre exactement ce qui part,
`KARE.resumeTexte()` le compte rendu, `KARE.promptSelectClim()` le prompt,
`KARE.viderFile()` relance les envois en attente.
Le bouton **Voir les données envoyées** fait la même chose sans console.
