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
index.html               tout le code (~280 Ko)
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

- **`input type="number"` refuse une valeur assignée avec une virgule.** `i.value = "2,5"` vide le
  champ silencieusement. Toujours écrire un point ; c'est la lecture qui tolère la virgule.
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
- **Une ancre de patch qui ne correspond plus** fait échouer un script de modification en cours de
  route. Vérifier que le fichier a bien été écrit avant de passer à la suite.

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
