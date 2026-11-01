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
- `/tent types` — les ids de tous les objets en un bloc (six tentes, et depuis 1.12.0 / 1.13.0 / 1.14.0 les huit
  [charrettes](CHARRETTES.md), les sept [ateliers](ATELIERS.md) et les six
  [tentes de marchands](#tentes-de-marchands-1140)).

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

## Tentes de marchands (1.14.0)

Six grandes tentes d'étal, posées comme les six autres (un bloc, même bloc / entité de bloc / rendu / collisions /
commandes), rangées dans le même onglet créatif **Tentes**, après les six premières. Elles partagent le même
pavillon (`tools/merchant/merchantlib.py`, fonction `pavilion`) : carré d'environ 6,5 × 6 blocs ouvert devant et sur
l'avant des côtés, quatre gros poteaux sculptés (bois sombre, frettes de fer, chapiteau, fleuron doré), poutres
d'avant-toit à 3,4 blocs, haut toit à quatre pans légèrement creusés jusqu'à 6,6 blocs avec un épi doré, rayures
couleur / beige, lambrequin à dents carrées bordé d'or, mât à drapeau à queue d'aronde à l'arrière gauche (et un
petit drapeau à l'arrière droit, guirlande de fanions vers le sommet), grande bannière à l'emblème au milieu de
l'avant, lanternes allumées sur les poteaux avant, tapis à l'emblème devant l'entrée, comptoir en L, étagères du
fond, toile de fond et de l'arrière des côtés. Chaque tente a son propre atlas (`textures/entity/<id>.png`).

| id | nom | couleur / emblème | emprise (l × h × p, blocs) | cubes | générateur |
|----|-----|-----|-----|-----|-----|
| `tente_armurier` | Tente du marchand d'armes et d'armures | rouge / épées croisées | 8,5 × 8,2 × 8,7 | 620 | `tools/merchant/generate_tente_armurier.py` |
| `tente_alchimiste` | Tente du marchand d'alchimie | violet, bords dorés / fiole | 8,4 × 8,2 × 8,7 | 762 | `tools/merchant/generate_tente_alchimiste.py` |
| `tente_herboriste` | Tente de l'herboriste | vert, lierre / feuille | 8,4 × 8,2 × 8,7 | 816 | `tools/merchant/generate_tente_herboriste.py` |
| `tente_forgeron` | Tente du forgeron | bleu marine / enclume | 8,4 × 8,2 × 8,7 | 644 | `tools/merchant/generate_tente_forgeron.py` |
| `tente_nourriture` | Tente du marchand de nourriture | jaune ocre / fromage | 8,4 × 8,2 × 8,7 | 681 | `tools/merchant/generate_tente_nourriture.py` |
| `tente_tissus` | Tente du marchand de tissus | turquoise / parchemin | 8,8 × 8,2 × 8,7 | 660 | `tools/merchant/generate_tente_tissus.py` |

L'emprise compte le drapeau qui dépasse à l'arrière gauche (jusqu'à 4,5 blocs du centre) et le **tapis devant
l'entrée** (jusqu'à 5,4 blocs devant le centre) : il faut cette place libre devant la tente pour la poser.

**Obtenir / poser** : `/give @p medievalships:tente_armurier` (de même `tente_alchimiste`, `tente_herboriste`,
`tente_forgeron`, `tente_nourriture`, `tente_tissus`), ou `/tent give tente_armurier`, ou dans l'onglet Tentes.
Clic droit au sol : l'entrée fait face au joueur. `/tent place armurier` (le nom court sans `tente_` marche aussi),
`/tent remove`, casser le bloc d'ancrage (au centre, au sol) : comme les autres tentes.

**Ce qu'on y trouve** (tout est dans le modèle sauf les meubles des mods, listés ensuite) :

- **Marchand d'armes et d'armures** : bannières rouges aux épées croisées (devant, avant droit, côté gauche),
  râtelier d'épées, haches et lances le long du côté gauche, second râtelier d'épées et de lances au fond, deux
  armures de plates complètes sur leurs supports derrière le comptoir, heaumes, rondaches et lingots sur les
  étagères et le comptoir, une épée posée, lances dans un tonneau, l'écu au lion d'or appuyé sur une caisse devant,
  caisses cerclées de fer.
- **Marchand d'alchimie** : étagères pleines de fioles de couleur, chaudron violet bouillonnant avec un cristal
  d'améthyste lumineux à l'avant gauche, grosses fioles sur le comptoir gauche, livre ouvert sur une nappe violette
  à franges dorées, bougies, bocaux, parchemin, bouquets d'herbes suspendus.
- **Herboriste** : lierre sur le toit, le lambrequin et les poteaux, bouquets d'herbes séchées et de lavande
  suspendus, pots de fleurs (blanches, violettes, rouges) et pousses sur les comptoirs et les étagères, caisses
  moussues, caisses de récolte, paniers.
- **Forgeron** : forge de pierre au foyer rougeoyant au fond à gauche, grosse enclume grise sur un bloc de pierre
  devant, râtelier d'épées, heaumes, boucliers, outils et lingots ; la forge émet de temps en temps une flamme et
  une fumée (particules vanilla des « random display ticks » du bloc, comme les ateliers : rien de permanent).
- **Marchand de nourriture** : table de présentation sous une nappe jaune avec une pyramide de fromages, meules et
  pains sur les étagères, comptoir de tomates, pommes, petits pains et légumes, jambons et saucissons pendus à la
  poutre avant, paniers, sacs, tonneaux.
- **Marchand de tissus** : grand casier de rouleaux de tissu (crème, bleu, lilas, violet, jaune, or, rouge), comptoir
  du fond avec une pyramide de coupons, tissus suspendus, étagère de linge plié, tringle de tissus pendus au-dessus
  du comptoir gauche, mannequin en robe crème à l'avant gauche, comptoir droit sous une nappe turquoise bordée d'or,
  rideau turquoise au poteau avant droit.

**Meubles des mods** (même principe que plus haut : le bloc du mod s'il est installé, sinon le bloc vanilla
indiqué `→`, sinon une boîte de substitution du modèle ; purement visuels) :

- **Armes et armures** (7) : `landsoficaria:cypress_barrel` ×2 → `minecraft:barrel`, `furnish:spruce_crate` ×3,
  `furnish:dark_oak_crate`, `farmhouse_decorations:kerosene_lantern` (sur le comptoir, lumineuse).
- **Alchimie** (4) : `landsoficaria:cypress_barrel` ×2 → `minecraft:barrel`, `furnish:spruce_crate`,
  `farmhouse_decorations:pile_of_books`.
- **Herboriste** (5) : `landsoficaria:cypress_barrel` → `minecraft:barrel`, `farmersdelight:cabbage_crate`,
  `farmersdelight:carrot_crate`, `farmersdelight:onion_crate`, `farmersdelight:wooden_basket`.
- **Forgeron** (5) : `landsoficaria:cypress_barrel` → `minecraft:barrel`, `furnish:spruce_crate` ×3,
  `farmhouse_decorations:tool_board` (panneau à outils sur le côté droit).
- **Nourriture** (6) : `farmersdelight:tomato_crate`, `farmersdelight:cabbage_crate`, `farmersdelight:potato_crate`,
  `farmersdelight:wooden_basket`, `farmersdelight:rice_bag`, `landsoficaria:cypress_barrel` → `minecraft:barrel`.
- **Tissus** (5) : `furnish:spruce_crate` ×5 → `minecraft:barrel`.

Les bannières, emblèmes, armures, fioles, rouleaux de tissu, fromages, l'enclume et la forge sont modélisés (aucun
meuble de mod ne les représente). **Collisions** : poteaux, comptoirs, étagères, râteliers, tonneaux et caisses,
enclume, forge, chaudron ; la toile, les bannières et le tapis ne bloquent pas, l'entrée au milieu de l'avant reste
libre.

**Pour les développeurs** : `merchantlib.py` donne `setup`, `Atlas(id, colour)` (+ `atlas.add(nom, l, h, peintre)`
pour les régions propres à une tente), `pavilion(...)` (options : emblème, coin du drapeau, bannières de côté,
lanternes, comptoir, étagères, lierre ; renvoie la disposition : hauteurs, dessus des comptoirs, niveaux des
étagères, sol libre, places près des poteaux avant, bone `detail`), des accessoires (`barrel`, `crate`, `sack`,
`basket`, `bottle`, `hanging_bunch`, `weapon_rack`, `sword`, `axe`, `spear`, `counter`, `shelf_unit`,
`table_cloth`, `banner`, `rug`, `vine`, `lantern`), `Decor` et `export` (écrit `tents/<id>.json` avec sa
`"texture"`, le modèle, l'atlas, l'icône, le décor). Relancer un générateur réécrit tous les fichiers de sa tente.

**Limites connues / non vérifié** :

- Le test en jeu des six tentes de marchands (`TentGameTest`, ci-dessous) est écrit mais n'a pas encore tourné en
  CI au moment de la 1.14.0 (exécutions annulées pour libérer les machines) : la pose, les collisions et le rendu en
  jeu ne sont vérifiés que par les tests JUnit et les rendus hors jeu (`tools/preview.py`).
- Les rayures du toit sont dessinées par facettes : leurs bords font de petites marches d'une rangée à l'autre au
  lieu d'une ligne droite.
- Le rendu réel des meubles des mods (seulement dans la variante « decor » du test en jeu) et des particules de la
  forge n'ont pas été vus.

## Tentes de marchands II (1.15.0)

Cinq tentes d'étal de plus, du même système que les six de la 1.14.0 (un bloc = toute la tente, modèle statique,
boîtes de collision, niveaux de détail, aucun tick, aucune particule permanente), du même pavillon
(`merchantlib.pavilion`) et à la même échelle, rangées dans l'onglet **Tentes** après les six premières
(`TentTypes.MERCHANTS2`). Chacune a son atlas (`textures/entity/<id>.png`).

| id | nom | couleur / emblème de la bannière | générateur |
|----|-----|-----|-----|
| `tente_barde` | Tente du vendeur de barde | bordeaux et beige / lyre d'or sur bannière violette | `tools/merchant/generate_tente_barde.py` |
| `tente_fusils` | Tente du vendeur de fusils | rouge sombre et beige / mousquets croisés sur bannière sombre | `tools/merchant/generate_tente_fusils.py` |
| `tente_archer` | Tente du vendeur d'archerie | vert et beige, toit plus bas / arc et flèche | `tools/merchant/generate_tente_archer.py` |
| `tente_mage` | Tente du vendeur de mage | violet et beige, ornements dorés / étoile d'or | `tools/merchant/generate_tente_mage.py` |
| `tente_armures` | Tente du vendeur d'armures | bleu marine et beige / écu héraldique | `tools/merchant/generate_tente_armures.py` |

**Obtenir / poser** : `/give @p medievalships:tente_barde` (de même `tente_fusils`, `tente_archer`, `tente_mage`,
`tente_armures`), ou `/tent give tente_barde`, ou dans l'onglet Tentes. Clic droit au sol : l'entrée fait face au
joueur. `/tent place barde` (nom court sans `tente_`, ici `barde`, `fusils`, `archer`, `mage`, `armures` ; attention,
`armurier` reste la tente d'armes et d'armures de la 1.14.0), `/tent remove`, casser le bloc d'ancrage : comme les
autres tentes. Comme pour la 1.14.0, il faut de la place libre devant l'entrée pour le tapis.

**Pour un PNJ marchand (EasyNPC) et les joueurs** : chaque tente garde à l'intérieur, derrière le comptoir
principal, une place libre d'au moins 1 × 1 × 2,2 blocs (sans boîte de collision) où poser le PNJ ; l'entrée au
milieu de l'avant et le tapis devant restent libres (le tapis est plat, sans collision).

**Ce qu'on y trouve** (d'après l'image de référence ; tout est modélisé dans la tente sauf les meubles des mods) :

- **Vendeur de barde** : luths et guitares et petits instruments accrochés au fond, grande harpe dorée, tambours
  (rouge à cordage doré, naturel), livres de musique et partitions, livre ouvert sur un lutrin, flûtes dans un
  tonneau, étagères et comptoirs, rideaux bordeaux sur les côtés, tapis violet bordé d'or, lanternes.
- **Vendeur de fusils** : râtelier de fusils et de mousquets debout le long du fond, long comptoir sous un chemin
  de table rouge à dents dorées avec un long fusil et un pistolet à barillet, caisses de munitions, petites pièces
  mécaniques et laiton, tonneaux de poudre, lanternes.
- **Vendeur d'archerie** : arcs exposés au fond, carquois pleins de flèches à l'empennage blanc, fagots de flèches,
  arbalètes sur le comptoir drapé de vert, caisses, la **cible ronde d'entraînement** sur son chevalet devant la
  tente, tapis vert, lanternes ; toit plus bas que les autres pavillons.
- **Vendeur de mage** : étagères de cristaux bleus et violets et de potions qui luisent (dessinés en pleine
  lumière, sans particules), bâtons de mage à tête de cristal debout à droite, orbe lumineux sur son support,
  grimoires ouverts sur le comptoir central drapé de violet à dents dorées, caisses, coffre, tapis violet, lanternes.
- **Vendeur d'armures** : plusieurs mannequins d'armures de styles différents (chevalier en plates d'argent,
  soldat plus simple, armure lourde d'acier sombre, armure d'apparat dorée), heaumes de formes variées sur les
  étagères, cuirasses, grand bouclier bleu à l'aigle d'or devant, coffres et caisses, tapis bleu, lanternes.

**Meubles des mods** : chaque générateur pose ses meubles (caisses, tonneaux, étagères, lanternes, livres...)
par `Decor` (`interiors/<id>_decor.json`) : le bloc du mod s'il est installé, sinon le bloc vanilla indiqué, sinon
une boîte de substitution ; ids vérifiés dans le catalogue des mods. Les armes, armures, bâtons, instruments et
fusils n'existent dans les mods que comme objets (pas comme blocs) : ils sont modélisés dans la tente.

**Pour les développeurs** (ajouts rétrocompatibles de `merchantlib.py`, les six tentes de la 1.14.0 se
régénèrent à l'identique) : couleurs `burgundy`, `darkred`, `navy`, `charcoal` ; emblèmes `lyre`, `muskets`, `bow`,
`star`, `shield` (et `cannon`, inutilisé) ; `Atlas(id, colour, banner_colour=..., rug_colour=...)` pour une bannière
(et le drapeau, les fanions) ou un tapis d'une autre couleur que la toile ; `pavilion(..., roof_rise=2.2)` pour un
toit plus bas (hauteur du sommet au-dessus des avant-toits, 3,2 par défaut).

**Limites connues / non vérifié** :

- Le test en jeu (`TentGameTest`) pose aussi ces cinq tentes une fois chacune (emprise vérifiée dans la plateforme
  dégagée) ; son passage en CI n'est pas garanti au moment de l'écriture.
- Le rendu réel des meubles des mods n'est visible que dans la variante « decor » du test en jeu.
- Les PNJ EasyNPC ne sont pas fournis : la place est prévue, le PNJ se pose à la main.

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
  d'écran, `/tent remove`, bloc et collisions disparus), puis chacune des onze autres tentes une fois (les cinq
  autres tentes de camp et, depuis 1.14.0, les six tentes de marchands, dont l'emprise est d'abord vérifiée dans la
  plateforme dégagée) : posée, bloc, orientation, entité de bloc, une requête de collision sur sa première boîte
  pleine, une capture d'écran, retirée par `/tent remove x y z`.
- JUnit `MerchantTest` (1.14.0) : les six tentes de marchands dans `TentTypes.ALL` et `MERCHANTS`, groupe
  `tents`, noms courts (`/tent place armurier`), emprises à l'échelle, boîtes de collision dans l'emprise, quatre
  poteaux pleins, entrée libre, fichiers (langues, blockstate, objet, icône, modèle, atlas), modèles chargés.
- JUnit `Merchant2Test` (1.15.0) : les cinq tentes de `MERCHANTS2` après les douze premières, mêmes vérifications,
  plus une place libre de 1 × 1 × 2,2 blocs pour un PNJ, rien de solide sur le tapis, aucune particule ; le test en
  jeu pose désormais les seize autres tentes (les cinq de la 1.15.0 comprises).

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
