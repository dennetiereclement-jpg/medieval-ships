# Ateliers d'artisanat (un bloc = un atelier)

Sept ateliers de métiers médiévaux pour les villages, les villes et les serveurs MMO / RPG. **Chaque atelier est UN
seul bloc**, exactement comme les [tentes](TENTES.md) et les [charrettes](CHARRETTES.md) : on pose le bloc, l'atelier
entier (forge, établis, étagères, outils, toit sur poteaux, lanternes...) est dessiné à partir de lui. Ils sont
**statiques** : pas d'IA, pas d'animation, pas d'apparition naturelle, rien ne « tick » ; seules quelques
particules discrètes (fumée, flammes, glyphes) sont dessinées par le client.

> **L'artisanat (interface, recettes, métiers) n'est pas encore relié — prévu plus tard.** Pour l'instant ce sont
> des **objets à poser** : un clic droit sur un atelier n'ouvre rien.

| id | nom | métier (prévu) | contenu |
|----|-----|-----|-----|
| `workshop_blacksmith` | Atelier du forgeron (Blacksmith's Workshop) | Forgeron | forge en pierre avec cheminée et feu, enclume noire sur un bloc de pierre, établi, outils, chaînes, lanternes, bac d'eau, petit toit de planches sur poteaux |
| `workshop_leatherworker` | Atelier du tailleur de cuir (Leatherworker's Workshop) | Tailleur de cuir | grande peau tendue lacée sur un cadre, établi drapé de cuir, chutes, outils de coupe, caisses cerclées, étagères, veste de cuir suspendue, lanterne |
| `workshop_tailor` | Atelier du tailleur de lin (Tailor's Workshop) | Tailleur de lin | métier à tisser et sa toile bleue et blanche, rouleaux de tissu, bobines, tissus suspendus, tunique sur un mannequin, table de couture au chemin bleu frangé d'or, lanterne, sac |
| `workshop_engineer` | Atelier de l'ingénieur (Engineer's Workshop) | Ingénieur | large toit de planches, grande roue dentée au mur, plan épinglé, outils suspendus, long établi d'engrenages et de pièces de laiton, caisses métalliques, tuyaux de cuivre, lanterne |
| `workshop_cook` | Atelier du cuisinier (Cook's Workshop) | Cuisinier | foyer en pierre et feu sous un grand chaudron noir, table de préparation et pain, herbes, ail et piments suspendus, étagères de pommes, pains, bols et bocaux, caisses, paniers, lanterne |
| `workshop_alchemist` | Atelier de l'alchimiste (Alchemist's Workshop) | Alchimiste | table d'alchimie au drap violet et livre ouvert, étagères de fioles colorées, amas d'améthyste, alambic vert lumineux et tuyau de cuivre, mortier et pilon, bougie, plantes, bannière violette, tonneau |
| `workshop_enchanter` | Atelier de l'enchanteur (Enchanter's Workshop) | Enchanteur (offensif, défensif, mystique) | auvent violet aux bordures dorées, enseigne « Enchanteur », autel d'enchantement et livre ouvert lumineux, bibliothèques, cristaux, potions, parchemins, bougies, lanternes, bannières étoilées, cercle arcanique doré, coffres, tapis violet sur une estrade |

Objets : `medievalships:workshop_blacksmith`, `medievalships:workshop_leatherworker`, `medievalships:workshop_tailor`,
`medievalships:workshop_engineer`, `medievalships:workshop_cook`, `medievalships:workshop_alchemist`,
`medievalships:workshop_enchanter` — tous dans l'onglet créatif **Ateliers** (séparé des vaisseaux, des tentes et des
charrettes). Piles de 16.

## Obtenir, poser, orienter, retirer

- **Obtenir** : onglet créatif « Ateliers », ou `/workshop give <id> [joueurs]` (aussi `/atelier give`,
  `/tent give`, `/ship give <id>`).
- **Poser** : clic droit au sol avec l'objet. L'avant de l'atelier fait face au joueur (état de bloc `facing`,
  quatre directions : le modèle, les boîtes de collision et les sources de particules tournent d'un quart de tour
  avec lui).
- **Vérification de place** : avant de poser, le jeu vérifie que toute l'emprise de l'atelier (tournée selon
  l'orientation) est libre — air, herbes, fleurs, neige, plantes remplaçables — et que le sol est assez plein
  dessous ; sinon un message rouge en français (ce qui gêne, et où) et rien n'est posé. Un atelier n'écrase
  **jamais** une construction existante. Même code que les tentes et les charrettes.
- **Retirer** : casser le bloc d'ancrage (au sol, au centre de l'atelier : visez-le, son contour est un bloc entier ;
  bruit de bois, solidité 1,0 comme les charrettes). En survie il rend l'objet. Ou `/workshop remove`. Rien d'autre à
  nettoyer. On peut le reposer ailleurs aussitôt.
- **Collisions** : établis, forges, enclumes, étagères, poteaux... ont des boîtes de collision statiques (celles du
  fichier `workshops/<id>.json`). Même chemin que les tentes : `EntityCollisionMixin` → `ShipCollisions.withHulls`
  → `TentCollisions`.
- **Persistance** : c'est un bloc avec son entité de bloc, dans le chunk. Multijoueur et serveur dédié : rien de
  spécial ; le rendu et les particules sont côté client, le serveur ne garde que l'orientation et les boîtes de
  collision (remplies au chargement du chunk, oubliées à son déchargement).

## Commandes (admin, mêmes permissions que `/ship`)

`/atelier` est un alias de `/workshop`. Ces deux commandes ne connaissent que les ateliers (`/tent` et `/cart`
acceptent aussi les ids des ateliers, et leurs `remove` / `list` voient tous les objets).

- `/workshop give <id> [joueurs]` — donne l'objet.
- `/workshop place <id> [x y z] [south|west|north|east]` — pose l'atelier à la position (ou celle de l'exécutant),
  l'avant vers la direction donnée (ou vers l'exécutant). Même vérification de place libre que l'objet.
- `/workshop remove [nearest|x y z]` — retire l'atelier le plus proche, ou celui dont l'ancrage est en x y z (une
  tente ou une charrette à cet endroit n'est pas touchée).
- `/workshop list` — les ateliers chargés de ce monde, du plus proche au plus lointain.
- `/workshop types` — les sept ids.

Exemple (PNJ ou bloc de commande) : `/atelier place workshop_blacksmith 120 64 -40 north`.

## Particules

Chaque fichier `assets/medievalships/workshops/<id>.json` peut lister des sources de particules :

```json
"particles": [
  {"type": "smoke", "pos": [0.0, 2.9, -1.0], "chance": 0.8, "count": 2},
  {"type": "enchant", "pos": [0.0, 1.5, 0.0], "chance": 1.0, "count": 6}
]
```

- `type` : `flame`, `small_flame`, `smoke`, `campfire_smoke`, `enchant`, `witch`, `portal`, `end_rod`,
  `electric_spark` ou `glow` (le préfixe `minecraft:` est accepté ; un type inconnu est ignoré) ;
- `pos` : le point en coordonnées de l'atelier (blocs ; y vers le haut, +z = l'avant, le bloc d'ancrage en
  (0, 0, 0) au sol), tourné avec l'orientation comme les boîtes de collision ;
- `chance` (0 à 1, défaut 1) : probabilité d'émettre à chaque « tick d'affichage aléatoire » du bloc d'ancrage —
  le jeu l'appelle environ une fois toutes les deux secondes pour un bloc proche du joueur, d'où des particules
  **discrètes** et gratuites (rien côté serveur, aucun ticker) ;
- `count` (1 à 16, défaut 1) : particules émises à chaque fois.

## Performances

- **Aucun tick** : l'entité de bloc n'a pas de ticker ; les particules passent par le tick d'affichage aléatoire
  vanilla du bloc (client seulement). Le serveur ne fait rien pour un atelier posé hormis ses boîtes de collision
  statiques (par chunk, consultées seulement pour les entités qui bougent dans l'emprise).
- **Rendu** : le même `TentBlockEntityRenderer` que les tentes et les charrettes (modèle statique en cache, atlas
  partagé, élimination hors champ par l'emprise), mêmes niveaux de détail : `tentDecorDistance` (32 blocs) et
  `tentRenderDistance` (64 blocs) dans `config/medievalships.json`.

## L'artisanat (prévu plus tard)

Les ateliers sont pensés pour un système de métiers (forgeron, tailleur de cuir, tailleur de lin, ingénieur,
cuisinier, alchimiste, enchanteur avec ses spécialisations offensif / défensif / mystique) : interface de
fabrication, recettes configurables sans Java, niveaux et expérience par joueur, commandes de quêtes. **Rien de cela
n'est encore relié** : cette version ne fournit que les objets à poser.

## Tests faits

- JUnit `WorkshopTest` : les sept fichiers `workshops/<id>.json` se chargent après les tentes et les charrettes
  (famille `workshops`, ids, noms français et anglais, `byId` avec ou sans le préfixe `workshop_`), emprises posées au
  sol et boîtes dans l'emprise, rotation des boîtes et des particules, champ `particles` lu (préfixe `minecraft:`,
  valeurs par défaut, bornes, type inconnu ignoré, rotation selon l'orientation), types des particules des fichiers
  livrés valides, noms dans `fr_fr` / `en_us`, onglet, fichiers d'objet, d'état de bloc (quatre orientations) et
  d'icône présents, modèles lisibles et sans animation. `CartTest` : 21 objets en tout.
- Test en jeu `WorkshopGameTest` (CI, appelé par `ShipClientGameTest` après les charrettes, sur une plateforme de
  pierre en terrain sec à x = 1600, chunks forcés) : `/workshop give` et `/ship give` donnent l'objet ; chacun des
  sept ateliers posé par `/workshop place` (le premier par `/atelier place`), dans les quatre orientations : bloc
  `WorkshopBlock`, orientation, entité de bloc, boîtes de collision enregistrées côté serveur et connues du client,
  une requête de collision sur sa première boîte, une capture d'écran, retiré par `/workshop remove x y z` (le
  deuxième par `/atelier remove`), boîtes oubliées ; `/workshop remove` laisse une tente en place.

## Non vérifié

- Les modèles et textures définitifs : ce document est écrit avec des fichiers provisoires (modèle de la charrette de
  marché) remplacés à l'intégration par les vrais modèles des sept ateliers ; les emprises et boîtes de collision
  réelles sont celles de ces fichiers.
- Les particules à l'écran (le code est compilé et la lecture du champ testée, mais aucune vérification visuelle
  automatique ; les captures n'en montrent que par hasard).
- La pose au clic droit par un vrai joueur et la casse à la main en survie (le test passe par les commandes, même
  code de vérification de place).
- Le passage d'un joueur ou d'un mob contre chaque boîte de collision (seule la première boîte de chaque atelier est
  interrogée en jeu).
- Les copies WorldEdit / Axiom (même bloc que les tentes : orientation copiée, collisions reconstruites au
  chargement du chunk ; pas d'essai).

## Ajouter un atelier (pour les développeurs)

1. Le modèle `models/entity/<id>.bbmodel`, son atlas (`"texture"`), `workshops/<id>.json` (emprise, boîtes de
   collision, particules) et l'icône `textures/item/<id>.png`. Repère : y vers le haut, +z = l'avant, le bloc
   d'ancrage en (0, 0, 0), posé au sol en y = 0.
2. Java : une ligne `workshop("<id>", "nom fr", "English name")` dans `core/TentTypes.java` (et dans `WORKSHOPS`),
   les noms dans `lang/fr_fr.json` et `lang/en_us.json` (`block.medievalships.<id>`), `blockstates/<id>.json`,
   `items/<id>.json` et `models/item/<id>.json` (copies des existants). Bloc, objet, onglet, commandes, collisions,
   particules et rendu sont génériques.
