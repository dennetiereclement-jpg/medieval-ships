# Tests — ce qui a été vérifié, et ce qui ne l'a pas été

## Test dans le vrai jeu (automatique, GitHub Actions)

À chaque envoi sur GitHub, la tâche *In-game test* lance un **vrai client Minecraft 1.21.11
avec le mod** (`src/gametest/.../ShipClientGameTest.java`), crée un monde, un bassin et un
quai, met la galère à l'eau puis vérifie, résultats et captures publiés sur la branche
`test-results-full` :

| Vérification | Résultat |
|---|---|
| un joueur qui tombe sur le pont s'y tient (à 1/1000 de bloc près) | réussi |
| il saute sur le pont et retombe sur le pont | réussi |
| il marche jusqu'à la proue, monte sur la plate-forme avant, reste à bord | réussi |
| il saute depuis un quai (avec élan) et atterrit sur le pont | réussi |
| un mob (support d'armure) tient sur le pont | réussi |
| un nageur qui remonte sous la coque est arrêté par le fond de la coque | réussi |
| un joueur à la barre fait avancer le navire (Z) | réussi |
| le mob reste à bord pendant la navigation | réussi |

Correction apportée grâce à ce test : la coque était creuse (un plancher et des parois) ; un
joueur tombé à l'eau pouvait passer sous la quille et remonter à l'intérieur. La coque est
maintenant un **volume plein** de la quille au pont, qui suit sa forme arrondie.


## Contexte

L'environnement de développement utilisé **bloquait l'accès** à `maven.fabricmc.net` et aux
serveurs de Mojang (`piston-meta`, `piston-data`, `libraries.minecraft.net`). Il a donc été
**impossible de télécharger Minecraft 1.21.11 et Fabric Loom**, et donc de compiler le mod
complet, de produire le `.jar` et de lancer un client ou un serveur dédié.

Pour réduire le risque malgré tout :

* toute la logique de navigation est écrite en **Java pur** (paquet `core`) et a été compilée
  et testée ;
* le code lié à Minecraft a été écrit en vérifiant **chaque nom de classe, méthode et champ**
  dans les mappings Yarn officiels de 1.21.11 (`1.21.11+build.6`) et dans les sources de
  Fabric API 0.141.6+1.21.11, puis relu par un second audit indépendant sur la même base.

## Tests exécutés (tous réussis : 18/18)

`./gradlew test` (ici exécutés avec `javac` + JUnit 5) :

| Test | Vérifie |
|---|---|
| `poseRoundTripAndForward` | conversions repère navire ↔ monde, conventions de cap Minecraft |
| `hullProfileMatchesModelGenerator` | la forme de coque Java = celle du générateur du modèle 3D |
| `deckIsWalkableAtAnyHeading` | **aucun trou dans le pont** : ~1 100 points du pont × 48 caps |
| `wallsHaveNoPlayerSizedGaps` | **aucune brèche** de 0,6 bloc dans le bastingage, 32 caps |
| `farQueryReturnsNothing`, `carryVolume` | rejet rapide ; volume transporté (y compris en saut) |
| `seatsAndPicking` | 9 places ; clic sur la barre, la coque, le pont ; pas de clic « à travers » le pont |
| `physicsInertia` | accélération progressive (> 3 s), glisse > 15 blocs après relâchement, retour progressif de la barre |
| `turningSlowsTheShip` | perte de vitesse en virage |
| `moverStopsAtTheCoastAndCanBackOff` | arrêt à la côte sans la pénétrer, marche arrière possible |
| `moverEscapesWhenSpawnedInsideTerrain` | un navire engagé dans la terre ne peut pas s'y enfoncer mais peut en sortir |
| `otherHullIsAnObstacle` | deux navires ne se traversent pas |
| `ferryGoesAroundTheIslandAndComesBack` | ferry A → B → A avec escales, contournement d'une île, jamais dans la terre |
| `routeWithWaypointsAndTurns` | route à 4 virages, arrêt à moins de 3,5 blocs de l'escale |
| `nextIndexModes` | modes aller-retour / boucle / aller simple |
| `requiredBonesAndAnimationsExist` | le `.bbmodel` contient les os et animations utilisés par le mod |
| `matchesPythonReference` | le lecteur Java du `.bbmodel` produit **exactement** la même géométrie que le rendu de référence (2 208 faces, pose animée : rames, barre, voile) |
| `furlCollapsesTheSail` | la voile se cargue réellement |

Test de robustesse supplémentaire (hors suite JUnit) : 60 archipels aléatoires de 6 îles,
aller-retour de 600 blocs : **57 réussis**, 0 passage dans la terre. Les 3 échecs sont des
ports avec un îlot à 7 blocs du quai ; le navire a alors signalé son blocage (comportement
prévu : l'administrateur ajoute un point de passage).

Le modèle a aussi été vérifié visuellement (rendu des 6 vues, `docs/preview.png`) et ses
conventions (ordre des rotations, faces/UV, animations) ont été comparées au code source de
Blockbench.

## Tests NON exécutés (à faire de votre côté)

Impossible ici faute d'accès aux serveurs Fabric/Mojang :

1. **Compilation** `./gradlew build` et production du `.jar`.
2. Lancement client (`runClient`) et **serveur dédié** (`runServer`).
3. En jeu : mise à l'eau, pilotage, passagers, marche sur le pont, rendu et animations,
   commandes, sauvegarde/redémarrage, ferry sans joueur à proximité.

Procédure de recette conseillée (≈ 20 min, deux joueurs) :

1. Créatif → onglet *Navires médiévaux* → clic droit sur un océan.
2. Clic droit sur la barre : Z/Q/D/S, Espace/Ctrl ; vérifier inertie et collisions avec la côte
   et un quai.
3. Second joueur : clic droit sur la coque (monter à bord), marcher pendant que le navire
   avance et tourne, sauter, s'asseoir sur un banc, Maj pour se lever.
4. Se déconnecter à bord, se reconnecter : le joueur doit être sur le pont, le navire intact.
5. Faire un ferry selon `docs/FERRY.md`, s'éloigner à plus de 300 blocs, revenir ; puis
   redémarrer le serveur pendant une traversée.
6. `/ship list`, `/ship info`, accroupi + clic gauche pour récupérer le navire.

### Audit indépendant du code Minecraft

Un second audit a vérifié ~200 symboles Minecraft/Fabric contre les mappings 1.21.11 :
aucune erreur de compilation probable trouvée. Il a relevé 5 problèmes d'exécution, tous
corrigés : collisions de coque absentes du chemin « montée de marche », risque d'expulsion
« Flying is not enabled » sur les ponts surélevés, fuite mémoire du registre des navires,
rayon de chargement de chunks trop petit possible, tickets de chunk pouvant expirer avant le
chargement d'un ferry au redémarrage.

Points non vérifiables sans les sources décompilées (à surveiller à la première compilation) :
la visibilité de `Entity.onRemove` (surchargée en `public`) et la capture des arguments dans
les `@ModifyVariable` de `EntityCollisionMixin`.

Si la compilation signale une erreur, elle portera très probablement sur un nom d'API Minecraft
de 1.21.11 : envoyez-moi le message, la correction sera rapide.
