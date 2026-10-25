# Le Léviathan des Cieux (`sky_leviathan`) — plan, animations et guide du joueur

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

## 5. Phase 3 : animations et effets

Tout ce qui bouge est un **petit os animé** du modèle (`tools/generate_leviathan.py`, `build_animations`) ;
le reste (ballon, coque, ponts, pièces, meubles, tour, suspentes) est dessiné depuis le cache statique du
moteur de rendu (calculé une fois, recopié à chaque image) : moins de 15 % des faces sont animées
(vérifié par `LeviathanAnimationTest`). Tout part de l'état synchronisé de l'entité : chaque joueur voit
la même chose.

| Élément | Mouvement | Piloté par | Os |
|---|---|---|---|
| Ailerons de gouvernail (dorsal, bas) | braquent de ±10° | la barre (`steer`) | `fin_dorsal`, `fin_lower` (+ roue `helm_wheel`, safran `rudder`) |
| Ailerons de profondeur (latéraux) | braquent de ±8° | la montée / descente (`elevator`) | `fin_side_p`, `fin_side_s` |
| Tous les ailerons de queue | léger frémissement (±1°) en permanence | le temps (`streamer_wave`) | `fin_*` |
| Voiles noires | respirent (le creux se gonfle et se relâche de ±22 % autour de la vergue : les écoutes restent amarrées au bastingage) et se balancent un peu | le temps | `black_sail_*` |
| Pavillon pirate | ondule (deux moitiés) | le temps (`flag_wave`) | `flag`, `flag_tip` |
| Banderoles déchirées, guirlandes de fanions, draperies noires du ballon | se balancent légèrement (les draperies autour de leurs deux nœuds, ±1,1°) | le temps | `pennants_*`, `swag_*` |
| Lanternes suspendues | se balancent | le temps (`lantern_sway`) | `lantern_*` |
| Grands engrenages de la tour et leurs pignons, volant et trains d'engrenages de la salle des machines | tournent dans leur plan, engrenés (pignons plus rapides, en sens inverse), en avant ou en arrière, plus vite avec la vitesse ; boucle sans à-coup | la phase de la machine (`engine`) | `tower_gear_*`, `tower_pinion_*`, `engine_gear_*` |
| Pistons | une course par tour de volant, manivelles décalées d'un demi-tour | la phase de la machine | `engine_piston_*` |
| Chaudière et machine | vibrent (±0,012 bloc, rapide et irrégulier) | la phase de la machine | `engine_boiler` |
| Tout le vaisseau | flotte : monte et descend lentement de ±0,07 bloc (deux battements, période ≈ 7 s) | le temps | dessin seulement (`ShipModels.Visual.hover`) |

La **phase de la machine** n'avance qu'avec la vitesse (en arrière en marche arrière) : vaisseau garé,
engrenages et pistons sont immobiles et la chaudière ne vibre plus.

**Vapeur et sons** (`LeviathanEffects`, client seulement, à moins de 96 blocs du joueur, quelques particules
par tick, sons vanilla). La machine **tourne** quand le vaisseau avance ou change d'altitude, ou quand
quelqu'un (ou le pilote automatique) tient la barre ; garée, elle est froide.

* Machine froide : seulement un filet de vapeur, de temps en temps, à la soupape de sûreté de la chaudière
  (gardée chaude), et le craquement des membrures et des cordages dans le vent.
* Machine en marche : bouffées de vapeur à la soupape du dôme de la chaudière, jets aux vannes de ses deux
  conduites (avec leur sifflement), vapeur aux deux tuyaux de la tour qui entrent dans le ballon, vapeur et
  un peu de fumée aux évents d'échappement des deux flancs au-dessus de la salle des machines (la planche ne
  montre aucune cheminée extérieure : la chaudière s'échappe par ces évents) ; battement des pistons
  (piston qui sort / qui rentre), cliquetis des engrenages, grondement du foyer ; tout est plus rapide et
  plus fort avec la vitesse. Les sons de la salle des machines s'entendent à moins de 28 blocs.

## 6. Guide du joueur

### Obtenir et poser le vaisseau

* Objet *Le Léviathan des Cieux* dans l'inventaire créatif (onglet *Navires médiévaux*), ou
  `/ship give sky_leviathan [joueurs]` (administrateurs). Aucune apparition naturelle.
* **Clic droit sur le sol, l'eau ou un toit** : le vaisseau apparaît au-dessus, en vol stationnaire,
  seulement si **toute** sa place est libre (environ 67 blocs de long, 25 de large, 48 de haut :
  ballon, ailerons, navire suspendu, aileron ventral, mât du pavillon) et sous le plafond `maxAltitude`.
  Sinon un message l'indique et rien n'est posé. `/ship spawn sky_leviathan` le fait apparaître au-dessus
  de votre position, proue dans votre direction.
* Récupérer : accroupi + clic gauche sur le vaisseau (administrateurs) ; `/ship remove` le supprime.

### Monter à bord, marcher, portes, échelles, sièges

* **Clic droit sur la coque** : on est déposé sur le pont principal. On marche librement sur les ponts
  ouverts (pont principal, gaillard d'avant, château arrière, dunette, pont d'observation au sommet du
  ballon) **et dans toutes les pièces**, pendant le vol : on suit le vaisseau, on ne tombe pas, on ne
  traverse ni les murs, ni les planchers, ni la coque.
* **Portes et trappes** : clic droit pour ouvrir / fermer (portes animées, à un ou deux battants) :
  tour (0), trappe du pont d'observation (1), cabine du capitaine (2), chambre (3), salle des cartes (4),
  magasin avant (5), salle commune (6), poste d'équipage (7), cambuse (8), salle des machines (9),
  trappe de la cale (11). L'état des portes est sauvegardé.
* **Escaliers** entre les niveaux (marches de 0,5 bloc) ; **échelles** : dans la tour (du pont principal
  jusqu'au pont d'observation, 28 blocs : sauter sur l'échelle puis avancer) et vers la cale.
* **Sièges** : clic droit sur un banc, une chaise, un tabouret ou un fauteuil (26 places : salle commune,
  pont, cabine, salle des cartes, poste d'équipage, cambuse, salle des machines…) ; Maj pour se lever (on
  se relève à côté du siège).

### Piloter

**Prendre la barre** : clic droit sur la roue, sur le château arrière (le pilote se tient debout derrière
la roue). Touches (ce sont celles de déplacement de Minecraft, changeables dans *Options → Commandes*) :

| Action | Touche (AZERTY) |
|---|---|
| Avancer (prendre de la vitesse) | Z |
| Ralentir, puis reculer | S |
| Tourner à bâbord / tribord | Q / D |
| **Monter** | Espace |
| **Descendre** | Ctrl |
| Quitter la barre | Maj |

Relâchées, Espace et Ctrl laissent le vaisseau **garder son altitude** (il ne tombe pas). C'est un très
grand vaisseau lourd : il met longtemps à prendre son erre et à s'arrêter, vire large, monte et descend
progressivement, se stabilise seul. Il ne traverse ni le relief, ni les arbres, ni les bâtiments. La barre
d'action affiche l'altitude, la montée / descente et la vitesse.

### Pilote automatique (itinéraires aériens)

Comme le dirigeable steampunk (détails dans [COMMANDES.md](COMMANDES.md), *Itinéraires aériens*) :

```
/ship route create <nom> [pingpong|loop|once] air      # itinéraire aérien
/ship route addstop <nom> [secondes] [nom de l'escale] # placez-vous là où doit être le pont principal
/ship route addpoint <nom>                             # point de passage en 3D
/ship route edit <nom> <n°> altitude <y> | speed <blocs/s> | wait <secondes> | yaw <degrés>|here | clear
/ship route assign <nom>                                # près du vaisseau : décolle et suit l'itinéraire
/ship route depart | /ship ai enable | /ship ai disable | /ship route show <nom> | /ship info
```

Il décolle, monte à l'altitude de croisière (toujours au moins `aiClearance` = 8 blocs sous la quille
au-dessus du relief, des arbres et des bâtiments), anticipe les virages, ralentit, descend à l'escale dans
les `aiApproachDistance` = 48 derniers blocs, s'arrête, attend, se tourne vers le cap de l'escale et repart.
Les itinéraires sont sauvegardés dans le monde.

### Réglages (`config/medievalships.json`, bloc `ships.sky_leviathan`, `/ship reload`)

| Clé | Défaut | Rôle |
|---|---|---|
| `slowSpeed` / `normalSpeed` / `fastSpeed` | 2 / 4.2 / 6.8 | allures (blocs/s) |
| `reverseSpeed` | 1.2 | marche arrière |
| `acceleration`, `braking`, `waterDrag` | 0.3, 0.6, 0.15 | blocs/s² ; perte de vitesse en roue libre (forte inertie) |
| `maxTurnRate`, `minTurnFactor` | 6.5, 0.5 | rotation maximale (°/s), part disponible à l'arrêt (vire sur place lentement) |
| `helmRate`, `helmReturnRate`, `turnResponse`, `turnSpeedLoss` | 0.8, 0.8, 0.5, 0.08 | barre, inertie de rotation, ralentissement en virage |
| `waveRocking` | 0.5 | balancement visuel (0 = aucun) |
| `aiWaypointRadius`, `aiStopRadius`, `aiLookahead`, `aiProbeDistance` | 16, 4, 36, 80 | pilote automatique : rayons, anticipation, portée de détection |
| `aiDefaultWaitSeconds`, `aiStuckSeconds`, `aiTurnAroundSpeed` | 300, 12, 0.5 | attente par défaut aux escales, détection de blocage, vitesse en demi-tour |
| `flight.climbSpeed` / `flight.descendSpeed` | 1.2 / 1.0 | montée et descente (blocs/s) |
| `flight.verticalAcceleration` | 0.45 | changements d'altitude progressifs (blocs/s²) |
| `flight.maxAltitude` | 300 | plafond : le haut du vaisseau ne le dépasse jamais |
| `flight.aiClearance`, `flight.aiApproachDistance`, `flight.aiLandingClearance` | 8, 48, 2 | pilote automatique : hauteur au-dessus du relief, distance de descente vers une escale, hauteur gardée en descendant |
| `flight.sway` | 0.6 | balancement visuel (0 = aucun) |

### Mobilier et modèles

* **Mobilier des mods de décoration** : voir le tableau de la section 4 (pièce par pièce). Ils sont
  facultatifs : un mod absent est remplacé par une boîte de même taille. Aucun fichier des mods n'est copié.
* **Modèles faits pour le vaisseau** (dans son modèle Blockbench `blockbench/sky_leviathan.bbmodel`,
  générés par `tools/leviathan_furniture.py` et `tools/generate_leviathan.py`) : la grande chaudière rivetée
  (nervures dorées, trappe à rayons, foyers rougeoyants, manomètres, ballons latéraux, cheminée), la machine
  à pistons et son volant, les trains d'engrenages muraux, les conduites, vannes, réservoirs, tableaux de
  manomètres et banc de leviers, la passerelle et ses garde-corps ; les tonneaux couchés sur berceau et
  debout, les coffres de marin, étagères de bocaux et bouteilles, sacs, rouleaux de cordage ; les tapis
  rouges, couvertures rouges des lits, cartes, instruments (compas, sextant, compas à pointes, sablier,
  globe, longue-vue), potences et poteaux de lanternes, cadres des tableaux, hublots et fenêtres vus de
  l'intérieur, membrures. Dehors : roue de barre, safran, cabestan, roue du pont d'observation, lanternes,
  engrenages de la tour, ailerons, pavillon.

### Captures

* Comparaison planche / jeu (variante avec les mods de décoration) :
  [comparaison_sky_leviathan.png](comparaison_sky_leviathan.png) — côté, perspective, avant, arrière,
  dessus, détails / ailerons ; pont principal, salle commune, cabine du capitaine, cale, coursive, salle des
  machines. Refaite par `python3 tools/leviathan_compare.py <planche de référence> <dossier des captures>`
  (captures `*_solo_sky_leviathan_*.png` de la branche `test-results-decor`).
* Prises de vue du test en jeu (`LeviathanGameTest`, branche `test-results-<variante>-<branche>`) :
  `1_cote` … `5_perspective`, `18_ballon`, `19_ailerons`, `20_coque_suspendue`, `21_ailerons_en_virage`
  (en virage et en montée, depuis une caméra derrière la queue), `6_pont`, `7_cabine`, `8_pont_superieur`,
  `9_salle_commune` … `17_salle_machines_arriere`, `22_salle_machines_en_marche`.

### À bord pendant les virages et les montées

* Sur un client, la coque suit le serveur sans le glissement vanilla de trois ticks (`followsServerExactly`) :
  le pont où l'on marche est où le serveur l'a (à un tick près), au lieu d'environ quatre ticks de retard ;
  son cap est le cap précis synchronisé (le cap des paquets, arrondi à 1,4°, faisait osciller la coque de
  quelques dixièmes de degré). En descendant de la barre pendant une montée, le pilote se pose sur la
  dunette au lieu de 0,15 bloc sous le pont du serveur.
* Les cellules de la coque sont données au moteur de collision comme des boîtes alignées sur le monde
  couvrant chaque cellule tournée : quand le vaisseau tourne, elles changent de forme, et un joueur appuyé
  contre une paroi pouvait s'y retrouver d'un centième de bloc ; la règle vanilla ignore une boîte déjà
  chevauchée, et il traversait la paroi (dans le puits de la tour, après un virage : chute sur le pont
  principal). Une boîte chevauchée de moins de 0,1 bloc est maintenant rognée de son côté et l'arrête
  toujours (`HullContact`, pour tous les vaisseaux ; testé par `HullContactTest`).

### Limites connues

* Le flottement est seulement dessiné (±0,07 bloc) : les collisions et les joueurs à bord ne le suivent pas,
  d'où, au plus, un écart de quelques centièmes de bloc entre les pieds et le pont.
* La machine tourne avec la vitesse horizontale : en vol stationnaire, ou pendant une montée sur place, les
  engrenages et les pistons sont immobiles (la vapeur et le battement continuent tant que quelqu'un tient la
  barre).
* La planche n'est pas cohérente entre ses vues (vue arrière : ailerons d'un seul côté) : disposition
  symétrique, fidèle aux vues de côté et de dessus.
* Les sons sont des sons vanilla (piston, chaîne, haut fourneau, feu éteint, bois) : une approximation
  d'une machine à vapeur.
* De loin, l'intérieur et les meubles ne sont plus dessinés (au-delà de 48 blocs), ni les petits détails
  extérieurs (au-delà de 80 blocs).
* Persistance (position, cap, altitude, vitesse, itinéraire, pilote automatique, portes) : générique au mod
  et vérifiée par les tests unitaires et le test des itinéraires des nouveaux véhicules ; un vrai
  redémarrage de serveur avec ce vaisseau n'a pas été fait à la main.
