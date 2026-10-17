# Tests — ce qui a été vérifié, et ce qui reste à valider en jeu

## Compilation

Le mod est compilé à chaque envoi par GitHub Actions (`./gradlew build`, tâche *Build*) avec
Fabric Loom 1.14, Minecraft 1.21.11, Yarn `1.21.11+build.6`, Fabric API 0.141.6+1.21.11 :
le `.jar` obtenu est celui qui vous est livré.

## Tests dans le vrai jeu (automatiques, GitHub Actions)

La tâche *In-game test* lance un **vrai client Minecraft 1.21.11** avec le `.jar` de
production (mod remappé, comme sur un vrai serveur), deux fois : **sans** et **avec Lithium**.
Chaque fois, tout le scénario est joué **en solo** puis sur un **vrai serveur dédié** auquel le
client se connecte par le réseau (contrôles de mouvement du serveur actifs) : 54 vérifications,
toutes réussies.
Le test (`src/gametest/.../ShipClientGameTest.java`) crée un monde, des bassins, met les navires
à l'eau puis vérifie (résultats et captures publiés sur les branches `test-results-vanilla` et
`test-results-lithium`) :

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

## Tests unitaires (38, tous réussis)

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
| `matchesPythonReference` (×2) | le lecteur `.bbmodel` du mod produit exactement la même géométrie que le rendu de référence (galère 2 208 faces ; galion 7 943 faces, 2 textures) |
| `bonesAnimationsAndTextures`, `requiredBonesAndAnimationsExist`, `furlCollapsesTheSail` | os, animations et textures attendus par le mod |

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
5. **Sauvegarde / redémarrage** avec un galion en mer et des joueurs à bord ; anciennes galères
   déjà posées dans votre monde (elles gardent leur identifiant `medievalships:galley`).
6. **Autres mods** de votre serveur qui modifient les collisions ou le rendu des entités (seul
   Lithium a été testé).
