# Le Léviathan des Cieux (`sky_leviathan`) — analyse et plan (phase 1)

Planche de référence : `scratchpad/ref/leviathan_ref.png` (vues de côté, avant, arrière, dessus,
perspective, détails, six vues intérieures). Comparaisons rendu / référence : voir le rapport.

## 1. Mesures sur la planche (vue de côté, 1536 × 1024)

Échelle retenue : **0,07 bloc par pixel** de la vue de côté (65 blocs de la pointe avant à la pointe
arrière, comme le cahier des charges).

| Élément | Pixels (vue de côté) | Blocs |
|---|---|---|
| Ballon (nez → fin de l'enveloppe) | x 100 → 838 | **52** |
| Ballon, hauteur | y 145 → 425 | **19,6** |
| Ballon, largeur (vue avant, rapport L/H ≈ 1,3) | — | **24,4** (sections elliptiques, un peu aplaties) |
| Cerclages en bois | x 160, 255, 705, 785 | z = 21, 14,35, −17,15, −22,75 |
| Grands panneaux de bois des flancs | entre les deux cerclages du milieu, y 190 → 395 | azimut 45° → 142° |
| Nez : ferrure à engrenage + pointe | x 0 → 100 | jusqu'à z = 32,2 |
| Queue : moyeu + pointe | x 838 → 935 | jusqu'à z = −33,2 |
| Navire suspendu (coque) | x 165 → 745 | **35,8** (41 avec l'éperon, 45 avec le beaupré), 10 de large |
| Pont principal / quille | y 540 / 630 | 0 / −6,3 |
| Gaillard d'avant, dunette, château arrière | y 497 / 490 / 455 | +3,0 / +3,0 / +5,5 |
| Espace ballon → pont | y 425 → 540 | 8 blocs |
| Mât du pavillon (sommet) | y 18 | +36,8 |
| Aileron ventral (pointe) | (465, 705) | y −11,55 |

Proportions : longueur totale 65 (67 avec les ailerons latéraux), hauteur totale 48 (pavillon
compris). Le ballon est un **œuf** : sections `(1 − t^a)^b` (avant a = 2,6, b = 0,55 ; arrière
a = 2,4, b = 0,6), plus effilé vers l'arrière, le plus large au milieu.

Ailerons noirs « aile de chauve-souris » (bord d'attaque bombé, bord de fuite festonné entre les
nervures, trois trous près de la pointe, pique en emblème) : un dorsal sur le ballon, deux hauts
(±30°), deux latéraux (±115°), un bas, au moyeu de queue ; un ventral sous la quille. Le dorsal et
le bas servent de gouvernail (`steer`), les latéraux de profondeur (`elevator`). La planche n'est pas
cohérente d'une vue à l'autre (vue arrière : ailerons d'un seul côté) : disposition symétrique
retenue, qui reproduit la silhouette des vues de côté et de dessus.

## 2. Niveaux et pièces (coordonnées du navire : y = 0 au pont principal, +z = proue)

| Niveau | Pièces |
|---|---|
| Pont d'observation (y 28, sur le ballon) | plancher arrondi de 24 × 11, garde-corps, mât et pavillon pirate, roue décorative, cabestan, trappe |
| Dunette (y 5,5) | garde-corps, lanternes de poupe |
| Château arrière (y 3) | **barre** (pilote debout derrière la roue, z −11,6), escaliers ; sous la dunette : **salle des cartes** (y 3 → 5) |
| Pont principal (y 0) | pont ouvert entre les châteaux, **tour centrale** (échelle intérieure jusqu'au pont d'observation, grand engrenage), descente vers la salle commune, bancs ; sous le château arrière : **cabine du capitaine** (bureau + chambre, porte double) ; sous le gaillard : **magasin du maître d'équipage** |
| Pont inférieur (y −3) | **salle commune** (grande table, bancs), **coursive** (tapis rouge) avec **poste d'équipage** et **cambuse** de chaque côté, porte vers la salle des machines |
| Cale (y −5,5) | **cale / stockage** sur toute la longueur, échelle et trappe vers la coursive |
| Salle des machines (y −5 → −0,5, sur deux niveaux) | palier au niveau du pont inférieur, escalier, **chaudière** avec cheminée, manomètres, volant, pistons et engrenage animés |

Portes (grille) : 0 tour, 1 trappe du pont d'observation, 2 cabine du capitaine, 3 chambre,
4 salle des cartes, 5 magasin avant, 6 salle commune, 7 poste d'équipage, 8 cambuse,
9 salle des machines, 11 trappe de la cale. Escaliers de 0,5 bloc ; échelles : tour (28 blocs) et cale.

Tout est dans la grille intérieure (cellules de 0,5 bloc, `tools/leviathan_interior.py`) : le ballon
y est plein, les ponts ouverts sont « dehors » mais portés (on y marche pendant le vol), les murs,
planchers et plafonds des pièces sont dessinés sur les limites des cellules. Les pièces sont
séparées du dehors par au moins une cellule pleine sur chacune de leurs six faces (aussi au tableau
arrière, à l'étrave et sous le bouchain), sauf la descente du pont principal et le puits de la tour :
aucune pièce ne s'ouvre sur le vide (`LeviathanTest.noWayOut`).

## 3. Vol et pilote automatique

Physique `Flight` du dirigeable steampunk, réglages d'un très grand vaisseau lourd : 2 / 4,2 /
6,8 blocs/s, accélération 0,3, virage max 6,5°/s, montée 1,2 et descente 1,0 bloc/s avec une
accélération verticale de 0,45 (changements d'altitude progressifs), marge de 8 blocs au-dessus
du relief pour le pilote automatique (itinéraires `air`), approche des escales à 48 blocs.

## 4. Phase 2 : aménagement des pièces

Tout est dans `tools/leviathan_decor.py` (placement, pièce par pièce, d'après les six vues intérieures
de la planche), `tools/leviathan_furniture.py` (meubles faits pour le vaisseau, quand aucun mod n'a
l'équivalent) et `tools/leviathan_texture.py` (seconde texture `sky_leviathan_interior.png` : lambris,
planchers, plafonds, tôle rivetée et suie de la salle des machines, tapis, cartes, livres, bocaux…).
Les blocs des mods sont dessinés par le vaisseau là où ils se trouvent (jamais posés dans le monde, aucun
fichier des mods copié, seulement leurs identifiants) ; leur emprise est pleine dans la grille
intérieure (sauf chaises, bancs et petits objets) ; si un mod manque, une boîte de même taille le
remplace (os `fallback_<i>`, les lanternes restent lumineuses). 197 blocs de mods, 26 places assises
(chacune avec son point pour se relever) ; portes, escaliers, échelles, coursive et accès à la
passerelle de la salle des machines restent dégagés (vérifié par script et par `LeviathanTest`).

Mods : Farmhouse Decorations (`farmhouse_decorations`), Furnish (`furnish`), Farmer's Delight
(`farmersdelight`), Lands of Icaria (`landsoficaria`), Mebahel Dwarven Automatons
(`mebahelcreaturesdwarven`).

| Pièce | Meubles des mods réutilisés | Pièces faites pour le vaisseau |
|---|---|---|
| **Salle commune** | grande table `farmhouse_decorations:dining_table_side` (aux deux bouts, pieds tournés) + `dining_table_middle` (2 × 4 blocs, pieds aux bouts seulement), 8 bancs `furnish:dark_oak_bench`, 4 `farmhouse_decorations:dining_chair` aux bouts ; sur la table `furnish:plate`, `farmersdelight:roast_chicken_block`, `farmersdelight:honey_glazed_ham_block`, `wine_bottle`, `red_wine_bottle`, `wine_glass`, `kerosene_lantern` ; bar : `liquor_cabinet`, `kitchen_wall_shelf`, 2 tonneaux en perce couchés sur leur berceau (faits pour le vaisseau) ; `wall_shelf`, `dresser`, `pile_of_books` ; table de jeu `furnish:spruce_square_table` + `furnish:chess_board` + `spruce_stool` ; 3 `chained_kerosene_lantern` au-dessus de la table | tapis rouge, étagères de bocaux et bouteilles, hublots, coffre de marin, bougies, cadres des tableaux (vanilla `bust`, `burning_skull`, `sea`), potences de lanternes, membrures (poteaux, baux, courbes) |
| **Cabine du capitaine** (bureau + chambre) | `farmhouse_decorations:desk` et fauteuil `furnish:dark_oak_chair`, 6 `tall_bookshelf`, bureau tourné vers la porte (le capitaine assis côté genoux), table à cartes en 2 `dining_table_side`, `furnish:spruce_chair`, `cigar_box`, `furnish:book_pile`, `cuckoo_clock` ; chambre : `double_bed`, `night_stand`, table à écrire en 2 `dining_table_side`, `wardrobe`, `dresser`, `dining_chair`, `pile_of_books`, lanternes `kerosene_lantern` / `chained_kerosene_lantern` | couverture rouge du lit, cartes, encrier, compas, sextant, compas à pointes, cartes roulées, sablier, globe (Nautilus), coffres sous les tables et au pied du lit, fenêtres vues de l'intérieur (flancs et poupe), tapis, tableaux (`wanderer`, `skull_and_roses`, `sea`) |
| **Salle des cartes** | table de 2 `farmhouse_decorations:dining_table_side`, 2 `furnish:spruce_stool`, 4 `tall_bookshelf`, `farmersdelight:wooden_basket` de cartes roulées, lanternes | grande carte, instruments, longue-vue (Nautilus), cartes murales, fenêtres de poupe |
| **Pont principal** | caisses `furnish:spruce_crate` / `dark_oak_crate`, table du navigateur `furnish:dark_oak_square_table`, 4 bancs `furnish:dark_oak_bench`, lanternes `chained_kerosene_lantern` | tonneaux, rouleaux de cordage, poteaux à lanterne, compas, sextant, carte roulée, coffre sur le château arrière |
| **Magasin du maître d'équipage** | `spruce_crate`, `dark_oak_crate` (aussi empilées dans l'angle de l'avant), `farmersdelight:potato_crate`, `farmersdelight:rice_bag`, `workbench` + `tool_board`, second `tool_board` sur la cloison avant, lanternes | tonneaux (dont deux à l'avant), étagères de bocaux et bouteilles sur les deux murs, coffre de marin, cordages, sacs, membrures |
| **Coursive** | `night_stand` + `kerosene_lantern`, petite `spruce_crate`, lanternes sur potences et suspendues | long tapis rouge, potences, cadres (`wanderer`, `kebab`), membrures |
| **Poste d'équipage** | 2 `single_bed` (sous une couverture rouge faite pour le vaisseau), `furnish:spruce_square_table`, 2 `spruce_stool`, `acoustic_guitar`, `red_wine_bottle`, lanternes | coffres de marin, hublots |
| **Cambuse** | `farmersdelight:stove` + `cooking_pot`, `kitchen_counter` + `cutting_board` + `skillet`, `kitchen_wall_shelf`, `seasoning_rack`, `carrot_crate`, `cabbage_crate`, `onion_crate`, `rice_bag`, `wooden_basket`, tabouret | tonneau en perce couché sur son berceau, sac, hublots |
| **Cale / stockage** | `workbench` + `tool_board` + `cutting_board` + lanterne, caisses `furnish`, `potato_crate`, `carrot_crate`, `beetroot_crate`, `cabbage_crate`, `rice_bag`, `straw_bale`, coffre au trésor `mebahelcreaturesdwarven:dwemer_chest`, `landsoficaria:storage_vase` | 3 tonneaux couchés sur berceaux, séparés, couvercles et robinets vers l'allée, tonneaux debout, étagères de bocaux, coffres, sac, lanternes sur potences, poteaux et baux |
| **Salle des machines** | conduites et engrenages de bronze `mebahelcreaturesdwarven:dwemer_metal_pipe_gear`, `dwemer_metal_pipe`, `dwemer_metal_block` ; caisses `furnish` (côté bâbord du palier : le côté tribord reste libre pour monter sur la passerelle), établi `workbench` + `tool_board`, lanternes chaudes | **grande chaudière rivetée** (nervures dorées, trappe ronde à rayons sur un collier riveté qui épouse la virole, deux foyers rougeoyants, manomètres, ballons latéraux, cheminée cerclée), tuyauteries vers les murs avec vannes, collecteurs de vapeur sous le plafond, réservoirs sous pression, tableaux de manomètres, banc de leviers, tas de charbon, garde-corps du palier / de l'escalier / de la passerelle, **pistons et volant animés**, trains d'engrenages muraux animés |

Prises de vue en jeu (`LeviathanGameTest`) : `9_salle_commune` à `16_pont_principal`, depuis les points de
vue des vues intérieures de la planche.

## 5. Reste à faire (phase 3)

Sons et vapeur de la salle des machines, cordages animés, vérification en jeu de la persistance après
redémarrage.
