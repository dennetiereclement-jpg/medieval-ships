# Ateliers d'artisanat (un bloc = un atelier)

Huit ateliers de métiers médiévaux pour les villages, les villes et les serveurs MMO / RPG (les sept de 1.13.0 et
l'établi du joaillier de 1.22.0). **Chaque atelier est UN seul bloc**, exactement comme les [tentes](TENTES.md) et
les [charrettes](CHARRETTES.md) : on pose le bloc, l'atelier entier (forge, établis, étagères, outils, toit sur
poteaux, lanternes...) est dessiné à partir de lui. Ils sont **statiques** : pas d'IA, pas d'animation, pas
d'apparition naturelle, rien ne « tick » ; seules quelques particules discrètes (fumée, flammes, glyphes) sont
dessinées par le client.

> **Le mod n'a ni recettes, ni interface de fabrication, ni progression de métier**, et 1.22.0 n'en invente aucune.
> Ce sont des **objets à poser** ; un clic droit déclenche seulement un point d'accroche générique (un événement pour
> un autre mod, ou une commande choisie par le serveur), voir
> [Relier un atelier à un système de métiers](#relier-un-atelier-à-un-système-de-métiers). Sans réglage, il affiche
> un court message (« Établi du joaillier — aucune interface de fabrication n'est reliée »).

| id | nom | métier (id du métier) | contenu |
|----|-----|-----|-----|
| `workshop_blacksmith` | Atelier du forgeron (Blacksmith's Workshop) | Forgeron (`blacksmith`) | forge en pierre avec cheminée et feu, enclume noire sur un bloc de pierre, établi, outils, chaînes, lanternes, bac d'eau, petit toit de planches sur poteaux |
| `workshop_leatherworker` | Atelier du tailleur de cuir (Leatherworker's Workshop) | Tailleur de cuir (`leatherworker`) | grande peau tendue lacée sur un cadre, établi drapé de cuir, chutes, outils de coupe, caisses cerclées, étagères, veste de cuir suspendue, lanterne |
| `workshop_tailor` | Atelier du tailleur de lin (Tailor's Workshop) | Tailleur de lin (`tailor`) | métier à tisser et sa toile bleue et blanche, rouleaux de tissu, bobines, tissus suspendus, tunique sur un mannequin, table de couture au chemin bleu frangé d'or, lanterne, sac |
| `workshop_engineer` | Atelier de l'ingénieur (Engineer's Workshop) | Ingénieur (`engineer`) | large toit de planches, grande roue dentée au mur, plan épinglé, outils suspendus, long établi d'engrenages et de pièces de laiton, caisses métalliques, tuyaux de cuivre, lanterne |
| `workshop_cook` | Atelier du cuisinier (Cook's Workshop) | Cuisinier (`cook`) | foyer en pierre et feu sous un grand chaudron noir, table de préparation et pain, herbes, ail et piments suspendus, étagères de pommes, pains, bols et bocaux, caisses, paniers, lanterne |
| `workshop_alchemist` | Atelier de l'alchimiste (Alchemist's Workshop) | Alchimiste (`alchemist`) | table d'alchimie au drap violet et livre ouvert, étagères de fioles colorées, amas d'améthyste, alambic vert lumineux et tuyau de cuivre, mortier et pilon, bougie, plantes, bannière violette, tonneau |
| `workshop_enchanter` | Atelier de l'enchanteur (Enchanter's Workshop) | Enchanteur (`enchanter` ; offensif, défensif, mystique) | auvent violet aux bordures dorées, enseigne « Enchanteur », autel d'enchantement et livre ouvert lumineux, bibliothèques, cristaux, potions, parchemins, bougies, lanternes, bannières étoilées, cercle arcanique doré, coffres, tapis violet sur une estrade |
| `workshop_jeweler` | Établi du joaillier (Jeweller's Workbench), 1.22.0 | Joaillier (`jeweler`) | établi en chêne noir d'environ 2 x 1 blocs, tiroirs à poignées de fer, ferrures rivetées, tablette basse, chemin violet à l'ourlet dentelé et au diamant d'or, machine à tailler et polir les gemmes (disque, roue à manivelle, pince tenant une bague à la gemme bleue), lingots d'or, gemmes taillées lumineuses, plateau de pierre, bagues, marteau, pinces, support à griffes, loupe, outils suspendus ([détails](#établi-du-joaillier-1220)) |

Objets : `medievalships:workshop_blacksmith`, `medievalships:workshop_leatherworker`, `medievalships:workshop_tailor`,
`medievalships:workshop_engineer`, `medievalships:workshop_cook`, `medievalships:workshop_alchemist`,
`medievalships:workshop_enchanter`, `medievalships:workshop_jeweler` — tous dans l'onglet créatif **Ateliers** (séparé des vaisseaux, des tentes et des
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
- `/workshop types` — les huit ids.

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

## Établi du joaillier (1.22.0)

`workshop_jeweler` — « Établi du joaillier » / « Jeweller's Workbench », métier `jeweler`, huitième atelier (après
l'enchanteur). `/give @p medievalships:workshop_jeweler` (ou `/workshop give workshop_jeweler`, `/workshop place
jeweler`). Seul l'établi central de l'image de référence est modélisé (pas la tente autour) :

- un **établi rectangulaire en chêne noir** d'environ **2 blocs de large sur 1 de profondeur**, plateau à 1,0 bloc,
  1,37 bloc avec la machine ; pieds carrés épais à sabots de fer, traverses basses et écharpes sur les côtés, plateau
  de planches encadré d'un chant plus épais et plus clair qui déborde, **ferrures de coin rivetées** en fer ;
- **deux tiroirs** en façade (cadre mouluré, entrée de serrure, poignée de fer) de part et d'autre du chemin de table ;
- une **tablette basse** près du sol avec deux petits lingots, des pépites d'or et deux gemmes (rouge, bleue) ;
- un **chemin violet** posé sur le plateau d'arrière en avant, qui **retombe devant** entre les tiroirs : bandes et
  **ourlet dentelé (en zigzag) dorés**, **symbole de gemme taillée en or** au centre de la partie qui pend (et un
  court retombé à l'arrière) ;
- sur le plateau, au centre, une **machine à tailler / polir les gemmes** en fonte grise, un peu tournée vers
  l'avant-droite pour qu'on voie le disque et la roue : socle, bâti en A de chaque côté, paliers, axe, **disque de
  polissage** rond (acier poli à cercles concentriques), **roue à manivelle** à rayons sur le côté avec sa poignée,
  **pince** sur un montant qui tient une **bague d'or sertie d'une gemme bleue** contre le disque ;
- à gauche une **pile de cinq lingots d'or** (trois dessous, deux en travers), un **petit marteau de précision**, une
  **pince de joaillier** (poignées gainées de cuir rouge) et des **gemmes taillées** éparses (rouge, bleue, verte,
  violette) ;
- à droite un **plateau de pierre blanche** garni de cinq gemmes, **deux bagues en cours** (l'une à plat avec sa
  pierre rouge, l'autre debout dans la fente d'un petit bloc de bois), un **support à griffes** en laiton tenant une
  gemme verte, une **loupe** (lentille cerclée de laiton, manche de bois) ;
- sous le bout gauche du plateau, deux **crochets** : une **pince** et un **petit marteau** y pendent.

Les gemmes (et la pierre des bagues) sont **légèrement lumineuses** (dessinées pleine lumière, éléments `glow_*`) ;
aucune particule. 171 cubes, détails fins dans la texture : atlas propre
`textures/entity/workshops_c.png` (256 x 256, `tools/workshops/ws_texture_c.py`), modèle par
`tools/workshops/generate_workshop_jeweler.py` (réutilise les aides de `wslib_b.py`). Les petits objets (gemmes,
bagues, outils, crochets, tablette) sont dans l'os `detail`, cachés au-delà de `tentDecorDistance`.
**Collisions** : une boîte pour l'établi (2,04 x 1,0 x 1,04) et une pour la machine au-dessus du plateau ; on tourne
autour. Bloc d'ancrage sous le milieu de l'établi ; l'avant (tiroirs, chemin qui pend) fait face au joueur qui le pose.

## Relier un atelier à un système de métiers

**Aucune recette, aucune interface de fabrication, aucune progression n'a été inventée** : le mod ne fournit qu'un
point d'accroche léger et générique, le même pour **les huit ateliers**, pour qu'un système de métiers existant (un
autre mod, un datapack, un plugin MMO qui s'ouvre par commande) prenne la main.

Un **clic droit** sur un atelier (avec ou sans objet en main ; accroupi avec un objet, l'objet se pose comme
d'habitude), côté **serveur** :

1. **spectateur** : rien ; **survie, aventure, créatif** : la suite. Au plus **un usage toutes les 10 ticks par
   joueur** (un double clic ne déclenche qu'une fois) ;
2. l'**événement Fabric `fr.medievalships.api.WorkshopUseCallback`** est déclenché avec le joueur, le monde, la
   position du bloc d'ancrage, le `TentType` de l'atelier et l'**id du métier**. Un écouteur qui renvoie autre chose
   que `ActionResult.PASS` **annule** la suite (son résultat devient celui du clic) ;
3. sinon, si la configuration du serveur a une **commande pour ce métier**, elle est exécutée **comme le joueur**
   (`@s` = le joueur, à sa position et son orientation), silencieusement, avec le niveau de permission d'un bloc de
   commande (2) — seule la configuration choisit la commande, le joueur ne fait que la déclencher ;
4. sinon un **court message** dans la barre d'action : « Établi du joaillier — aucune interface de fabrication n'est
   reliée » (le nom de l'atelier cliqué ; en anglais « … — no crafting interface is linked »).

**Ids des métiers** : champ facultatif `"profession"` du fichier `workshops/<id>.json` ; par défaut l'id sans
`workshop_` : `blacksmith`, `leatherworker`, `tailor`, `engineer`, `cook`, `alchemist`, `enchanter`, `jeweler`.

**Réglage** (`config/medievalships.json`, section `"server"`, clé `workshopCommands`, vide par défaut ; la clé est un
id de métier, `workshop_<métier>` est accepté aussi ; le `/` initial est facultatif ; une commande vide est ignorée) :

```json
"server": {
  "workshopCommands": {
    "jeweler": "trigger jeweler_menu",
    "blacksmith": "function monserveur:metiers/ouvrir_forge",
    "alchemist": "dialog show @s monserveur:alchimie"
  }
}
```

Exemples : un datapack qui ouvre son menu sur un `trigger` (`/scoreboard objectives add jeweler_menu trigger` puis
`scoreboard players enable @a jeweler_menu`), une `function` qui donne des quêtes ou ouvre un coffre-menu, la
commande d'ouverture d'une interface MMO existante. Le fichier est relu au démarrage du serveur.

**Pour un mod Java** (dépendance au mod Medieval Ships) :

```java
WorkshopUseCallback.EVENT.register((player, world, pos, type, profession) -> {
    if (!"jeweler".equals(profession)) {
        return ActionResult.PASS;          // les autres ateliers : comportement normal
    }
    MonMod.ouvrirInterfaceJoaillier(player); // votre propre interface / vos recettes
    return ActionResult.SUCCESS;           // annule la commande configurée et le message
});
```

Le code peut aussi changer la commande d'un métier : `ConfigManager.server().setWorkshopCommand("jeweler", "...")`
(jusqu'au prochain chargement de la configuration).

## Tests faits

- 1.22.0, JUnit `JewelerBenchTest` : ids des métiers des huit ateliers (`blacksmith` … `jeweler`), champ
  `"profession"` lu (nettoyé, vide ou absent : l'id sans `workshop_`, aucun pour les autres objets) ; réglage
  `workshopCommands` lu par Gson et nettoyé (clés en minuscules, `workshop_` accepté, `/` retiré, entrées vides ou
  nulles ignorées, vide par défaut et pour un ancien fichier), `workshopCommand` / `setWorkshopCommand` ; établi :
  taille (≈ 2,15 x 1,17 x 1,42), deux boîtes de collision, atlas `workshops_c.png`, icône, modèle statique avec son os
  `detail`, budget de cubes, gemmes lumineuses et chaque élément de la référence présent par son nom (pieds,
  traverses, ferrures, tiroirs, tablette, chemin, machine, disque, roue, manivelle, pince, bague tenue, cinq lingots,
  gemmes, plateau, bagues, marteau, pinces, support, loupe, crochets, outils suspendus). `WorkshopTest`,
  `CartTest`, `TrainingTest`, `DecorationTest` : huit ateliers, indices de `PROPS` décalés (52 objets).
- 1.22.0, test en jeu `WorkshopGameTest` : l'établi du joaillier est posé, orienté, entré en collision, photographié
  et retiré comme les sept autres ; puis le point d'accroche : avec la commande `tag @s add used_jeweler` réglée pour
  `jeweler` par `setWorkshopCommand`, le clic côté serveur (le `onUse` de l'état du bloc) l'exécute comme le joueur
  (étiquette ajoutée) ; un second clic dans les 10 ticks ne fait rien, puis à nouveau après ; un écouteur
  `WorkshopUseCallback` qui renvoie `FAIL` l'annule ; sans commande le clic est traité (message) sans rien exécuter ;
  un spectateur ne déclenche rien. Le réglage est rétabli ensuite.
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
- 1.22.0 : le clic droit d'un vrai joueur à la souris (le test appelle le même `onUse` côté serveur), l'affichage du
  message dans la barre d'action, une vraie interface MMO ouverte par commande ; le rendu de l'établi dans le jeu
  n'est vu que sur la capture du test (les images de contrôle sont celles du rendu hors jeu).

## Ajouter un atelier (pour les développeurs)

1. Le modèle `models/entity/<id>.bbmodel`, son atlas (`"texture"`), `workshops/<id>.json` (emprise, boîtes de
   collision, particules, `"profession"` facultatif) et l'icône `textures/item/<id>.png`. Repère : y vers le haut, +z = l'avant, le bloc
   d'ancrage en (0, 0, 0), posé au sol en y = 0.
2. Java : une ligne `workshop("<id>", "nom fr", "English name")` dans `core/TentTypes.java` (et dans `WORKSHOPS`),
   les noms dans `lang/fr_fr.json` et `lang/en_us.json` (`block.medievalships.<id>`), `blockstates/<id>.json`,
   `items/<id>.json` et `models/item/<id>.json` (copies des existants). Bloc, objet, onglet, commandes, collisions,
   particules et rendu sont génériques.
