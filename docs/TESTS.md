# Tests — ce qui a été vérifié, et ce qui reste à valider en jeu

## Compilation

Le mod est compilé à chaque envoi par GitHub Actions (`./gradlew build`, tâche *Build*) avec
Fabric Loom 1.14, Minecraft 1.21.11, Yarn `1.21.11+build.6`, Fabric API 0.141.6+1.21.11 :
le `.jar` obtenu est celui qui vous est livré.

## Tests dans le vrai jeu (automatiques, GitHub Actions)

La tâche *In-game test* lance un **vrai client Minecraft 1.21.11** avec le `.jar` de
production (mod remappé, comme sur un vrai serveur), deux fois : **sans** et **avec Lithium**.
Chaque fois, tout le scénario est joué **en solo** puis sur un **vrai serveur dédié** auquel le
client se connecte par le réseau (contrôles de mouvement du serveur actifs) : **194 vérifications,
toutes réussies** (version 1.6.0, avec et sans Lithium, en solo et sur serveur dédié).
Le test (`src/gametest/.../ShipClientGameTest.java`) crée un monde, des bassins, met les navires
à l'eau puis vérifie (résultats et captures publiés sur les branches `test-results-vanilla` et
`test-results-lithium`) :

### Nouveaux navires (galère rouge, bateau à roue à vapeur, voilier elfique) — 1.5.0

Le même scénario pour chacun, dans un quatrième bassin (44 × 100 blocs) :

* mise à l'eau par `/ship spawn <type>` ; **il flotte sur sa ligne de flottaison** (eau à
  −58,11 pour une surface à −58) ;
* **six captures comparables à l'image de référence** : côté droit, côté gauche, proue, poupe,
  dessus, perspective (+ pont, navigation, pilote automatique) ;
* chute sur le pont et sauts : le joueur reste sur le pont ;
* **toutes les places occupées** (10, 8 et 8), un passager de plus est refusé ;
* pilotage : il avance (galère rouge 8,7 blocs en 4 s ; bateau à vapeur 4,0 — accélération
  progressive ; voilier 6,3) et vire (26,5° / 16,3° / 11,0° en 3 s), passagers toujours assis ;
* descente du barreur sur le pont ;
* **pilote automatique sur un itinéraire** de deux points : il rejoint le second point (31 → 1,2,
  40 → 0,6 et 33,5 → 1,3 blocs) ;
* `/ship give <type>` donne l'objet.

Les captures sont dans les branches `test-results-*` (fichiers `*_medieval_galley_*`,
`*_steam_paddleboat_*`, `*_elven_sailboat_*`). Pendant les six vues, le test désactive
`furlSailWhenStopped` côté serveur (puis le rétablit) pour que les voiles restent établies.

### Dirigeable steampunk — 1.6.0

Au-dessus d'un terrain plat, à l'est des bassins, joué en solo et sur serveur dédié :

* `/ship spawn steampunk_airship` : il apparaît **en l'air**, la quille un bloc au-dessus du sol,
  sans rien toucher ; **il ne tombe pas** (même hauteur au millième après 3 s) ;
* **six captures comparables à l'image de référence** (`steampunk_airship_1_droite` …
  `6_perspective`, puis `7_vol` et `8_pilote_auto`) ;
* **6 places occupées** (pilote + 5 passagers), un de plus refusé ;
* pilotage : **Espace fait monter** (4,9 blocs en 4 s, montée progressive), touche relâchée il
  **garde son altitude** (au millième), il **avance** (6,8 blocs en 5 s) et **vire** (13,9° en
  3 s) **à altitude constante**, **Ctrl le fait descendre** (3,3 blocs) ; les passagers restent
  assis ; le pilote descend sur le pont de la nacelle ; jamais à l'intérieur d'un bloc ;
* **pilote automatique en 3D** : itinéraire aérien de 60 blocs jusqu'à une escale 12 blocs plus
  haut, un **mur de 16 blocs** au milieu : il le **survole** (quille 5 blocs au-dessus), ne touche
  jamais ni le mur ni le sol, **arrive à l'escale** (à 2,9 blocs, pont à 4 cm de la hauteur
  voulue) puis se tourne vers le cap de l'escale ;
* **clic droit avec l'objet** sur le sol : un second dirigeable apparaît au-dessus ;
  `/ship give steampunk_airship` donne l'objet.

Tests unitaires (`AirshipTest`, 9 tests) : forme identique au générateur, dimensions et
places, vol stationnaire sans chute, montée et descente progressives avec inertie, atterrissage
sans s'enfoncer, plafond `maxAltitude` et toit infranchissables, virages doux, arrêt devant une
montagne, **itinéraire 3D par-dessus une colline** (décollage, survol à plus de 0,5 bloc du
sol, descente à l'escale, cap tenu à l'escale).

Non vérifié automatiquement : le **redémarrage d'un serveur** avec un dirigeable en route (la
sauvegarde utilise le même mécanisme que les navires — position, vitesses, vitesse verticale,
itinéraire et état du pilote automatique enregistrés avec l'entité — mais le test en jeu ne
peut pas redémarrer le serveur) ; les **sons** (joués côté client, inaudibles pour le test) ;
plusieurs joueurs réels à bord en même temps (le test utilise des porte-armures comme
passagers).

### Filets de sécurité (collisions désactivées)

Pour simuler un mod qui remplacerait le code des collisions (autre que Lithium), le test coupe
les collisions des coques puis lâche le joueur de 9 blocs de haut :

| Vérification | Solo | Serveur dédié |
|---|---|---|
| il est quand même rattrapé par le pont principal du galion | réussi | réussi |
| il est quand même rattrapé par le gaillard d'arrière | réussi | réussi |

### Galère (non-régression)

| Vérification | Sans Lithium | Avec Lithium |
|---|---|---|
| un joueur qui tombe sur le pont s'y tient (à 1/1000 de bloc près) | réussi | réussi |
| il saute sur le pont et retombe sur le pont | réussi | réussi |
| il marche jusqu'à la proue, monte sur la plate-forme avant, reste à bord | réussi | réussi |
| il saute depuis un quai (avec élan) et atterrit sur le pont | réussi | réussi |
| un mob (support d'armure) tient sur le pont | réussi | réussi |
| un nageur qui remonte sous la coque est arrêté par le fond de la coque | réussi | réussi |
| un joueur à la barre fait avancer le navire (Z) | réussi | réussi |
| le mob reste à bord pendant la navigation | réussi | réussi |

### Grand galion

| Vérification | Sans Lithium | Avec Lithium |
|---|---|---|
| le galion est mis à l'eau à côté de la galère, les deux coexistent | réussi | réussi |
| un joueur tombe sur le pont principal et s'y tient ; il saute et retombe sur le pont | réussi | réussi |
| il entre dans la **grande cabine** par la porte de la cloison | réussi | réussi |
| il sort sur le **balcon** par la porte du tableau arrière ; la balustrade le retient | réussi | réussi |
| il monte l'escalier jusqu'au **gaillard d'arrière** (+2,6 blocs) puis au **gaillard d'avant** | réussi | réussi |
| **16 passagers** assis (15 + le barreur) ; un 17ᵉ est refusé | réussi | réussi |
| maniement lourd : 0,7 bloc parcouru en 2 s, 11 en 8 s ; 9 blocs sur l'erre en 4 s sans propulsion ; 9° de virage en 4 s | réussi | réussi |
| pendant la navigation et le virage, les 16 passagers restent assis et un mob debout sur le pont est transporté | réussi | réussi |
| le barreur qui quitte la barre se retrouve debout sur le gaillard d'arrière | réussi (après correction) | réussi (après correction) |
| `/ship give galleon` donne l'objet *Grand galion* | réussi | réussi |

Correction apportée grâce à ce test : en quittant la barre, le joueur restait à la hauteur de
son siège, dans l'épaisseur du plancher du gaillard d'arrière. Le client place maintenant son
joueur sur le point de descente du siège, et le filet de sécurité couvre aussi les planchers
des châteaux.

Captures en jeu (branches `test-results-*`) : vue d'ensemble, flanc, poupe, proue, pont,
cabine, balcon, gaillard d'arrière, navigation.

### Grand vaisseau de guerre

| Vérification | Solo et serveur dédié, sans et avec Lithium |
|---|---|
| le vaisseau est mis à l'eau dans un troisième bassin ; la galère et le galion existent toujours | réussi |
| un joueur tombe sur le pont principal et s'y tient ; il saute et retombe sur le pont | réussi |
| il entre dans la **grande cabine** par la porte de la cloison | réussi |
| il monte au **gaillard d'arrière** puis à la **dunette** par les deux escaliers | réussi |
| il monte au **gaillard d'avant** | réussi |
| **24 passagers** assis (23 + le barreur) ; un 25ᵉ est refusé | réussi |
| maniement très lourd : 0,4 bloc en 2 s, 11 en 10 s ; 7,8 blocs d'erre en 4 s ; 4° de virage en 4 s | réussi |
| pendant la navigation, les 24 passagers restent assis et un mob debout sur le pont est transporté | réussi |
| le barreur qui quitte la barre se retrouve debout sur le gaillard d'arrière | réussi |
| collisions coupées : le joueur est quand même rattrapé par le pont principal et par la dunette | réussi |
| `/ship give warship` donne l'objet *Grand vaisseau de guerre* | réussi |

## Tests unitaires (85, tous réussis)

`./gradlew test` :

| Test | Vérifie |
|---|---|
| `galleyGeometryUnchanged` | **la galère est identique à la version 1.1.1** : sondes, sièges, ~1 800 valeurs de boîtes de collision, visée, embarquement, transport comparés à un instantané pris avant l'ajout du galion |
| `hullProfileMatchesModelGenerator`, `hullMatchesModelGenerator` | formes de coque Java = générateurs des modèles 3D (galère et galion) |
| `deckIsWalkableAtAnyHeading` (×2) | aucun trou dans les ponts, tous les caps |
| `wallsHaveNoPlayerSizedGaps`, `hullIsSolidBelowTheDeck`, `hullBoxesStayInsideTheHullBottom` | murailles sans brèche, coque pleine, pas de mur invisible sous l'eau |
| `sixteenSeats` | 16 places sur le galion, chacune libre de tout mur, et chaque point de descente est une place debout valide |
| `boardingSpots` | embarquer en cliquant n'importe où sur la coque du galion place le joueur debout, jamais dans un mur ni sur le toit de la dunette |
| `stairsAreClimbable` | marches ≤ 0,6 bloc jusqu'au gaillard d'arrière (+2,6) et au gaillard d'avant (+2) |
| `rescueOntoCastleFloors` | filet de sécurité sur les planchers des châteaux |
| `cabinIsAccessible`, `balcony` | on entre dans la grande cabine par la porte, on sort sur le balcon par le tableau arrière, la balustrade retient, le balcon est transporté |
| `gunports` | 12 sabords (6 par bord) prêts pour de futurs canons |
| `heavierThanTheGalley` | galion : > 10 s pour atteindre l'allure normale, > 30 blocs de glisse, virage plus lent |
| `ferryAroundTheIslandAndBack` (galion) | aller-retour de 400 blocs autour d'une île de 60 blocs, demi-tours aux escales, jamais dans la terre, aucun blocage |
| `routeWithTurnsStopsOnTheQuay` (galion) | route à 4 virages, arrêt à moins de 5 blocs de l'escale |
| `ferryGoesAroundTheIslandAndComesBack`, `routeWithWaypointsAndTurns` (galère) | inchangés |
| `physicsInertia`, `turningSlowsTheShip`, `moverStopsAtTheCoastAndCanBackOff`, `moverEscapesWhenSpawnedInsideTerrain`, `otherHullIsAnObstacle` | physique et collisions avec le terrain |
| `WarshipTest` (16 tests) | vaisseau : dimensions, forme identique au générateur, 24 sièges, ponts sans trou à tous les caps, murailles sans brèche, embarquement, escaliers, grande cabine, visée, 58 sabords, filets de sécurité, plus lourd que le galion, aller-retour de 600 blocs autour d'une île de 90 blocs, route à 4 virages |
| `matchesPythonReference` (×3) | le lecteur `.bbmodel` du mod produit exactement la même géométrie que le rendu de référence (galère 2 208 faces ; galion 7 943 faces, 2 textures) |
| `bonesAnimationsAndTextures`, `requiredBonesAndAnimationsExist`, `furlCollapsesTheSail` | os, animations et textures attendus par le mod |
| `NewShipsTest` (18 tests) | galère rouge, bateau à vapeur, voilier elfique : formes identiques aux générateurs, dimensions demandées (28 × 5 × 3, 22 × 8 × 5, 30 × 6 × 4), places et points de descente libres, ponts sans trou à tous les caps, embarquement, visée de la barre et de la coque, flottaison ; **roues à aubes** : une de chaque côté, hors de la coque, immergée d'environ 0,9 bloc, tambour solide, largeur prise en compte par le pilote automatique ; maniement (galère vive, vapeur progressive et maniable à basse vitesse, voilier rapide et fluide) ; identifiants et alias `grand_warship` |
| `NewShipModelsTest` | les trois nouveaux modèles : os et animations attendus, géométrie identique au rendu de référence Python |
| `NoZFightingTest` | **aucun scintillement (z-fighting)** : dans les six modèles, tels que le mod les lit, aucune face n'est dans le même plan qu'une autre face qu'elle chevauche (les deux sens comptent, le rendu dessine les deux côtés des faces) |
| `uniqueIds` | chaque cube et chaque os des six modèles a son propre identifiant |
| `tools/sail_check.py` (outil) | aucune voile n'en traverse une autre (vaisseau, galion, voilier, galère rouge) |

Les modèles ont aussi été vérifiés visuellement (`docs/preview.png`, `docs/preview_galleon.png`,
`docs/preview_galleon_details.png`) et leurs conventions comparées au code source de Blockbench.

## À valider en jeu de votre côté

Ce que les tests automatiques ne peuvent pas juger ou n'ont pas couvert :

1. **Plusieurs joueurs en même temps** : le serveur dédié est testé avec un joueur ; vérifiez à
   deux : marcher sur le galion pendant qu'un autre barre, s'asseoir, descendre.
2. **Aspect** : rendu du galion de nuit (fenêtres et lanternes éclairées), voiles au vent,
   drapeaux, roulis — jugement esthétique.
3. **Mise à l'eau avec l'objet** *Grand galion* (clic droit sur l'eau) : la vérification de
   place est testée via `/ship spawn galleon`, pas l'utilisation de l'objet à la main.
4. **Ferry en galion sur votre carte** : l'IA est validée en simulation et le galion navigue en
   jeu, mais vos ports réels (largeur des chenaux, quais) décideront des points de passage
   nécessaires (voir FERRY.md).
5. **Sauvegarde / redémarrage** avec les nouveaux navires (galère rouge, bateau à vapeur, voilier
   elfique) : ils utilisent la même sauvegarde que les autres, mais aucun test automatique ne
   redémarre le serveur ; de même avec un galion en mer et des joueurs à bord ; anciennes galères
   déjà posées dans votre monde (elles gardent leur identifiant `medievalships:galley`).
7. **Sons de la machine à vapeur, fumée, écume** : effets côté client vérifiés sur les captures
   (fumée visible) ; le son n'est pas vérifiable automatiquement.
8. **Roue à aubes en mouvement** : son sens de rotation est vérifié par le générateur et le
   modèle, mais il faut la regarder tourner en jeu (en avant et en marche arrière).
6. **Autres mods** de votre serveur qui modifient les collisions ou le rendu des entités (seul
   Lithium a été testé).
