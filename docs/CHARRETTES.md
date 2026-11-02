# Charrettes médiévales (un bloc = une charrette)

Huit charrettes de décor pour les villages, marchés, fermes, camps de bûcherons, routes et zones de quête.
**Chaque charrette est UN seul bloc**, exactement comme les [tentes](TENTES.md) : on pose le bloc, la charrette
entière (roues à rayons, essieux, plateau, ridelles, brancards, bâche, chargement, lanternes) est dessinée à partir
de lui. Elles sont **statiques** : pas de déplacement, pas d'IA, pas d'animation, pas d'apparition naturelle, rien
ne « tick ».

| id | nom | emprise (l × h × p, blocs) | cubes | boîtes de collision | générateur |
|----|-----|-----|-----|-----|-----|
| `cart_covered_white` | Charrette couverte blanche (White Covered Wagon) | 3,0 × 3,3 × 6,0 | 431 | 15 | `tools/carts/generate_cart_covered_white.py` |
| `cart_hay` | Charrette de foin (Hay Cart) | 3,1 × 2,1 × 5,6 | 276 | 11 | `tools/carts/generate_cart_hay.py` |
| `cart_merchant_wagon` | Roulotte de marchand (Merchant Wagon) | 2,9 × 3,2 × 4,6 | 323 | 11 | `tools/carts/generate_cart_merchant_wagon.py` |
| `cart_market` | Charrette de marché (Market Cart) | 3,6 × 2,9 × 5,1 | 293 | 33 | `tools/carts/generate_cart_market.py` |
| `cart_logs` | Charrette de bûcheron (Log Cart) | 3,0 × 2,6 × 5,7 | 239 | 10 | `tools/carts/generate_cart_logs.py` |
| `cart_open` | Charrette de transport (Open Cart) | 2,7 × 1,8 × 4,8 | 110 | 7 | `tools/carts/generate_cart_open.py` |
| `cart_covered_teal` | Charrette couverte turquoise (Teal Covered Wagon) | 2,6 × 2,9 × 4,3 | 371 | 14 | `tools/carts/generate_cart_covered_teal.py` |
| `cart_barrels` | Charrette à tonneaux (Barrel Cart) | 2,8 × 2,2 × 4,6 | 280 | 11 | `tools/carts/generate_cart_barrels.py` |

Objets : `medievalships:cart_covered_white`, `medievalships:cart_hay`, `medievalships:cart_merchant_wagon`,
`medievalships:cart_market`, `medievalships:cart_logs`, `medievalships:cart_open`,
`medievalships:cart_covered_teal`, `medievalships:cart_barrels` — tous dans l'onglet créatif **Charrettes**
(séparé des vaisseaux et des tentes).

L'emprise est mesurée autour du bloc d'ancrage (la profondeur compte le timon / les brancards devant). Les roues
touchent le sol du bloc d'ancrage : rien ne flotte ni ne s'enfonce.

- **Charrette couverte blanche** : grand chariot à quatre roues à rayons, bâche blanche arrondie sur arceaux
  (coutures, jupe), banc et chargement visibles à l'intérieur, deux lanternes à l'ouverture avant, timon.
- **Charrette de foin** : quatre roues (celles de l'avant plus petites), ridelles basses à barreaux et ferrures,
  deux couches de bottes de foin cordées, un tonneau cerclé et un sac à l'avant, timon.
- **Roulotte de marchand** : petite maison sur roues, parois de planches rouge sombre à pilastres dorés, toit rouge
  bombé, fenêtres à volets rouges, jardinières fleuries, porte, lanternes, marches à l'arrière.
- **Charrette de marché** : plateau à quatre roues, auvent rayé rouge et blanc sur six poteaux, cagettes de fruits
  et légumes, une lanterne, un tonneau et une caisse à côté.
- **Charrette de bûcheron** : plateau robuste, pile de neuf rondins (4 / 3 / 2, écorce et cernes en bout) sanglés
  par deux cordes.
- **Charrette de transport** : charrette ouverte à ridelles en barrières de bois, plancher de planches, deux grandes
  roues à rayons, brancards sur béquille.
- **Charrette couverte turquoise** : petit chariot à bâche turquoise arrondie bordée d'or (frange), paroi avant à
  porte, lanterne à l'ouverture, quatre roues, timon.
- **Charrette à tonneaux** : deux grandes roues, deux gros tonneaux cerclés de fer debout, lanterne sur poteau au
  coin avant, montants arrière hauts, brancards.

Depuis 1.19.0 l'onglet **Charrettes** contient aussi, en dernier, une neuvième « charrette » bien plus grande : la
**[taverne nomade](TAVERNE.md)** (`taverne_nomade`, environ 13 x 10 blocs : roulotte-taverne à comptoir, terrasse,
tables, tabourets, feu de camp et chaudron), même bloc et mêmes commandes que les autres, et sur laquelle **on peut
s'asseoir** (clic droit sur un tabouret, Maj pour se lever).

## Poser, orienter, retirer

- **Poser** : clic droit au sol avec l'objet. L'avant de la charrette (timon / brancards) fait face au joueur (état
  de bloc `facing`, quatre directions : le modèle et les boîtes de collision tournent d'un quart de tour avec lui).
- **Vérification de place** : avant de poser, le jeu vérifie que toute l'emprise de la charrette (tournée selon
  l'orientation) est libre — air, herbes, fleurs, neige, plantes remplaçables — et que le sol est assez plein
  dessous ; sinon un message rouge en français (ce qui gêne, et où) et rien n'est posé. Une charrette n'écrase
  **jamais** une construction existante. C'est le même code que pour les tentes.
- **Retirer** : casser le bloc d'ancrage (au sol, au centre de la charrette : visez-le, son contour est un bloc
  entier ; bruit de bois). En survie il rend l'objet. Ou `/cart remove`. Rien d'autre à nettoyer.
- **Collisions** : roues, plateau, ridelles, caisse de la roulotte, tonneaux et cargaison pleine ont des boîtes de
  collision statiques (7 à 33 par charrette) ; le timon et les brancards n'en ont pas, on les enjambe (vérifié par
  JUnit pour la charrette de transport, de foin, de bûcheron et à tonneaux). Même chemin
  que les tentes : `EntityCollisionMixin` → `ShipCollisions.withHulls` → `TentCollisions`.
- **Persistance** : c'est un bloc avec son entité de bloc, dans le chunk. Multijoueur et serveur dédié : rien de
  spécial ; le rendu est côté client, le serveur ne garde que l'orientation et les boîtes de collision (remplies au
  chargement du chunk, oubliées à son déchargement).

## Commandes (admin, mêmes permissions que `/ship`)

`/cart` est un alias de `/tent` : les deux acceptent les ids des tentes, des charrettes et (depuis 1.13.0) des
[ateliers](ATELIERS.md).

- `/cart give <id> [joueurs]` — donne l'objet (`/tent give <id>` et `/ship give <id>` marchent aussi).
- `/cart place <id> [x y z] [south|west|north|east]` — pose la charrette à la position (ou celle de l'exécutant),
  l'avant vers la direction donnée (ou vers l'exécutant). Même vérification de place libre que l'objet.
- `/cart remove [nearest|x y z]` — retire la charrette (ou tente) la plus proche, ou celle dont l'ancrage est en x y z.
- `/cart list` — les tentes et charrettes chargées de ce monde, de la plus proche à la plus lointaine.
- `/cart types` — les vingt et un ids (six tentes, huit charrettes, sept ateliers).

## Modèles et textures

Vrais modèles 3D générés en Python (`tools/carts/`), sur la base des outils des tentes :

- `cartlib.py` : roues à rayons (jante en anneau de segments inclinés, moyeu, 8 à 12 rayons), essieux, plateau,
  ridelles, brancards sur béquille, timon, bâche arrondie lissée sur arceaux, toit bombé, lanterne sur poteau,
  tonneaux, rondins, bottes de foin, cageots, icônes, export ;
- `cart_frame.py` : châssis lourd (roues par essieu, longerons, ferrures), tonneau cerclé, rondin à 12 pans, cordes ;
- `cart_texture.py` : l'atlas partagé `textures/entity/carts.png` (bois clair et sombre, fer, toile blanche et
  turquoise, bois rouge, liseré doré, auvent rayé, foin, écorce et cernes, tonneau, fruits et légumes) ;
- `generate_cart_<id>.py` : un par charrette ; écrit le modèle (`blockbench/` + `models/entity/<id>.bbmodel`),
  `carts/<id>.json` (emprise + boîtes de collision, lus par `TentType` famille `carts`) et l'icône.

Les lanternes sont dessinées en pleine lumière (`glow`), sans source de lumière dans le monde. Le chargement est
modélisé dans le modèle de chaque charrette (pas de blocs de mods de décoration) : rien ne manque jamais, même sans
mods sur le client.

## Performances

- **Aucun tick** : l'entité de bloc n'a pas de ticker, pas de particules, pas d'animation ; le serveur ne fait rien
  pour une charrette posée hormis ses boîtes de collision statiques (par chunk, consultées seulement pour les
  entités qui bougent dans l'emprise).
- **Rendu** : le même `TentBlockEntityRenderer` que les tentes (chemin statique `BbModel.renderStatic`, matrices en
  cache), avec l'atlas des charrettes ; la boîte de rendu est l'emprise, donc le jeu l'élimine hors champ. Modèles
  légers : 110 à 431 cubes (bien sous la limite de ~600), une seule texture partagée par les huit.
- **Niveaux de détail** : les mêmes réglages que les tentes (`config/medievalships.json`, section `server`, lus par
  le client dans son propre fichier) : `tentDecorDistance` (32 blocs) et `tentRenderDistance` (64 blocs) ; au-delà
  de `tentRenderDistance` la charrette n'est plus dessinée.

## WorldEdit, Axiom, structures

Comme les tentes : un bloc avec son état `facing` et une entité de bloc vide. Copier / coller / tourner avec
WorldEdit ou Axiom, ou enregistrer dans une structure, copie la charrette avec son orientation ; les boîtes de
collision se reconstruisent au chargement du chunk.

## Tests faits

- JUnit `CartTest` (les huit fichiers `carts/<id>.json` se chargent à côté des six tentes, famille `carts`, atlas `carts.png`,
  emprises et collisions tournées selon l'orientation, tailles à l'échelle, posées au sol, une roue au sol qui
  collisionne, boîtes dans l'emprise),
  `WagonCartsTest` (les deux charrettes couvertes, la roulotte et la charrette de marché : quatre roues chacune,
  bâches, toit et auvent hauts et pleins, marches à la porte de la roulotte), `CartCargoTest` (foin, rondins, tonneaux : roues, cargaison, brancards sans collision). Avec les
  tests existants : 275 tests JUnit verts sur la branche intégrée.
- Compilation complète et build GitHub (workflow « Build ») verts sur `carts` (1.12.0).
- Test en jeu `CartGameTest` (CI, appelé par `ShipClientGameTest`, variantes vanilla / Lithium / avec les mods de
  décoration) : chacune des huit charrettes une fois, posée par `/cart place` (la première par `/tent place`), bloc,
  orientation (les quatre directions), entité de bloc, une requête de collision sur sa première boîte, une capture
  d'écran, retirée par `/cart remove x y z`, boîtes oubliées.
- Rendus de comparaison référence / modèle des huit charrettes (hors dépôt).

## Non vérifié

- Le résultat du test en jeu sur la branche intégrée au moment de la livraison (il tourne après le build ; il était
  en cours sur les branches `carts-core`, `carts-a` et `carts-b`).
- La pose au clic droit par un vrai joueur et la casse à la main en survie (le test passe par les commandes, même
  code de vérification de place).
- Le passage d'un joueur ou d'un mob contre chaque boîte de collision (seule la première boîte de chaque charrette
  est interrogée en jeu ; les autres sont vérifiées par JUnit).
- Les copies WorldEdit / Axiom (raisonnement ci-dessus, pas d'essai).

## Ajouter une charrette (pour les développeurs)

1. `tools/carts/generate_cart_<nom>.py` sur le modèle des huit existants (aides de `cartlib.py` et `cart_frame.py`).
   Repère : y vers le haut, +z = l'avant (timon), le bloc d'ancrage en (0, 0, 0), roues au sol en y = 0.
2. Lancer le générateur : modèle, `carts/<id>.json`, icône (et l'atlas partagé si `cart_texture.py` a changé).
3. Java : une ligne `cart("<id>", "nom fr", "English name")` dans `core/TentTypes.java` (et dans `CARTS`), les noms
   dans `lang/fr_fr.json` et `lang/en_us.json` (`block.medievalships.<id>`), `blockstates/<id>.json`,
   `items/<id>.json` et `models/item/<id>.json` (copies des existants). Bloc, objet, onglet, commandes, collisions
   et rendu sont génériques.
