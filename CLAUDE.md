# Fiche chantier KA-RÉ

Application tablette de relevé de rendez-vous devis, pour **Rémi KATA — SARL KA-RÉ**,
artisan plombier-chauffagiste-climaticien à Raville (57), qui travaille seul.

Il l'utilise chez le client : il coche les lots techniques concernés, répond aux questions,
relève les pièces, dessine le plan, et envoie la fiche. Au bureau, un chiffrage nocturne
automatique reprend le tout pour préparer le devis.

## Ce que ce projet n'est pas

Ce n'est pas un logiciel de dessin ni un outil de dimensionnement thermique. C'est un
**aide-mémoire de relevé** : son seul but est que Rémi ne reparte pas d'un chantier sans une
information dont il aura besoin pour chiffrer. Chaque fonction doit se justifier par « quelle
information oubliée est-ce que ça rattrape ? ». Une fonction qui n'y répond pas est du poids mort.

## Architecture

Un seul fichier, `index.html`, qui contient le HTML, le CSS et le JavaScript. Aucune dépendance
externe, aucun CDN, aucun framework. Servi par GitHub Pages, installé comme PWA sur la tablette.

```
index.html               tout le code (~352 Ko)
sw.js                    service worker : réseau d'abord pour la page, cache d'abord pour les assets
manifest.webmanifest     manifeste PWA
icon-192.png             icônes, logo KA-RÉ sur fond blanc
icon-512.png
icon-maskable-512.png
gen-demo.py              génère une démo neutralisée (aucun envoi, aucun téléchargement)
```

Le JavaScript est découpé en sections repérées par des bannières `/* ==== TITRE ==== */` :
outils, stockage, navigation, une section par vue, photos, mode client, sorties, envoi,
démarrage, et le module croquis en fin de fichier.

## Contraintes non négociables

**JavaScript ES5 uniquement.** La tablette est une vieille Android. Pas de `let`, `const`,
fonctions fléchées, template literals, classes, `async/await`. Les seules exceptions tolérées
sont `Promise` et `fetch`, présents partout depuis longtemps.

**`confirm()` et `prompt()` sont bloqués** dans certains navigateurs embarqués. Pour une
confirmation, utiliser le double appui armé (`arme(bouton, libellé, action)`). Pour une saisie,
les dialogues maison (`demanderTexte`, `choisirDansListe`, `demanderDenivele`, `demanderCote`).

**CORS avec Make.** Les POST partent en `application/x-www-form-urlencoded`, corps
`"payload=" + encodeURIComponent(JSON.stringify(obj))`. C'est le seul type de contenu qui évite
le preflight OPTIONS, que Make ne gère pas. Pour *lire* une réponse, le scénario Make doit
renvoyer l'en-tête `Access-Control-Allow-Origin: *`.

**Tout accès à `localStorage` passe par `lire()` / `ecrire()`**, qui encapsulent le try/catch.
La mémoire peut être pleine ou refusée : `ecrire()` renvoie `false`, il faut le traiter.

**Ergonomie tactile** : `min-height: 44px` sur ce qui se touche, `font-size: 16px` sur les
`input` — en dessous, iOS zoome au focus et l'écran part de travers.

## Règles métier qui touchent le code

- **Aucun champ n'est obligatoire.** L'envoi ne refuse jamais rien, même une fiche vide, même
  sans nom de client. L'écran de fin signale, il ne bloque pas. C'est une décision de Rémi,
  pas un oubli : sur un chantier, celui qui sait ce qui compte est celui qui est devant le client.
- **Aucun prix dans l'appli.** Le relevé ne chiffre pas. Les prix viennent des devis fournisseurs,
  de la base Notion, puis de CEDEO, et seulement au bureau.
- **Rien ne part vers Axonaut depuis l'appli.** Aucune création de devis, jamais. La fiche part
  vers Make, et c'est un humain qui valide ensuite.
- Les calculs de puissance sont affichés comme **pré-dimensionnement à confirmer** par Select Clim
  ou Projipack. Ne jamais les présenter comme un résultat définitif.

## Pièges rencontrés, à ne pas réintroduire

- **`input type="number"` AVALE la virgule.** C'est le pire bug rencontré sur ce projet, trouvé le
  01/09/2026 par Rémi en plein relevé chez un client : taper `2,5` n'y vide pas le champ et n'alerte
  pas — le navigateur retire la virgule et enregistre `25`. Une cote fausse d'un facteur 10, relevée
  sur un chantier et impossible à rattraper au bureau. Depuis la v2.9, tout champ chiffré passe par
  `champNombre(i)` : `type="text"` + `inputmode="decimal"`, ce qui donne le clavier numérique et
  laisse passer la virgule comme le point, `nb()` faisant la conversion. **Ne jamais remettre
  `type="number"` dans ce fichier.** Corollaire : assigner `i.value = "2,5"` fonctionne désormais.
- **Un rectangle est à distance zéro sur toute sa surface.** Mesurer la distance à son *contour*,
  sinon une pièce gagne toujours contre ce qui est posé dessus et on ne peut plus rien y sélectionner.
- **Le métré comptait double.** Les éléments reportés d'un croquis de pièce sur le plan portent un
  `src` et sont exclus du comptage. La source de vérité est le croquis de pièce.
- **`rendre()` reconstruit tout l'écran.** Sans mémoire de l'état, les blocs dépliés se referment et
  la page remonte. Le registre `BLOCS` et la restauration du scroll s'en chargent : tout nouveau
  `<details>` doit passer par `bloc()` ou par `memoDetails()`.
- **Les caractères de contrôle écrits littéralement dans une expression régulière** cassent le
  démarrage complet de l'appli. Toujours écrire les échappements sous forme `\n`, jamais le
  caractère brut.
- **Le magnétisme du croquis existait, mais derrière un bouton éteint.** `snapPoint()` (accrochage
  aux extrémités) et `calerAngle()` (calage horizontale / verticale / 45°) ne s'appliquent qu'en mode
  « Règle », et `CRE.droit` valait `false` au démarrage. Résultat le 04/09/2026 : Rémi relève une
  salle de bain en L, ses traits ne se joignent pas et rien n'est d'équerre — alors que le code pour
  le faire était là. Depuis la v3.0 la règle est active par défaut. Leçon générale : une aide qui
  n'est pas le comportement par défaut n'existe pas pour celui qui est debout sur un chantier.
- **Le rayon d'accrochage était en coordonnées du plan**, donc il rétrécissait à l'écran dès qu'on
  dézoomait. Il est maintenant divisé par `CRE.z` pour garder la même tolérance sous le doigt.
- **`snapPoint()` s'accrochait au trait en cours de tracé.** L'élément est poussé dans `C.el` dès le
  `pointerdown`, donc pendant le `pointermove` son propre bout figurait parmi les candidats, à
  quelques pixels du doigt : le trait avançait par sauts de la largeur du seuil et l'angle calé par
  `calerAngle()` était écrasé au passage. Mesuré le 05/09/2026 : viser 0,245 renvoyait 0,240, la
  position précédente du trait. D'où le paramètre `sauf` — **toujours passer l'élément en cours**.
- **L'outil Déplacer insérait un sommet au lieu de déplacer.** Tout appui sur un trait tombait sur
  `segmentSous()` → `insererSommet()`, donc déplacer une ligne était impossible : elle se déformait,
  ou ne bougeait pas. Depuis la v3.0, appui = déplacer l'élément, appui long (550 ms) = ajouter un
  point. Le timer est annulé dès que le doigt bouge de plus de 0,006.
- **L'ORDRE compte quand on convertit un champ.** Dans `champ()`, `i.type` était encore `number` au
  moment où la valeur était assignée : écrire `"10."` dans un champ number le vide silencieusement,
  donc la saisie repartait de zéro dès le séparateur décimal. Toujours appeler `champNombre(i)`
  AVANT `i.value = ...`.
- **`majCalculs()` appelle `rendre()`, qui détruit le champ en cours de frappe.** Sur la vue Pièces,
  chaque touche reconstruisait l'écran, l'input était recréé et le clavier se fermait : il fallait
  rappuyer dans la case à chaque chiffre. `rendre()` mémorise maintenant le `data-ch` du champ actif
  et la position du curseur, et les restaure après reconstruction. Tout nouveau champ de saisie doit
  porter un `data-ch` unique, sinon il perdra le focus de la même façon.
- **Une ancre de patch qui ne correspond plus** fait échouer un script de modification en cours de
  route. Vérifier que le fichier a bien été écrit avant de passer à la suite.

- **Un outil qui reste armé pose en boucle.** En mode Symboles, chaque `pointerdown` posait un
  symbole — y compris le premier doigt d'un pincement pour zoomer. Un plan relevé le 17/09/2026 s'est
  couvert d'UI. Depuis la v3.4 : un symbole posé rend la main (retour à « Déplacer »), et
  `annulerTrace()` reprend le symbole posé par le premier doigt quand le second arrive (`pose:true`
  dans `CRE.encours`). Pour en poser un autre, on reprend « Symboles » — c'est ce que Rémi demandait.
- **Le mur gagnait contre l'UI collée dessus.** Dans l'outil Déplacer, l'ordre était sommet → segment →
  élément : une UI posée contre une cloison (le cas normal) tombait sur le segment du mur et c'est la
  pièce qui partait. `symSousBoite()` est testé en premier : un symbole est petit et posé exprès, il
  gagne toujours sous le doigt. Et `C.fige` (bouton « Bloquer ») retire les pièces de toute sélection.
- **« Poser les pièces » effaçait le plan.** Ajouter une pièce oubliée puis relancer le bouton
  reposait tout en grille, et le positionnement fait au doigt était perdu. Depuis la v3.4,
  `poserToutesLesPieces()` ne pose en grille que si le plan est vide ; sinon `completerPieces()`
  ajoute ce qui manque sous le plan, à la même échelle, met à jour les cotes qui ont changé sans
  bouger les rectangles, et ne touche à rien d'autre.
- **Un balcon comptait 1 kW de chauffage.** Toute pièce entrait dans `calcPiece()`. Le flag
  `P.annexe` (proposé d'après le nom, décochable) sort la pièce des volumes, puissances, surface
  chauffée et dégagements, tout en la gardant sur le plan en pointillé avec sa surface.
- **Radiateur et sèche-serviettes étaient dessinés en élévation** sur un plan vu de dessus. Ce sont
  maintenant des rectangles fins hachurés (1,4 × 0,18 et 0,6 × 0,18), à coller contre un mur.
- **Une fiche liée à une opportunité est partie « sans nom ».** Le 17/09/2026, `client.nom` était
  vide à l'envoi alors que `societe` et `opp_titre` étaient remplis ; Make a créé un dossier
  « fiche sans nom » dans CLIENTS/2026. Le code qui vide le nom n'a pas été identifié. Filets posés :
  `nomClient()` (nom saisi → société Axonaut → nom extrait du titre « … - NOM Prénom, Ville ») est
  utilisé dans le payload, les photos et l'écran d'envoi ; au démarrage, une fiche liée sans nom
  reprend la société et l'incident est journalisé ; vider le champ Nom à la main est journalisé aussi.
  Si ça se reproduit, le journal technique (Réglages) dira lequel des deux cas s'est produit.
- **Le repère d'une UI se déduit de la pièce qui la contient** (`reperer()` : « UI Salon »), sinon
  « UI n ». Il suit le symbole quand on le déplace, sauf si Rémi a tapé un texte à la main (`E.auto`).

- **Le canvas bougeait sous le doigt.** `.crzone` centrait le canvas verticalement ; quand la barre
  contextuelle apparaissait au premier appui sur un élément (ou que la palette de symboles se
  fermait), la zone changeait de hauteur et le canvas était recentré de ~25 px pendant le geste :
  le trait sautait de 4 % de la largeur du plan avant même de bouger. Mesuré le 19/09/2026 par un
  `pointermove` sans déplacement : +0,043. Depuis la v3.5 le canvas est ancré en haut
  (`align-items:flex-start`), la barre contextuelle garde toujours sa hauteur (vide plutôt
  qu'absente), et la palette appelle `dimensionner()` quand elle s'ouvre ou se ferme. Règle : rien ne
  doit changer la géométrie de la zone pendant qu'un pointeur est actif.
- **Les photos partaient en direct, pas par la file.** Sans réseau, la fiche attendait dans la file
  mais les photos et les croquis rasterisés échouaient en silence (`.catch(function(){})`) et
  n'étaient jamais renvoyés. Depuis la v3.5 tout passe par `fileAjouter()` ; l'envoi direct n'est que
  le repli quand `localStorage` refuse d'écrire.
- **La file s'écrasait elle-même.** `viderFile()` travaillait sur une copie prise au départ et la
  réécrivait à chaque succès : ce qui arrivait pendant l'envoi (les photos, justement) était perdu.
  Elle relit maintenant la file à chaque pas et retire chaque item par sa clé `k`.
- **Le rejet de paume ignore le doigt pendant 1,8 s après le stylet** (`CRE.dernierPen`). Voulu.
  Mais un test Playwright qui mélange `pen` et `touch` sans attendre tombe dedans — et un
  utilisateur qui pose le stylet pour reprendre au doigt aussi, brièvement.

## v3.6 — sortie de la mise en situation « multisplit à la place d'une chaudière gaz »

- **Une seule question commande la dépose** : `remplace` dans le lot clim (`climRemplace(L)`,
  `climEstChauffage()`). Si oui, les questions gaz après travaux, conduit, radiateurs, ECS, appoint et
  abonnement apparaissent (`si:climRemplace`), l'alerte « chauffage principal » s'affiche, et
  `postesObligatoires()` ajoute les postes correspondants — **sans prix ni taux de TVA** : la TVA de
  la dépose dans une opération clim reste « à trancher au bureau ». Une question peut porter un
  crochet `apres:function(L,v)` exécuté au choix d'une puce : `rad_dep` passe les émetteurs vides
  à « Déposé ».
- **`bilanClim()`** sépare pièces traitées (avec UI, chaud + froid) et pièces sans UI (chaud) ; les
  annexes sont exclues. C'est ce qui alimente le bloc du lot, le résumé, `calculs.clim` du payload.
- **Photos guidées** : `photosAttendues(L)` = `photosCles(L)` (les indispensables, qui manquent à
  l'envoi) puis le reste de `etiquettesLot(L)` sans « Autre ». Le bloc Photos est en tête du lot ; un
  tap sur une vignette vide ouvre l'appareil avec l'étiquette, la photo prise remplace le bouton. En
  clim-remplace, deux étiquettes s'ajoutent (plaque du générateur déposé, compteur gaz).
- **Cotes en une saisie** : `eclaterCotes("4,9 x 2,7")` → `["4,9","2,7"]` (séparateurs x × * / ; ou
  espace, 2 ou 3 nombres, sinon `null`). Appliqué sur `change` du champ Longueur. `chainer([...])`
  fait d'Entrée le passage au champ suivant, en retrouvant le champ par `data-ch` **après** un
  éventuel `rendre()` — ne jamais garder une référence d'élément entre deux rendus.
- **Ouvrants** : `M.ouv=[{l,h}]` en mètres, `vitreeMur(M)` = Σ l×h si au moins un ouvrant est complet,
  sinon la case « Surface vitrée (m²) » (qui n'est affichée que sans ouvrant). Toute lecture de la
  surface vitrée passe par `vitreeMur()` — plus jamais `nb(M.vit)` en direct.
- **Plaud sur une pièce** : `P.plaud` = ISO de l'appui. Résumé, payload (`dicte_plaud`) et
  `pointsOuverts()` disent « vers 15 h 12 (chercher ±10 min) » : l'horloge de la tablette et celle du
  Plaud ne sont pas synchronisées.
- **Plain-pied ou appartement** (`toutAuRdc()`) : les pièces courantes vont toutes au RDC ; l'ordre de
  `PIECES_TYPES` est celui d'une visite (entrée, séjour, cuisine, chambres, SDB, WC…).
- **Vue Maison** : la description d'isolation pour la NDD et l'échéance ne s'affichent qu'avec un lot
  PAC ; le régime de départ qu'avec un lot hydraulique (`aLotHydraulique()`). L'abonnement électrique
  reste toujours visible — Rémi y tient : c'est ce qui dit si le client doit changer de calibre.

## v3.7 — « Gaz ou PAC — à trancher »

Le client qui hésite entre une chaudière gaz et une PAC ne coche plus deux lots : dans le lot gaz,
« On remplace par quoi ? » → « À trancher » (`gazHesite(L)`). Le tronc commun est posé une fois, puis
les questions propres à la PAC (préfixe `pac_`, `si:gazHesite`), une question `versions` de type
**`multi`** (nouveau type : `pucesMulti`, valeur stockée en chaîne `"A + B"` pour rester compatible
avec `rep()`, le payload et le résumé), la préférence du client et « ce qui bloque la PAC ».

- **`aLotPac()` est vrai aussi en « à trancher » dès qu'une version PAC est cochée**
  (`gazVersionPac`) : ça ouvre d'un coup la NDD, les blocs Maison réservés à Projipack, le circuit de
  chauffage des pièces, le prompt Projipack et la ligne ADEME du brief. `promptProjipack()` prend ses
  données dans le lot gaz (`LH`) quand il n'y a pas de lot PAC.
- `postesObligatoires()` préfixe « Version gaz — » et « Version PAC — » ; le brief ajoute la consigne
  « un devis par version + comparatif interne » — **sans montant d'aide ni de prix** : les aides se
  vérifient à la source au moment du chiffrage, et les chiffres du comparatif sont pour Rémi, pas
  pour le client.
- La Maison relève la consommation annuelle en kWh (`facture_kwh`) en plus du montant : c'est la
  donnée du comparatif qu'on ne peut plus aller chercher le soir.

## v3.8 — retour du premier chantier en 3.7 (22/09/2026)

- **Le clavier décimal d'Android n'a ni « x » ni espace.** La saisie « 4,9 x 2,7 » de la v3.6 était
  donc intapable sur la tablette. Depuis la v3.8, `champ(…, fois=true)` pose une touche **×** dans le
  champ (`.kx`) : `preventDefault()` sur `pointerdown` garde le focus dans l'input, donc le clavier
  reste ouvert ; la touche écrit « x » et appelle `onc()`. Le tiret est aussi accepté comme séparateur
  par `eclaterCotes()`. Règle : une saisie composée doit être possible avec les seules touches du
  clavier décimal, ou avec une touche fournie par l'appli.
- **Chrome envoie `change` au champ actif quand `rendre()` le retire du DOM**, pendant que l'élément
  est encore rattaché. Comme `majCalculs()` rappelle `rendre()` à chaque touche, un gestionnaire de
  `change` qui répartit « 4,9 x 2 » se déclenchait dès le premier chiffre après le x, et relançait un
  rendu imbriqué qui perdait le focus. D'où `RENDU_EN_COURS` : pendant un rendu, les gestionnaires de
  `change` qui modifient l'état ne font rien. **Tout nouveau gestionnaire de `change` sur un champ
  géré par `champ()` doit commencer par `if(RENDU_EN_COURS || !document.body.contains(this)) return;`.**
  Corollaire pour les tests : un `change` dispatché sur un élément détaché est ignoré — le
  dispatcher sur l'élément vivant, retrouvé par `data-ch`.
- **Les ouvrants n'étaient pas trouvés** : en 3.7 la ligne largeur × hauteur n'apparaissait qu'après
  « + Ouvrant », dans un bloc replié, à côté d'une case « Surface vitrée (m²) » qui invitait à taper
  le résultat. Depuis la 3.8 la ligne largeur × hauteur est là d'office pour chaque mur (ligne
  « neuf » non stockée tant qu'on ne tape rien), la case m² n'apparaît que sur « m² déjà connus » ou
  pour une ancienne fiche, et elle prime sur les ouvrants si elle est remplie (`vitreeMur`). Taper
  « 0,8 x 2,1 » dans la case m² crée un ouvrant.
- **`ouvrirLots()` s'ouvre tout seul 350 ms après le choix d'un chantier** (`nouvelleFiche`). Un test
  qui enchaîne trop vite se fait recouvrir sa boîte de dialogue : attendre 500 ms après le choix.

## v3.9 — ce que la première fiche réelle en 3.7 (MAGAR, 22/09/2026) a appris

- **Sans année de construction, la fiche part sans aucune puissance.** « Une vieille ferme, début
  1900 » n'avait pas de case : G nul, déperditions, chaud, froid vides, Projipack « bloquant ». Depuis
  la 3.9 : tranches d'années (`PERIODES`, année représentative au milieu), « Inconnue », et repli du
  G sur la description de l'isolation en épaisseurs (`cranNDD`) — `origineG()` dit d'où vient le G.
  Le bloc « épaisseurs » s'affiche aussi sans lot PAC quand l'année manque.
- **La surface habitable vide est remplacée par la somme des pièces** (`surfaceHabitable()`,
  origine dans le payload). Rémi ne veut pas la retaper.
- **Les pièges de saisie vus dans la fiche** : « 80 » dans « nombre de trous » (c'était le Ø), « 72 »
  en surface vitrée (c'était 0,72 ou des cm). Réponses : carottage en choix (Aucun / 1 / 2 / 3+) avec le
  Ø et le mur en texte, `mursIncoherents()` (vitrée > mur) signalé sur la carte et à l'envoi.
- **Le questionnaire gaz confondait l'existant et le projet** : « Évacuation actuelle : conduit
  maçonné » alors que la cheminée était démolie et qu'une ventouse était prévue. D'où « Conduit
  supprimé ou condamné » et la question « Fumées de la nouvelle chaudière ». Idem condensats
  (« Existante à proximité / À créer, en gravité / Pompe »). En « à trancher », `pac_cond` (puits perdu
  pour l'eau de dégivrage — dit au Plaud, absent de la fiche).
- **Pièce sans émetteur** (`piecesSansEmetteur()`, lots hydrauliques seulement) : signalée sur la
  carte, à l'envoi, dans le résumé et le payload — la « pièce froide » du Plaud n'avait aucune trace.
- **Photos** : Rémi les prend au téléphone et les dépose dans Drive. Un tap sur une vignette attendue
  = « prise au téléphone » (`L.photosTel`, `P.photosTel`) ; la prise tablette reste derrière « Photo
  avec la tablette ». `photosManquantes()` en tient compte.
- **L'écran d'envoi emmène là où ça se corrige** : chaque alerte porte `vue` (id de vue ou `lid` de
  lot) et un bouton « → Corriger » ; les points ouverts sont des boutons vers leur lot.
- **Heure de départ retirée** (« je ne dois rien à personne »), champ conservé dans le modèle et le
  payload pour les anciennes fiches. « À récupérer auprès du client » (`V.docs`) part dans le brief.
- **NDD** : nom du bénéficiaire modifiable (`aides.beneficiaire`, client par défaut) ; « température
  extérieure d'arrêt » avec exemple, parce que 65 °C y avait été saisi.
- **Adapter** : tolérance passée de 45 cm à 1,5 m — au doigt, les pièces posées « à peu près » étaient
  plus loin que ça et le bouton ne faisait rien de visible.
- Constaté dans Drive, pas corrigé dans l'appli : la fiche est arrivée **deux fois** à 11 s d'écart
  (brouillon puis finale, mêmes noms de fichiers) — c'est le scénario Make de réception qui devra
  distinguer ou écraser.

## v4.0 — reprise au bureau par Make (24/09/2026)

- **Scénario Make 9858094 « KA-RE - Fiche chantier : reprise au bureau »**, webhook propre (Réglages →
  « Webhook — reprise au bureau »), data store 189035 « KA-RE Fiches chantier en cours » (9 Mo, le maximum
  de l'organisation). Quatre actions sur le même webhook, toujours avec `secret` : `sauvegarde`
  (clé = `fiche_id`, écrase), `reprises` (liste sans l'état, triée par `maj` décroissant), `reprendre`
  (renvoie `etat` en JSON brut) et `supprimer`. Une clé fausse répond 403 en JSON — c'est le seul des
  trois webhooks à le faire, utile pour diagnostiquer un réglage sur le PC.
- **Ce que l'appli envoie** : `etatPourMake()` = `exporterFiche()` tel quel tant qu'il pèse moins de
  3 Mo ; au-delà les photos perdent leur `data` (`sansData:true`, l'étiquette reste). Une photo sans
  `data` s'affiche « 📱 sur la tablette » et n'est jamais renvoyée par `envoyerPhotos()` — ne pas
  supposer `p.data` rempli ailleurs non plus. Au-delà de 3 Mo même allégé : refus, fichier ou code.
- **Quand ça part** : bouton « ☁ Sauvegarder pour le bureau » (vue envoi) et automatiquement 300 ms
  après un brouillon envoyé ; une fiche finale met `action:"supprimer"` dans la file. La sauvegarde
  n'est pas mise en file (l'état pèse trop pour `localStorage`) : sans réseau, elle échoue avec un
  message, la fiche reste sur l'appareil.
- **Reprise** : le dialogue « ⤒ Reprendre » liste d'abord les sauvegardes Make, un appui importe par
  `importerFiche()` — donc la règle « la plus récente gagne » s'applique, et une copie locale plus
  récente refuse la reprise (message explicite). Fichier et code restent en dessous.
- **`viderFile()` accepte des éléments qui portent leur propre URL (`it.u`)** même sans `cfg.webhook` :
  c'est ce qui permet au PC de vider la file de suppression sans avoir configuré l'envoi des fiches.
- Pièges Make rencontrés en le montant : « Search records » sort ses champs sous `data.` (`20.data.client`),
  « Get a record » les sort à plat avec `returnWrapped:false` ; le tri se donne en `sort:[{key, order:-1}]`
  (nombre, pas chaîne) ; un corps vide ou un JSON invalide plantaient le scénario, d'où le filtre
  `length(1.payload) > 0` et un gestionnaire « Ignore » sur le parseur ; un `WebhookRespond` qui
  intercale un texte libre dans du JSON écrit à la main casse au premier guillemet — l'état est inséré
  brut parce qu'il est déjà du JSON, le nom du client, lui, ne l'est pas.
- La publication sur GitHub est faite par Claude par `git push` (jeton du scénario Make 9722430),
  plus de dépôt à la main. `index.html` fait ~366 Ko.

## v4.1 — retour de la deuxième fiche réelle (BORDONNE, 24/09/2026)

- **La touche × est sur la longueur des radiateurs** (`champ(…, fois=true)` + `change` qui répartit
  « 80 x 60 » en longueur/hauteur, « 80 x 60 x 2 » en plus le nombre). Sur les ouvrants elle était déjà
  sur la largeur (« 1,2 x 1,5 » remplit les deux) ; la hauteur n'en a pas besoin. Règle : la touche va
  sur le **premier** champ d'un couple de cotes, jamais sur le second.
- **Les unités se rattrapent à la sortie du champ, jamais pendant la frappe.** BORDONNE est partie
  avec « 180 » sous plafond (des cm) : au `change`, une hauteur ≥ 100 est divisée par 100 (« 268 » →
  2,68 m) ; un radiateur < 10 est en mètres et passe en cm (`radEnCm`). Convertir sur `input` casserait
  la saisie (« 26 » tapé en route vers « 268 » deviendrait 0,26). Entre 10 et 100 on ne devine pas : toast.
- **Une température de confort hors 12–26 °C ne compte pas** (`tConfort()` → 20) : 1934 °C avaient été
  saisis, et `maisonIncoherences()` le dit à l'envoi avec « → Corriger ». Même fonction pour : T base
  hors −30/5, surface habitable < 80 % des pièces relevées ou < 9 m²/pièce (20 m² pour onze pièces),
  hsp > 10, côté de pièce > 40 m, radiateur < 10 cm, pièces sans cotes sans « Plans / cadastre » coché,
  aides non cochées alors que l'avis d'imposition est demandé (ou lot PAC sans aides).
- **Carottages PAC et clim en choix** (Aucun / 1 / 2 / 3 / 4 et plus / À voir), comme le gaz depuis
  la 3.9 : « 2 3 » avait été tapé dans le champ nombre. Une valeur stockée qui n'est plus dans la liste
  d'un `chx` est ajoutée comme puce (elle reste visible et dans le payload) — c'est général, dans `question()`.
- **`villeClient()`** : la commune manquante se prend dans le titre de l'opportunité (« …, Marly »), comme
  `nomClient()` prend le nom. Sans ça : dossier Drive « Nom  Objet » à double espace, sujet de mail qui
  finit par « - », NDD sans commune.
- **La fiche finale reste dans la mémoire Make**, sans ses photos (`etatPourMake(F, sansPhotos)`) : elles
  sont déjà dans Drive, et `envoyerPhotos()` ne renvoie jamais une photo sans `data`, donc un renvoi depuis
  le PC ne les duplique pas. Le libellé `appareil` porte « · fiche envoyée ». Le ✕ du dialogue « Reprendre »
  (double appui) fait le ménage — plus aucune suppression automatique. Le renvoi d'une finale corrigée
  recrée `fiche_<date>_<NOM>.json/.txt` dans Drive à côté des premiers : c'est au scénario de réception
  d'écraser ou de suffixer, pas à l'appli.
- Constaté, pas corrigé : la hauteur sous plafond par défaut est 2,5 (ou celle de la pièce précédente), et
  le payload ne distingue pas « 2,5 mesuré » de « 2,5 laissé ». Le Plaud disait 2,68 partout.

## v4.2 — « les plans donnent les surfaces, pas les hauteurs ni les fenêtres » (24/09/2026)

- Rémi ne retape pas les cotes quand le client fournit les plans, mais il veut être forcé — ou au moins
  averti — de relever sur place ce que les plans ne donnent pas : la hauteur sous plafond et les
  ouvrants (oubliés chez BORDONNE). Rien n'est bloquant, fidèle à la règle « aucun champ obligatoire ».
- **Bascule « 📐 Les surfaces viendront des plans du client »** en tête de la vue Pièces (`V.plansClient`) :
  coche « Plans / cadastre » dans « À récupérer », met « sur les plans » en placeholder des cotes, et
  fait taire l'alerte « pièces sans cotes ». Le payload porte `surfaces_sur_plans_client`.
- **Ligne « sur place » sur chaque pièce chauffée** dès qu'il y a un lot thermique (`lotThermique()` =
  PAC, clim ou hydraulique) : hauteur relevée ou « ✗ à relever » avec « ✓ 2,5 m, c'est bon » et
  « ⇊ Même hauteur : <niveau> » (applique aux pièces du même niveau, ou à toutes sans niveau) ; ouvrants
  comptés (`nbOuvrants`, un mur avec m² saisis compte 1) ou « ✗ à relever » avec « Sans ouvrant » (`P.sansOuv`).
- **`hspRelevee(P)`** : `P.hspOk` vrai quand la hauteur est tapée (oninput du champ, ou 3e nombre de
  « 4,9 x 2,7 x 2,5 »), confirmée, ou propagée. Les pièces créées depuis la 4.2 naissent avec `hspOk:false`
  même quand la hauteur est copiée de la pièce précédente. Les pièces d'avant n'ont pas le drapeau : toute
  hauteur différente du 2,5 par défaut est considérée relevée (heuristique assumée).
- À l'envoi : « Hauteur sous plafond non relevée : … » et « Ouvrants non relevés : … », avec → Corriger.
  Payload par pièce : `hsp_relevee`, `sans_ouvrant`.

## v4.3 — « pareil pour les émetteurs ? » (24/09/2026)

- La ligne « sur place » et les alertes couvrent aussi les émetteurs, dès qu'un lot chauffe de l'eau ou
  qu'une clim remplace le chauffage (`lotEmetteurs()`) : « ✗ Émetteur à relever » avec le bouton « Pas
  d'émetteur » (`P.sansRad`, la pièce froide assumée), « ✗ n émetteur(s) sans dimensions »
  (`emetteursIncomplets`, plancher chauffant exclu).
- **`piecesSansEmetteur()` ne dépend plus de la surface** : avec les plans du client aucune pièce n'a de
  surface, et l'alerte de la 3.9 ne sortait jamais. Une pièce non annexe, sans émetteur et sans « Pas
  d'émetteur » est signalée. Payload : `sans_emetteur` par pièce.

## v4.4 — l'épaisseur des radiateurs alu et fonte (24/09/2026)

- Projipack demande l'épaisseur d'un radiateur alu (et la profondeur d'une fonte) pour calculer la
  température de départ acceptée ; Rémi n'avait pas pensé à la regarder chez BORDONNE. Champ
  « Épaisseur (cm) » (`R.ep`) sur ces deux types seulement (`radAvecEpaisseur`), repris à l'ajout d'un
  émetteur et par « Appliquer à toutes les pièces », compté comme dimension manquante par
  `emetteursIncomplets` (« (épaisseur ?) » sur la ligne sur place), dans le payload (`epaisseur_cm`),
  le résumé et le prompt Projipack (« Alu 80×60 cm ép. 8 cm »).
- Unités : « 0,08 » (m) et « 80 » (mm) deviennent 8 cm à la sortie du champ — un radiateur de 40 cm
  d'épaisseur n'existe pas, au-dessus c'est des millimètres. `radEnCm` n'est pas utilisé ici : sa
  règle « < 10 = des mètres » aurait transformé 8 cm en 800.

## Le croquis, ce qui a été appris à l'usage

Deux formats de page figés ne tombent jamais juste : le plan finit dans un coin avec du blanc
partout. Depuis la v3.3, « ⇄ Format » a un troisième cran qui coupe la page juste sous le dessin
(`boiteDessin()` + `C.ratio = b.y2 + marge`), et le bouton `⤢` cadre la vue sur le dessin au lieu de
revenir bêtement à la page entière. Ni l'un ni l'autre ne déplace ni ne redimensionne quoi que ce
soit — **ne jamais mettre le dessin à l'échelle pour remplir la page** : les coordonnées sont
normalisées sur la largeur et `C.ech.px` y est adossé, une mise à l'échelle fausserait toutes les
cotes en mètres. Le vide à droite est le prix à payer, et il est moins cher qu'un métré faux.

## Fiches ouvertes en parallèle (v3.5)

Le nom du client dans la barre du haut est un bouton : il ouvre « Fiches ouvertes », la liste des
fiches non envoyées, avec bascule d'un appui (`ouvrirFiches()` → `ouvrirFiche(id)`), plus « Nouvelle
fiche pour un chantier » (retour à l'accueil, la fiche en cours reste ouverte) et « Fiche libre ». Un
compteur apparaît dans la barre dès qu'il y a plus d'une fiche en cours. C'était possible avant par
l'accueil, mais invisible : Rémi croyait devoir finir une fiche avant d'en commencer une autre.

## Comment tester

Il n'y a pas de framework de test. On lance l'appli dans Chromium avec Playwright, on pilote par
l'API de diagnostic exposée sur `window.KARE`, et on vérifie qu'aucune erreur JS ne remonte.

```js
const pg = await b.newPage();
pg.on('pageerror', e => console.log('ERREUR:', e.message));
await pg.goto('file:///.../index.html');
await pg.evaluate(() => { const V = window.KARE.visite; /* ... */ window.KARE.visite = V; });
```

`window.KARE` expose `visite`, `fiches`, `config`, `payload()`, `resumeTexte()`, `brief()`,
`coefG()`, `ndd()`, `metre()`, `croquis()`, `exporter()`, `importer()`, et les fonctions de
navigation. C'est le point d'entrée de tous les tests.

**Vérifier systématiquement après chaque modification** : que le script parse (`node --check` sur
le contenu de la balise script), que `window.KARE` existe au chargement, et qu'aucune erreur ne
remonte sur les parcours touchés. Une erreur JS au démarrage rend l'appli entièrement muette.

`python3 gen-demo.py` régénère la démo à partir du fichier de production : elle neutralise les
envois, les téléchargements et le service worker, et injecte des chantiers fictifs. À relancer
après chaque modification du fichier principal.

## Ce qui reste à faire

1. **Les scénarios Make existent depuis le 31/08/2026** (9736300 pour la liste, 9736360 pour la
   réception) et sont testés sur les cinq voies. Les URL et la clé partagée sont dans `README.md`,
   section 2, avec les trois pièges Make rencontrés en les montant — filtre OU/ET, module filtré qui
   arrête sa branche, `client` chaîne ou objet selon le type d'envoi.
2. **L'appli n'a jamais tourné sur un chantier réel** depuis la v1.1. Elle est passée à la v2.7
   sans un seul essai terrain. La chaîne technique, elle, est validée depuis la tablette de Rémi le
   1er septembre 2026 : liste des chantiers chargée, envoi accepté. Avant d'ajouter quoi que ce soit,
   la faire tourner en vrai chez un client.
3. **Le bouton « Tester l'envoi » ne prouve que la moitié.** Il envoie `test:true`, que le scénario
   de réception écarte aussitôt par filtre — volontairement, pour ne pas créer un dossier Drive à
   chaque essai. Du coup il vérifie que Make écoute, mais **pas que la clé partagée est bonne** : une
   clé fausse donne exactement le même écran. Et son seul retour est un toast de deux secondes, que
   Rémi n'a pas vu sur la tablette. À revoir : un aller-retour qui valide vraiment la clé, et un
   message qui reste affiché. En attendant, le test qui fait foi est « Rafraîchir la liste des
   chantiers » : il passe par l'autre scénario, qui contrôle la clé pour de bon.
4. Le fichier fait 280 Ko. S'il devient gênant, le découper en huit morceaux de 30 à 40 Ko :
   coquille HTML+CSS, puis le JS par sections, le démarrage en dernier.

## Ton interlocuteur

Rémi n'a pas le temps de lire. Les réponses vont droit au but, sans préambule ni récapitulatif de
ce qu'il vient de dire. Quand il y a un choix à faire, on le lui présente en options courtes avec
ce que chacune implique concrètement — jamais une question ouverte.

Il préfère une objection franche à un acquiescement : si une demande introduit un risque ou une
incohérence, il faut le dire avant de coder. Dans ce métier, une erreur coûte cher.
