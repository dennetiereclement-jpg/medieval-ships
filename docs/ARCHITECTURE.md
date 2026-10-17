# Architecture technique

## Vue d'ensemble

```
fr.medievalships
├── core/            Java pur, sans Minecraft, testé unitairement
│   ├── Ships            les types de navires : GALLEY, GALLEON (forme, plan, sièges, réglages)
│   ├── ShipType         identifiant, nom, géométrie et réglages par défaut d'un navire
│   ├── HullShape        forme paramétrique de coque (identique aux générateurs des modèles 3D)
│   ├── HullProfile      ancienne façade de la forme de la galère (conservée)
│   ├── ShipGeometry     une instance par type : coque, ponts, superstructures en boîtes de
│   │                    collision, sièges, sondes, visée, sabords
│   ├── ShipPhysics      accélération, inertie, barre, inertie de rotation
│   ├── ShipMover        déplacement avec collisions (terrain, quais, autres coques)
│   ├── Autopilot        pilote PNJ : points, escales, évitement, déblocage
│   └── Route, Waypoint, Gait, ShipConfig (par navire), ServerSettings (communs)
├── entity/          ShipEntity (commune) + GalleyEntity, GalleonEntity (une ligne chacune)
├── mixin/           EntityCollisionMixin (le pont devient solide)
├── command/         /ship
├── data/            config JSON + PersistentState (itinéraires, ferries, joueurs)
├── network/         paquet d'interaction client → serveur
└── client/          rendu (lecteur .bbmodel), visée précise, transport du joueur local
```

Aucune dépendance en dehors de Fabric API : **ni GeckoLib, ni Valkyrien Skies, ni Eureka**.
Le modèle et ses animations sont lus directement depuis le fichier Blockbench par un petit
lecteur intégré (`BbModel`), ce qui évite une dépendance supplémentaire à maintenir à chaque
version de Minecraft tout en gardant le modèle éditable dans Blockbench.

## Plusieurs navires, un seul code

Chaque navire est décrit par un `ShipType` (`core/Ships.java`) : une forme de coque
paramétrique (`HullShape`), un plan (`ShipGeometry.Spec` : sièges, barre, mâts, volumes
solides comme les châteaux, la cabine ou le balcon, sabords) et ses réglages par défaut.
Tout le reste est commun : `ShipEntity` (navigation, flottaison, passagers, transport sur le
pont, pilote automatique, persistance), les collisions, les commandes, le rendu
(`ShipRenderer` + un `ShipModels.Visual` par navire). Les sous-classes `GalleyEntity` et
`GalleonEntity` ne font que dire quel type elles sont.

Ajouter un navire = un `ShipType` dans `Ships`, une sous-classe d'une ligne, un `registerShip`,
un modèle Blockbench et une ligne dans `ShipModels`.

La galère n'a pas changé : ses valeurs sont reprises telles quelles dans `Ships.GALLEY`, son
identifiant d'entité (`medievalships:galley`) et d'objet aussi, ses sauvegardes se chargent
sans conversion, et le test `galleyGeometryUnchanged` compare toute sa géométrie (sondes,
sièges, boîtes de collision, visée, embarquement) à un instantané pris sur la version 1.1.1.

### Préparé pour les canons

`ShipGeometry.gunports()` donne pour chaque sabord sa position (repère du navire) et son bord
de tir ; le modèle du galion contient un os vide `cannon_l1`…`cannon_r6` à chaque sabord et un
os de mantelet `gunport_*` (ouvrable par une future animation). Un futur système de combat
pourra donc ajouter les canons sans toucher au modèle ni aux collisions.

## Une seule entité, autorité serveur

Chaque navire est **une seule entité** (`medievalships:galley` ou `medievalships:galleon`). Toute la navigation tourne sur le
serveur, 20 fois par seconde :

1. commandes : entrées du barreur (le serveur reçoit déjà les touches Z/Q/S/D, Espace, Ctrl
   via le paquet vanilla `PlayerInput`, aucun paquet supplémentaire) ou pilote automatique ;
2. `ShipPhysics` : vitesse et vitesse de rotation ;
3. flottaison : la hauteur suit la surface de l'eau mesurée sous la proue, le centre et la
   poupe ;
4. `ShipMover` : le déplacement est testé avec ~140 points de sonde répartis sur la coque
   (quille, flottaison, au-dessus de l'eau pour les quais). Si le mouvement complet heurte
   quelque chose, le navire essaie sans rotation, rotation seule, puis en glissant le long de
   l'obstacle ; sinon il s'arrête avec un léger rebond. Un navire déjà engagé dans un obstacle
   ne peut faire que des mouvements qui ne l'enfoncent pas davantage : il ne reste jamais
   bloqué définitivement (marche arrière toujours possible) ;
5. le cap précis est synchronisé par le DataTracker (les paquets d'entité arrondissent les
   angles à 1,4°, trop grossier pour une coque de 20 blocs) ; les clients interpolent.

Le barreur n'est **pas** le « controlling passenger » vanilla : il envoie seulement ses
touches. Le navire est donc identique pour tous les joueurs et pour le pilote automatique,
et il n'y a pas de désynchronisation entre clients. La latence du barreur est masquée par
l'inertie d'un navire de cette taille.

## Passagers assis

Galère : 9 places, la barre (siège 0) et 8 places sur les 4 bancs. Galion : 16 places, la
barre (siège 0), 8 bancs le long des pavois du pont principal, 3 sur le gaillard d'avant,
2 sur le gaillard d'arrière et 2 chaises dans la grande cabine. Les sièges sont des positions
locales tournées avec le navire (`getPassengerAttachmentPos`) ; l'attribution des sièges est
synchronisée vers les clients. Les passagers tournent avec le navire (leur caméra suit le cap)
et regardent librement autour d'eux ; seul le siège 0 pilote.

## Marche libre sur le pont — comment ça marche

C'était le point le plus délicat. Solution retenue, fiable sans moteur physique externe :

1. **Le pont est solide.** Minecraft calcule les collisions d'une entité avec une liste de
   formes. `EntityCollisionMixin` ajoute à cette liste, pour chaque navire proche, de petites
   boîtes alignées sur le monde qui pavent le pont (cases de 0,5 bloc) et la coque (parois du
   bastingage jusqu'à la quille). Chaque boîte couvre une petite cellule tournée de la coque :
   leur union épouse la forme réelle pour **n'importe quel cap** (testé tous les 7,5°), sans
   trou ni grosse boîte rectangulaire. Seules les boîtes proches de l'entité qui bouge sont
   générées (une dizaine en général). Les marches de 0,5 bloc vers les ponts surélevés de la
   poupe et de la proue se montent naturellement ; le bastingage (1,1 à 1,6 bloc) empêche de
   tomber par-dessus bord mais s'enjambe en sautant.
2. **Ce qui est à bord suit le navire.** Après chaque tick, tout ce qui se trouve dans le
   volume du pont (y compris en plein saut) est déplacé exactement comme la coque : translation
   et rotation autour du navire, cap compris.
   * Joueur local : côté client (c'est le client qui simule son propre joueur), après le tick
     de toutes les entités, en ne décalant que la position courante pour que joueur et navire
     s'interpolent ensemble à l'écran (pas de tremblement).
   * Mobs, PNJ, objets au sol : côté serveur.
3. **Pas de faux « moved wrongly ».** Côté serveur, les joueurs ne reçoivent pas les
   collisions de coque : le client est déjà l'autorité de son propre mouvement et la coque
   serveur a quelques ticks d'avance sur celle que voit le client. Résultat : aucune
   correction de position intempestive. Le contrôle anti-vol vanilla (« flying ») ne regarde que
   les blocs sous les pieds : sur les ponts surélevés l'eau est trop loin, le compteur est donc
   remis à zéro pour les joueurs qui se trouvent sur un navire.
4. **Clics précis.** La boîte d'entité est petite ; la visée (barre, bancs, coque, pont) est
   calculée contre la vraie géométrie et envoyée au serveur par un paquet dédié, validé
   (distance maximale 8 blocs). Cliquer sur le pont n'atteint jamais l'eau ou le fond sous la
   coque (impossible de vider l'eau sous le navire avec un seau).

5. **Compatibilité Lithium (et mods qui remplacent les collisions).** Lithium réécrit le calcul
   des collisions d'entités et contournait notre ajout : les joueurs traversaient le pont en
   sautant. Un mixin optionnel (`mixin/compat`, chargé seulement si Lithium est présent) ajoute
   les coques à la liste de collisions de Lithium. En plus, un **filet de sécurité** indépendant
   de tout mod replace sur le pont (sans saut visible) une entité qui se retrouverait dans
   l'épaisseur du pont. Vérifié en jeu, avec et sans Lithium (voir TESTS.md).
6. **Volumes multiples.** Au-delà de la coque, chaque navire déclare des volumes solides
   (`ShipGeometry.LocalBox`) tournés avec lui : pour le galion, plancher du gaillard d'arrière
   (toit de la grande cabine), cloison et sa porte, tableau arrière et porte du balcon, balcon
   et balustrade, dunette et son toit, marches des escaliers, barrières des gaillards. Ils sont
   découpés en petites boîtes alignées sur le monde exactement comme le pont, et servent aussi
   à la visée, au transport des entités (balcon en porte-à-faux compris) et au choix du point
   d'embarquement (jamais dans un mur ni dans la cabine fermée).

Limites connues, assumées :

* le roulis/tangage est **visuel** (≤ 1°) : le plancher de collision reste horizontal ;
* l'IA de déplacement des mobs vanilla ne « comprend » pas un pont mobile : un mob à bord est
  transporté correctement mais peut tomber à l'eau s'il marche vers le bastingage ouvert ;
* un joueur avec ~300 ms de ping ou plus voit la coque avec un léger retard ; la marche reste
  fluide car le transport est calculé sur la coque affichée.

Pourquoi pas Valkyrien Skies/Eureka : ils transforment des blocs du monde en « shipyard », ce
que vous ne voulez pas (navire en blocs), et ajoutent une dépendance lourde dont la version doit
suivre chaque mise à jour. Notre approche ne touche qu'une méthode de collision vanilla.

## Pilote automatique

* Suivi de route par « poursuite pure » : le navire vise un point 12 blocs plus loin sur le
  segment courant ; en fin de segment ce point glisse sur le segment suivant, d'où une
  anticipation naturelle des virages.
* Vitesse planifiée : allure de croisière, réduite dans les virages serrés, puis profil de
  freinage `v = √(2·a·d)` vers la prochaine escale pour s'arrêter au point exact.
* Évitement local, recalculé toutes les 5 ticks (pas de calcul de chemin global) : des rayons
  de largeur de coque sont lancés de -100° à +100° autour du cap voulu ; le premier cap libre
  le plus proche est choisi, en gardant le même côté pour contourner un obstacle (pas
  d'hésitation). La portée augmente avec la vitesse (≥ 36 blocs).
* Déblocage : sans progrès pendant 6 s → marche arrière en braquant ; après plusieurs échecs
  il tente l'autre côté ; sans rapprochement de l'objectif pendant 50 s → point de passage
  abandonné ou alerte aux administrateurs.
* Adapté à chaque navire : la longueur devant le centre (`aiReach`), la demi-largeur des rayons
  de dégagement et le rayon d'arrivée « à quai » viennent de la géométrie du navire ; les
  distances d'anticipation, de détection et de freinage viennent de sa configuration. Le
  galion, qui ne peut pas pivoter sur place, garde de l'erre pour faire demi-tour
  (`aiTurnAroundSpeed`) et son délai d'abandon est proportionnel à sa longueur.
* Validé en simulation : aller-retour autour d'une île, route à plusieurs virages, et
  60 archipels aléatoires (57 réussis ; les 3 échecs étaient des ports encombrés d'îlots à
  7 blocs, où l'administrateur doit ajouter un point de passage — le navire l'a signalé).

## Persistance

Sauvegardé avec l'entité : position, cap, vitesse, vitesse de rotation, barre, allure, limite
de vitesse, mode automatique, itinéraire, point visé, sens, phase (en mer / à quai), temps
d'attente restant, nom. Sauvegardé dans le monde (`data/medievalships.dat`) : itinéraires,
dernière position des navires automatiques, navire de chaque joueur déconnecté à bord.

## Performances

* calculs uniquement côté serveur, sur les navires chargés ;
* sondes de coque testées seulement quand le navire bouge ou tourne ;
* évitement d'obstacles toutes les 5 ticks, jamais de recherche de chemin ;
* collisions : liste en cache des navires par monde, rejet par distance avant tout calcul ;
* réseau : position vanilla + 7 valeurs DataTracker envoyées seulement quand elles changent ;
* rendu : galère ~370 cubes / 2200 faces, galion ~1540 cubes / 7900 faces (deux passes : coque
  et drapeaux, pour l'emblème remplaçable) ; animations calculées par le client à partir de
  l'état synchronisé ; culling sur la taille réelle de chaque navire ;
* collisions du galion : même coût par entité que la galère (seules les cellules proches de
  l'entité qui bouge sont générées), une vingtaine de boîtes en moyenne ;
* aucune génération naturelle, aucune structure, aucun spawn automatique.
