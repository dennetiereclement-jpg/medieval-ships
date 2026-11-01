# Tentes médiévales (un bloc = une tente)

Six tentes de décor pour les camps (orcs, trolls, bandits), marchés, ports, camps militaires, zones de quête et
villages. **Chaque tente est UN seul bloc** : on pose le bloc, la tente entière (toile, poteaux, cordes, plancher,
rambardes, lanternes et meubles) est dessinée à partir de lui, comme les navires sont dessinés à partir de leur
entité. Rien n'est posé autour, rien ne « tick », rien ne tourne côté serveur une fois la tente posée.

![Les six tentes](preview_tentes.png)

| id | nom | emprise (l × h × p, blocs) | cubes | générateur |
|----|-----|-----|-----|-----|
| `tent_command` | Grande tente de commandement | 10,5 × 8,3 × 8,4 | 449 | `tools/tents/generate_tent_command.py` |
| `tent_adventurer` | Petite tente d'aventurier | 8,3 × 3,8 × 8,8 | 154 | `tools/tents/generate_tent_adventurer.py` |
| `tent_market` | Grand abri de marché | 11,5 × 5,7 × 10,7 | 318 | `tools/tents/generate_tent_market.py` |
| `tent_camp` | Tente triangulaire de campement | 7,7 × 4,3 × 8,4 | 153 | `tools/tents/generate_tent_camp.py` |
| `tent_dwelling` | Tente d'habitation | 7,9 × 4,8 × 9,7 | 441 | `tools/tents/generate_tent_dwelling.py` |
| `tent_chief` | Grande tente de chef | 10,3 × 8,1 × 10,0 | 673 | `tools/tents/generate_tent_chief.py` |

L'emprise est centrée sur le bloc d'ancrage (largeur et profondeur réparties de part et d'autre ; la profondeur
compte les cordes et piquets devant et derrière). Les six objets sont dans l'onglet créatif **Tentes**.

- **Grande tente de commandement** : grand toit de toile beige usée aux bords déchirés, quatre gros poteaux
  légèrement penchés, structure ouverte à rambardes, cordes et contreventements, lanternes suspendues, grande roue
  de navire au centre, plancher de bois ; bureau-table de stratégie, chaise, banc, tabourets, livres, coffre.
- **Petite tente d'aventurier** : petite tente beige en A, toit un peu irrégulier, deux pans ouverts devant,
  piquets et cordes ; caisses, sac, tonneaux et un couchage (paillasse + couverture, dans le modèle).
- **Grand abri de marché** : grande toile beige sur plusieurs poteaux, bords irréguliers déchirés, pièces de tissu
  et fanions rouges, tables et étals de bois, tonneaux, caisses, marchandises (paniers, caisses de légumes, tartes,
  jambon, poulet rôti, amphores), lanternes.
- **Tente triangulaire de campement** : tente en A rustique, toile beige en pente, entrée ouverte, perches et
  cordes ; couchage, caisses, panier, sac, tonneau, lanterne.
- **Tente d'habitation** : toit de toile beige vieillie, intérieur praticable au tapis rouge, lit, petite table,
  coffre et rangements, lanternes qui éclairent l'intérieur ; devant, le pavillon à tables, bancs, tonneaux et
  bouteilles de la seconde image de référence.
- **Grande tente de chef** : plan polygonal, haut toit pointu en cône rayé beige / rouge / sombre, entrée ouverte,
  plusieurs piliers de bois, tapis, bibliothèque, tables, chaises, coffre, tonneaux, lanternes.

## Poser, orienter, retirer

- **Poser** : clic droit au sol avec l'objet. L'entrée de la tente fait face au joueur (état de bloc `facing`,
  quatre directions : le modèle et les boîtes de collision tournent d'un quart de tour avec lui).
- **Vérification de place** : avant de poser, le jeu vérifie que toute l'emprise de la tente (tournée selon
  l'orientation) est libre — air, herbes, fleurs, neige, plantes remplaçables — et que le sol est assez plein sous
  l'emprise ; sinon un message rouge en français (ce qui gêne, et où) et rien n'est posé. Une tente n'écrase
  **jamais** une construction existante.
- **Retirer** : casser le bloc d'ancrage (le bloc au centre, au sol : visez-le, son contour est un bloc entier). En
  survie il rend l'objet. Ou `/tent remove`. Il n'y a rien d'autre à nettoyer : rien d'autre n'a été posé.
- **Marcher dedans** : la toile et les cordes ne bloquent pas (on entre et sort librement) ; les poteaux, planchers,
  rambardes et meubles pleins ont des boîtes de collision statiques, ajoutées aux collisions des entités proches par
  le mixin de collision des navires (`EntityCollisionMixin` → `ShipCollisions.withHulls` → `TentCollisions`).
- **Eau** : le bloc d'ancrage est déclaré plein (`solid`) : l'eau qui coule dessus (rive, marée d'un seau) ne
  l'emporte pas, contrairement à un bloc fin ordinaire.
- **Meubles** : purement visuels (pas de coffre ouvrable, pas de lit utilisable, pas de siège). Voir la liste
  ci-dessous.
- **Persistance** : c'est un bloc avec son entité de bloc, dans le chunk. Multijoueur et serveur dédié : rien de
  spécial, le rendu est côté client uniquement ; le serveur ne garde que l'orientation et les boîtes de collision
  (remplies au chargement du chunk, oubliées à son déchargement, sans balayage ni tick).

## Commandes (admin, mêmes permissions que `/ship`)

- `/tent give <id> [joueurs]` — donne l'objet (`/ship give <id>` marche aussi pour les six tentes).
- `/tent place <id> [x y z] [south|west|north|east]` — pose la tente à la position (ou celle de l'exécutant),
  entrée vers la direction donnée (ou vers l'exécutant). Même vérification de place libre que l'objet.
- `/tent remove [nearest|x y z]` — retire la tente la plus proche, ou celle dont l'ancrage est en x y z.
- `/tent list` — les tentes chargées de ce monde, de la plus proche à la plus lointaine.
- `/tent types` — les six ids.

## Meubles par tente (mods source, substituts)

Les meubles viennent des mods de décoration du serveur : **Furnish** (`furnish:`), **Farmer's Delight**
(`farmersdelight:`), **Farmhouse Decorations** (`farmhouse_decorations:`), **Lands of Icaria** (`landsoficaria:`),
**Mebahel Dwarven** (`mebahelcreaturesdwarven:`). Chaque id a été vérifié dans les fichiers des mods. Le modèle de
bloc du mod est dessiné en place quand le mod est installé sur le client ; si le mod manque, le bloc vanilla
indiqué (`→`) est dessiné à la place, et à défaut une boîte de substitution peinte dans le modèle de la tente. Dans
tous les cas le serveur n'a pas besoin des mods : il ne manque jamais rien et rien ne plante. Les meubles sont
**visuels** : on ne peut pas les ouvrir ni s'y asseoir.

- **Grande tente de commandement** (12) : `farmhouse_decorations:desk` (table de stratégie),
  `farmhouse_decorations:pile_of_books`, `furnish:book_pile` (cartes et livres), `furnish:spruce_chair`,
  `furnish:spruce_bench`, `furnish:spruce_stool` ×2 (sièges), `furnish:spruce_crate`,
  `mebahelcreaturesdwarven:dwemer_chest` → `minecraft:chest`, `landsoficaria:cypress_barrel` → `minecraft:barrel`,
  `farmhouse_decorations:chained_kerosene_lantern` (suspendue, lumineuse), `farmhouse_decorations:kerosene_lantern`
  → `minecraft:lantern`.
- **Petite tente d'aventurier** (7) : `furnish:spruce_crate`, `furnish:oak_crate`, `farmersdelight:rice_bag`,
  `farmersdelight:carrot_crate` (dehors), `landsoficaria:cypress_barrel` ×2 → `minecraft:barrel`,
  `farmhouse_decorations:chained_kerosene_lantern` (lumineuse) ; le couchage fait partie du modèle.
- **Grand abri de marché** (33) : étals `furnish:spruce_bench`, caisses `furnish:oak_crate` ×2,
  `furnish:spruce_crate` ×2, marchandises `farmersdelight:carrot_crate`, `cabbage_crate`, `onion_crate`,
  `tomato_crate`, `rice_bag` ×2, `bamboo_basket`, `wooden_basket`, `straw_bale`, `apple_pie`, `pumpkin_pie`,
  `sweet_berry_cheesecake`, `honey_glazed_ham_block`, `roast_chicken_block`, `furnish:book_pile`,
  `farmhouse_decorations:wine_bottle`, `red_wine_bottle`, `furnish:amphora` → `minecraft:decorated_pot`,
  `landsoficaria:storage_vase` → `minecraft:decorated_pot`, tonneaux `landsoficaria:cypress_barrel`,
  `loaded_cypress_barrel` ×3 → `minecraft:barrel`, lanternes `farmhouse_decorations:chained_kerosene_lantern` ×4,
  `kerosene_lantern`.
- **Tente triangulaire de campement** (9) : `furnish:spruce_crate` ×2, `furnish:oak_crate`,
  `furnish:dark_oak_crate`, `farmersdelight:potato_crate`, `farmersdelight:wooden_basket`,
  `farmersdelight:rice_bag`, `landsoficaria:cypress_barrel` → `minecraft:barrel`,
  `farmhouse_decorations:chained_kerosene_lantern` (lumineuse) ; le couchage fait partie du modèle.
- **Tente d'habitation** (31) : `farmhouse_decorations:rug_3x_3` → `minecraft:red_carpet` (tapis rouge),
  `farmhouse_decorations:single_bed` (lit), `furnish:spruce_square_table`, `furnish:spruce_table`,
  `furnish:spruce_stool`, `furnish:plate` ×2, `farmersdelight:spruce_cabinet`,
  `mebahelcreaturesdwarven:dwemer_chest`, `furnish:spruce_crate` ×2, `furnish:dark_oak_crate`,
  `farmersdelight:carrot_crate`, `farmersdelight:rice_bag`, `landsoficaria:cypress_barrel` ×2,
  `loaded_cypress_barrel` → `minecraft:barrel`, `farmhouse_decorations:wine_bottle`, `red_wine_bottle`, lanternes
  `farmhouse_decorations:chained_kerosene_lantern` ×9 et `kerosene_lantern` ×3 (lumineuses, dedans et sous le
  pavillon).
- **Grande tente de chef** (17) : `farmhouse_decorations:rug_3x_3` → `minecraft:red_carpet`,
  `farmhouse_decorations:tall_bookshelf` → `minecraft:bookshelf`, `furnish:dark_oak_table` ×2,
  `furnish:dark_oak_chair`, `furnish:dark_oak_stool`, `furnish:spruce_chair` ×2,
  `mebahelcreaturesdwarven:dwemer_chest`, `furnish:spruce_crate`, `furnish:oak_crate`,
  `farmersdelight:carrot_crate`, `farmersdelight:rice_bag`, `landsoficaria:cypress_barrel` ×2 → `minecraft:barrel`,
  `farmhouse_decorations:chained_kerosene_lantern` ×2 (lumineuses).

Les fichiers exacts : `assets/medievalships/interiors/<id>_decor.json` (positions, orientation, échelle, `glow`,
`alt`, bone de substitution `fallback`).

## Performances

- **Aucun tick** : l'entité de bloc n'a pas de ticker, pas de particules, pas d'animation ; le serveur ne fait rien
  pour une tente posée hormis ses boîtes de collision statiques (par chunk, consultées seulement pour les entités
  qui bougent dans l'emprise).
- **Rendu** : un `BlockEntityRenderer` qui réutilise le chemin statique du rendu des navires (`BbModel.renderStatic`,
  matrices des bones en cache) ; la boîte de rendu est l'emprise de la tente, donc le jeu l'élimine hors champ
  (frustum culling). Modèles modestes (153 à 673 cubes) : des centaines de tentes restent peu coûteuses.
- **Niveaux de détail** (`config/medievalships.json`, section `server`, lus par le client dans son propre fichier
  de configuration : ils ne sont pas synchronisés depuis le serveur) :
  `tentDecorDistance` (32 blocs) : en deçà, les meubles et petits détails sont dessinés ; entre cette distance et
  `tentRenderDistance` (64 blocs) seule la tente nue est dessinée ; au-delà, rien.
- **Lanternes** : les lanternes lumineuses sont dessinées en pleine lumière (`glow`), sans source de lumière dans le
  monde.

## WorldEdit, Axiom, structures

Une tente n'est qu'un bloc avec son état `facing` et une entité de bloc vide : copier / coller / tourner une zone
avec WorldEdit ou Axiom, ou l'enregistrer dans une structure, copie la tente avec son orientation (la rotation
d'une sélection tourne l'état `facing` comme pour n'importe quel bloc orienté). Rien à nettoyer, pas de doublon :
les boîtes de collision se reconstruisent au chargement du chunk.

## Tests faits

- JUnit `TentTest`, `TentMarketTest`, `TentCampTest` : rotation des emprises et des boîtes de collision selon
  l'orientation, lecture des six fichiers `tents/<id>.json`, des décors (ids de blocs de la forme `mod:bloc`,
  bones de substitution présents dans le modèle) et des modèles.
- Test en jeu `TentGameTest` (CI, appelé par `ShipClientGameTest`, variantes vanilla / Lithium / avec les mods de
  décoration) : la petite tente d'aventurier en détail (`/tent place`, bloc et orientation, refus d'une seconde
  tente par-dessus, un joueur en survie arrêté par un poteau avant et entrant librement par l'entrée, captures
  d'écran, `/tent remove`, bloc et collisions disparus), puis chacune des cinq autres tentes une fois : posée,
  bloc, orientation, entité de bloc, une requête de collision sur sa première boîte pleine, une capture d'écran,
  retirée par `/tent remove x y z`.

## Non vérifié

- La pose au clic droit par un vrai joueur (le test en jeu passe par `/tent place`, même code de vérification de
  place) ; la casse à la main du bloc d'ancrage en survie (le retrait est testé par commande).
- Les copies WorldEdit / Axiom (raisonnement ci-dessus, pas d'essai).
- Le rendu réel des meubles des mods n'est visible que dans la variante « decor » du test en jeu (captures) ;
  dans les autres variantes ce sont les substituts.

## Ajouter une tente (pour les développeurs)

1. `tools/tents/generate_<id>.py` sur le modèle des six existants : `tl.setup(id)`, un `tl.Bone` racine, les aides
   de `tentlib.py` (`post`, `pole`, `rope`, `guy`, `canvas_panel`, `cone_roof`, `pennant`, `platform`, `railing`,
   `bedroll`, `lantern`), `tl.collide(...)` pour toute boîte solide non couverte par les aides, un `tl.Decor()` pour
   les meubles des mods (`decor.block(id, x, y, z, facing, scale, glow, alt, fallback)` ; bornes des blocs dans
   `tentlib.BOUNDS` ou le catalogue des mods), `decor.fallbacks(root)`, puis `tl.export(root, id, decor, icon=...)`.
   Repère : y vers le haut, +z = l'entrée, le bloc d'ancrage en (0, 0, 0).
2. Lancer le générateur : il écrit le modèle (blockbench + assets), l'atlas partagé `textures/entity/tents.png`,
   l'icône, `interiors/<id>_decor.json` et `tents/<id>.json` (emprise + boîtes de collision), lus par `TentType`.
3. Java : une ligne `TentType.load("<id>", "nom fr", "English name")` dans `core/TentTypes.java` (et dans `ALL`),
   les noms dans `lang/fr_fr.json` et `lang/en_us.json` (`block.medievalships.<id>`), un blockstate
   `blockstates/<id>.json` (copie des existants), `items/<id>.json` et `models/item/<id>.json` (idem). Bloc, objet,
   entité de bloc, commandes, collisions et rendu sont génériques : rien d'autre à enregistrer.
