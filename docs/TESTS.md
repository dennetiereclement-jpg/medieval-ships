# Tests — ce qui a été vérifié, et ce qui reste à valider en jeu

## Compilation

Le mod est compilé à chaque envoi par GitHub Actions (`./gradlew build`, tâche *Build*) avec
Fabric Loom 1.14, Minecraft 1.21.11, Yarn `1.21.11+build.6`, Fabric API 0.141.6+1.21.11 :
le `.jar` obtenu est celui qui vous est livré.

## Tests dans le vrai jeu (automatiques, GitHub Actions)

La tâche *In-game test* lance un **vrai client Minecraft 1.21.11** avec le `.jar` de
production (mod remappé, comme sur un vrai serveur), en quatre variantes : `vanilla` (Fabric API seule), `lithium`,
`decor` (les mods de décoration du Nautilus) et, depuis 1.28.1, `sodium` (Fabric API + Sodium, le moteur de rendu des
tronçons remplacé).
Chaque fois, tout le scénario est joué **en solo** puis sur un **vrai serveur dédié** auquel le
client se connecte par le réseau (contrôles de mouvement du serveur actifs) : **194 vérifications,
toutes réussies** (version 1.6.0, avec et sans Lithium, en solo et sur serveur dédié).
Le test (`src/gametest/.../ShipClientGameTest.java`) crée un monde, des bassins, met les navires
à l'eau puis vérifie (résultats et captures publiés sur les branches `test-results-<variante>`) :

### Navires de ville (navire royal au lion, navire forteresse, navire à vapeur à engrenages) — 1.27.0

Trois tests appelés à la fin de la séquence de `ShipClientGameTest`, en solo puis sur le serveur dédié, chacun dans son
propre bassin vitré de 100 blocs de long rempli d'eau (aucun recouvrement avec les zones des tentes, décorations, pieu,
pont-levis ni des autres navires) : `RoyalLionShipGameTest` (x 3868…3932) et `FortressShipGameTest` (x 3368…3432), avec
un quai de pierre à tribord, et `GearSteamShipGameTest` (x 4872…4928 ; déplacé de x 3400 à l'intégration, où il
recouvrait le bassin de la forteresse). Chacun met le navire à l'eau par
`/ship spawn <id>`, vérifie qu'il flotte à sa ligne de flottaison, que le modèle est chargé avec ses deux textures et
ses animations, place le joueur sur chaque pont et dans chaque pièce (cabine du capitaine, salle d'apparat, salle du
conseil et tourelle, salle des machines, quartiers, cale, galerie…), ouvre les portes, le fait s'asseoir sur trois
sièges (un seul, le fauteuil du capitaine, pour le vapeur) et se relever à côté, marcher dans la cale et la cabine
meublées (navire royal et forteresse), déploie la passerelle par son levier sur le quai puis la replie (sortie puis
rangée sans quai pour le vapeur), et le fait piloter quelques secondes à la barre (le navire avance ; engrenages, fumée et machine pour le
vapeur) ; captures des vues des références et des pièces meublées ; depuis 1.28.0, capture `<id>_cale_niveau_mer` depuis le pied de
l'escalier de la cale et comptage côté client des blocs d'eau du bassin dans l'emprise de la coque (tous ceux entièrement dans la
coque cachés, aucun de la mer libre) ; depuis 1.28.1 la capture est relue et ses pixels bleus comptés (moins de 4 % du cadre,
la nappe de la mer en couvre 10 à 25 %, une cale propre moins de 1 %) : la seule vérification qui voit ce que le moteur de
rendu a vraiment dessiné, Sodium compris ; puis retrait. Vérifications par mode : 28 (navire
royal au lion), 30 (forteresse), 22 (vapeur à engrenages). JUnit : `RoyalLionShipTest`, `FortressShipTest`,
`GearSteamShipTest` (grille fermée, pièces atteignables à pied, sièges et places pour se relever, mobilier dans la
coque, sondes de la grille et des mâts identiques à la forme Python), `NewShipModelsTest` (os, animations et quads de
référence des trois modèles), `NoZFightingTest`, `GangplankSpecsTest` et `GangplankFoldTest` (passerelles et paquets
rangés). Plans : [RoyalLion_PLAN.md](RoyalLion_PLAN.md), [Fortress_PLAN.md](Fortress_PLAN.md),
[GearSteam_PLAN.md](GearSteam_PLAN.md).

### Tentes de marché de Lion Port et des villes (dix-sept tentes) — 1.26.0

`TentGameTest` pose chacune des dix-sept tentes de marché (`TentTypes.MARKET_TENTS`, de `tente_lion_pavillon` à
`tente_arsenal`) une fois, face au sud, sur la plateforme de pierre dégagée de 29 × 29 blocs (emprise de chacune vérifiée
d'abord, la plus grande est notée dans le journal) : bloc d'ancrage, orientation, entité de bloc, boîtes de collision
enregistrées puis une requête de collision sur la première, capture d'écran, retrait par `/tent remove x y z` et boîtes
oubliées. Pendant qu'elle est posée, un villageois (sans IA) est mis au centre de la place du marchand laissée par son
constructeur derrière le comptoir : la colonne de 1 × 1 × 2,2 est hors de toute boîte de collision, le villageois n'est
dans aucune boîte (chemin du mixin) et ne bouge pas. JUnit `MarketATest` à `MarketFTest` (un par groupe : chargement,
modèle statique, lumière, emprise, poteaux, entrée, place du PNJ libre et atteignable à pied) et `MarketTentsTest`
(enregistrement, langues, fichiers, noms courts, place du marchand, emprise dans la plateforme dans les quatre
orientations). Voir [TENTES.md](TENTES.md#tentes-de-marché-de-lion-port-et-des-villes-1260).

### Camp militaire (pieu défensif et trois tentes) — 1.25.0

`StakeGameTest` (appelé par `ShipClientGameTest`) : pieu posé par `/deco place` (bloc, orientation, ticker serveur pour
lui seul, le tronc collisionne) ; un zombie (NoAI) à la pointe est blessé en moins de 10 ticks et repoussé vers
l'extérieur, pas de nouveau coup avant le délai, un coup après ; un zombie au pied, un contre le flanc du tronc et un
villageois à la pointe ne sont jamais blessés ; le joueur de test en survie (sa Résistance retirée le temps de
l'essai) n'est pas blessé par défaut, l'est avec `damagePlayers = true` (réglage rétabli) ; trois pieux côte à côte
se posent ; un pieu cassé rend son objet ; captures. `TentGameTest` pose chacune des trois tentes du camp
(`tente_militaire`, `tente_commandement`, `tente_marchande`) et met un villageois sur une place PNJ libre, hors de
toute boîte de collision ; `DecorationGameTest` attend 9 décorations. JUnit `StakeTest`, `CampMilitaireTest`,
`CampCommandementTest`, `CampMarchandeTest`. Voir [DECORATIONS.md](DECORATIONS.md#pieu-défensif-1250) et
[TENTES.md](TENTES.md#camp-militaire-1250).

### Pont-levis automatique — 1.24.0

`DrawbridgeGameTest` (joué par le vrai client, en solo **avec redémarrage du monde** puis sur serveur dédié) construit par
commandes un canal de 240 blocs (eau de 9 de profondeur, berges au niveau du tablier, quatre tours d'angle, passerelle
fixe en hauteur entre les tours, tablier de planches 5 blocs au-dessus de l'eau avec garde-corps et lanternes
suspendues), puis **n'utilise que les vraies commandes `/pontlevis`** :

* **définition et vérification** : un bloc posé dans l'arc de montée du vantail A est **refusé et nommé** par
  `verifier` (« heurteraient des blocs fixes … 2678 -42 -8 ») ; retiré, la vérification passe ; eau trouvée à −49,1,
  dessous du tablier mesuré **aux lanternes suspendues** (−44,44), chenal 19 de large (écart des charnières), travée de
  5 le long du chenal, axe le long de x, charnières automatiques sur les arêtes basses côté rive (z −9 et z 10,
  y −44) ;
* **conversion** : le pont est fermé et **ses planches sont toujours dans le monde** ; une seconde conversion est
  refusée sans rien changer ; aperçu (capture `pontlevis_1_apercu`) ;
* **barque** : une barque vide sur son pilote automatique traverse le pont **fermé** (aucune levée, verdict « passe
  sous le pont fermé ») ; avec un occupant (porte-armure assis), toujours aucune levée et le verdict compte sa tête
  (« occupants +… ») ; avec une **marge de 3 blocs**, la même barque chargée déclenche l'attente de sécurité puis la
  montée **80 ticks plus tard** : les planches quittent le monde, le client a les vantaux (boîtes) et les deux
  barrières (capture `pontlevis_2_ouverture`), le pont est ouvert (`pontlevis_3_ouvert`), se referme **5 s après le
  départ de la barque** et remet planches, garde-corps et lanternes ;
* **galère depuis l'ouest puis depuis l'est** (pilote automatique, destination de l'autre côté) : la levée se
  déclenche quand **la proue** est à 50 blocs du tablier (mesuré entre 44 et 52), le pilote automatique **attend
  devant le tablier** tant que le pont n'est pas ouvert (point le plus proche ≥ 2,5 blocs), la galère passe, le pont
  reste ouvert tout le temps qu'elle est dans le passage (`pontlevis_5_passage_*`), aucune fermeture ne commence tant
  qu'elle est comptée, le pont se referme une fois la zone de maintien quittée, les planches reviennent ;
* **joueur et sécurités** : un joueur en survie debout sur le tablier fermé ; une demande scriptée lance l'attente de
  sécurité ; **7 s plus tard rien n'a bougé** et le diagnostic nomme le tablier ; le joueur descend, les vantaux
  montent ; en marchant depuis la berge vers le tablier absent, **la barrière l'arrête** au bout de la berge
  (`pontlevis_4_barriere`) ; ouvert, un joueur téléporté à l'emplacement du tablier **tombe à l'eau** (le volume est
  réellement libre) ; la demande retirée, la fermeture commence ; **une nouvelle demande en pleine descente inverse le
  mouvement sans saut d'angle** ; retour à fermé, tablier en place ;
* **redémarrage (solo)** : le pont laissé ouvert (demande longue) est retrouvé **ouvert à 80° après la réouverture du
  monde**, ses planches toujours absentes, le client le reçoit à la connexion (`pontlevis_6_apres_redemarrage`) ; il se
  referme à la demande annulée et remet le tablier ;
* **restauration et suppression** : `restaurer` remet planches et garde-corps, **les tours et la passerelle fixe
  sont intactes**, le pont n'est plus converti ; `supprimer` l'oublie.

**Résultat (joué ici, vrai client 1.21.11 sous Xvfb, jar de production, sans Lithium) : 118 vérifications, toutes
réussies** — 53 en solo, 9 après la réouverture du monde, 56 sur le serveur dédié. Mesures relevées : eau −49,11, dessous
−44,94 (lanternes), largeur navigable 19, travée 5, charnières z −9 / 10 à y −44 ; galère de l'ouest : déclenchement à
48,3 blocs de la proue, point le plus proche 4,1 blocs avant l'ouverture, vitesse nulle devant le tablier, 22 ticks dans le
passage ; galère de l'est : 47,9 / 4,1 / 22 ticks. Ce test a trouvé et fait corriger trois défauts avant livraison : la
détection ne tournait jamais (débordement d'un compteur initialisé à `Long.MIN_VALUE`), la vérification du volume balayé
comptait la culée derrière la charnière (tout vrai pont aurait été refusé), et l'aperçu filaire plantait le client (format
des lignes de 1.21.11 : largeur de ligne obligatoire). Il tourne aussi dans la tâche *In-game test* de GitHub Actions
(sans et avec Lithium, avec les mods de décoration), à la suite des autres scénarios ; en local,
`./gradlew runProductionClientGameTest -PgametestOnly=drawbridge` ne joue que lui (≈ 9 min).

Rejoué tel quel après les changements visuels (mouvement amorti, chaînes de levage, poussière et choc en fin de
course) : **118 vérifications, toutes réussies** (53 solo, 9 après réouverture, 56 dédié), mêmes mesures. Les repères
de temps tiennent avec la courbe amortie (montée 80 ticks après le début de l'avertissement, fermeture 100 ticks après
le dernier navire, inversion en pleine descente sans saut : 65,2° → 68,4°) ; les chaînes se dessinent sans erreur sur
le client solo comme sur le client du serveur dédié, dans tous les états (`pontlevis_2_ouverture` les montre tendues
vers les ancres pendant la montée) ; le pont rouvert après redémarrage est retrouvé à 80° avec ses chaînes.
Rejoué une troisième fois avec le mécanisme complet (axe et paliers de charnière, poutre de treuil et tambours,
chaînes à vrais maillons, poteaux de barrière, lanternes qui gardent leur lumière) : **118 vérifications, toutes
réussies** (53 solo, 9 après réouverture, 56 dédié), aucune erreur de rendu, mêmes repères de temps ; deux captures
rapprochées en plus (`pontlevis_1b_mecanisme_ferme` : les chaînes des coins du tablier aux tambours sous la passerelle
fixe, pont fermé ; `pontlevis_6b_mecanisme_ouvert` : le vantail dressé, son axe et ses chaînes enroulées, après le
redémarrage).

Tests unitaires (`LeafGeometryTest`, `ChannelZonesTest`, `GaugeAndCycleTest`, 19 tests, Java pur) : repère et
rotation des vantaux (le bout libre monte, axe de rendu `v × up`, vantail de l'autre rive symétrique), boîtes fermées
identiques aux blocs, vantail dressé, centre du chenal libre une fois levé, volume balayé, dessous mesuré aux saillies
dans la bande navigable ; zones des deux côtés du chenal avec la proue qui compte, hystérésis, passage, bande navigable
qui ignore une barque amarrée sur la berge, portée d'une coque selon son cap, boîtes des zones (chenal en diagonale
compris) ; gabarit (barque qui passe, barque chargée qui passe avec la marge par défaut mais pas avec une plus
grande, galère au mât de 13,2 qui ouvre, bateau à vapeur trop large, égalité à la limite) ; cycle complet (attente de
sécurité 80 ticks, 160 ticks de montée, délai de 100 ticks, descente), inversion sans saut sur une nouvelle demande ou
une entité sous les vantaux, navire arrêté dans le passage qui tient le pont ouvert et fait refuser une fermeture
manuelle, joueur sur le tablier qui retient la montée avec diagnostic toutes les 5 s puis disparition de la demande
sans mouvement, bloc dans l'emprise → ERREUR puis reprise, automatisme suspendu et ordres manuels, gel quand les
tronçons ne sont pas chargés, restauration d'un état et réglages bornés.

Vérifié **par inspection seulement** (pas de test automatique) : la compatibilité Lithium du chemin de collision des
vantaux (même hook que les coques, `appendHulls`), le son (inaudible pour le test), plusieurs joueurs réels à la fois,
un navire d'un autre mod par profil, une largeur de navire supérieure au chenal (le verdict « trop large » n'est couvert
que par le test unitaire), le déchargement d'un tronçon pendant qu'un navire est en approche (la règle de grâce n'est
couverte que par relecture du code).

### Passerelles d'embarquement — 1.23.0

`GangplankGameTest` (en solo **et** sur serveur dédié) : quai de pierre et bassin construits par commandes, sloop
marchand à quai ; le levier est visé et cliqué pour de vrai (sélection côté client, paquet, serveur) → déploiement →
passerelle posée sur le quai ~3 s plus tard, boîtes de marche enregistrées sur le client ; un joueur en survie marche
du quai jusqu'au pont (touche avancer seulement) puis redescend sur le quai ; repli refusé tant qu'il est dessus,
accepté ensuite ; les commandes du pilote sont ignorées passerelle sortie (le sloop ne bouge pas) ; déploiement
refusé avec un bloc dans l'arc ; aller-retour NBT cohérent (mouvement en cours → état final) ; rechargement après la
disparition du quai → la passerelle se replie, puis refus faute d'appui ; dirigeable steampunk : refus en plein ciel
(« dans le vide »), déploiement à côté d'un ponton, maintien sur place, marche du ponton au pont. JUnit
`GangplankTest` : repère, animation, marches, escalier, recherche d'appui, balayage, fichiers et modèles.
1.23.2 (paquet compact) : le paquet rangé reste sous la charnière et petit (au plus un segment de haut, la moitié de la
planche de large), capture `passerelle_0b_paquet_replie` ; JUnit `GangplankFoldTest` (pour chaque navire, sur ses vrais
modèles : emprise sur la coque <= 40 % du paquet en accordéon de 1.23.1, saillie <= 0,35, à plat contre le flanc sans
jamais y entrer, faces extérieures aux couleurs de la coque, rien qui dépasse ; ailes puis segments un par un ;
déployée = planche de 1.23.0). Voir [PASSERELLES.md](PASSERELLES.md).

### Fonctions communes (aperçu de placement, tableau de bord, inclinaison, permissions, destinations)

`SharedFeaturesGameTest` (≈ 2 min de jeu, en solo **et** sur serveur dédié, avec et sans Lithium et
avec les mods de décoration) :

* **aperçu** : objet du dirigeable steampunk en main au-dessus d'un terrain dégagé → silhouette
  **verte** ; le serveur, avec la même visée et le même cap, trouve **exactement le même
  emplacement** (0,000000 bloc d'écart) ; le clic droit pose le dirigeable **exactement sur la
  silhouette** (moins de 0,01 bloc, même cap : le clic part du même point arrondi que l'aperçu) ;
  ensuite l'emplacement n'est plus montré libre ; entre deux
  murs de pierre trop rapprochés pour le ballon → silhouette **rouge**, et le clic droit **ne pose rien** ; plus de
  silhouette une fois l'objet rangé (captures `partage_1_apercu_vert`, `partage_2_apercu_rouge`) ;
* **permissions** : avec `placeAdminOnly: ["steampunk_airship"]` envoyé par le serveur au client (comme
  après `/ship reload`), le joueur de test (qui n'est pas administrateur, en solo comme sur le serveur
  dédié) voit une silhouette **grise** (`partage_2b_apercu_non_autorise`) et **ne peut pas** poser le
  dirigeable ; la règle levée, la silhouette redevient plaçable ;
* **navire sur l'eau** : dans un bassin creusé dans la plaine, l'objet de la galère montre une
  silhouette verte sur l'eau (`partage_7_apercu_navire_eau`), le serveur trouve le même emplacement et
  le clic droit pose la galère exactement dessus ;
* **tableau de bord** : un joueur sur le pont (pas à la barre) ne voit **rien** ; le pilote voit
  vitesse, altitude, montée/palier, moteur, pilote automatique et touches **telles qu'elles sont
  réglées dans ses options** (`partage_3_hud_pilote`) ; une limite `/ship speed 2` s'affiche
  (« Limite : 2,0 blocs/s ») ;
* **destination** : le pilote (non administrateur) tape `/pilote goto x y z` (45 blocs devant, 6 plus
  haut) → le pilote automatique prend la barre sur son propre itinéraire `goto-…`, le tableau de bord
  du joueur resté près de la barre affiche « Pilote auto : en route vers … (44 blocs) » et « Clic
  droit sur la barre : reprendre la main » (`partage_4_hud_pilote_auto`) ; le dirigeable arrive
  (phase *arrivé*, à 1,5 bloc du point, pont à 0,1 bloc de la hauteur demandée) avec le joueur à bord ;
  reprendre la barre annule la destination, efface son itinéraire et installe le joueur à la barre ;
* **garde-fous de `/pilote`** (joueur non administrateur) : au-delà de `playerDestinationMaxDistance`
  (réglé à 16 pour le test) la destination est refusée ; la destination d'un joueur n'est **pas** un
  ferry (après 5 s : aucun enregistrement pour le redémarrage, donc aucun chunk chargé pour elle) ;
  sauvegardée puis relue avec le code de sauvegarde des entités du jeu, elle est intacte (itinéraire,
  phase, auteur) ; `/pilote stop` l'annule ; celle d'un administrateur est menée comme un ferry
  (enregistrement présent) et relue comme telle ; un dirigeable affecté à l'itinéraire d'un
  administrateur ne peut pas être dérouté, ni en route, ni arrêté par `/ship ai disable` (il garde son
  itinéraire) ;
* **destinations d'un navire** (joueur à bord de la galère) : un point à terre sans eau à moins de 32
  blocs est refusé ; un point à 5 blocs du bord du bassin est ramené dans l'eau libre la plus proche ;
  le joueur descend à terre : 5 s plus tard la destination tient toujours, après 12 s elle est
  **annulée** (plus personne à bord pendant 10 s) ;
* **inclinaison** : dirigeable steampunk et Léviathan des Cieux en boucle sur un cercle (pilote
  automatique), un joueur **debout puis marchant** sur le pont : le steampunk tourne de 140° en 18 s
  et s'incline jusqu'à **4,5°** (borne 6°), le Léviathan tourne de 76° et s'incline de **1,0°** (sa
  borne) ; le client l'incline **du côté intérieur du virage** (tribord vers le bas dans ce virage à
  droite, contrôlé sur les échantillons du client) ; comme l'inclinaison n'est que dessinée, le pont
  où l'on se tient reste à plat et le joueur **reste sur le pont**, à 0,000 bloc de sa hauteur
  (`partage_5_inclinaison_*` à bord, `partage_6_inclinaison_dehors_*` de l'extérieur).

Tests unitaires (`SharedFeaturesTest`, 20 tests) : règles de permission (défaut, `placeRequiresAdmin`,
`placeAllowedPlayers` par pseudo ou UUID, `placeAdminOnly` avec alias et noms inconnus signalés,
ancien fichier de configuration sans les nouvelles clés) ; inclinaison (sens, virage sur place et
marche arrière, borne, lissage ; la transformation même du rendu, `Flight.bankPoint`, appliquée à
pleine inclinaison à chaque cellule praticable et aux bords du pont de chaque aéronef : aucune ne
bouge de plus d'un demi-bloc — ce test a trouvé que l'ancienne borne `asin(0,5/r)` laissait 0,50002
bloc sur le Léviathan, corrigée en `2 asin(0,5/2r)` ; tribord vers le bas dans un virage à droite ;
`bankAngle: 0` la coupe) ; tableau de bord (aéronef, navire, sous-marin, pilote automatique, pluriels
français, touches d'un clavier QWERTY, limite de vitesse et moteur « bridé à la limite ») ; destinations (itinéraire d'un point,
préfixe réservé, chaque refus de `/pilote` : ferry en route ou arrêté, autre pilote, distance,
Nautilus ; vol du dirigeable par-dessus un mur de 20 blocs jusqu'au point puis atterrissage à sa
garde, sans jamais toucher le relief ; navigation d'une galère jusqu'à son point ; une galère envoyée
dans les terres est déclarée bloquée, ce qui fait annuler la destination, sans jamais toucher la
côte) ; contrôle d'espace à arrêt précoce identique au comptage complet sur tous les navires.

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

### Nautilus — 1.7.0

Le scénario tourne dans un bassin de 28 × 142 blocs, profond de 26 blocs et fermé par des vitres. Il est joué **en solo puis sur un serveur dédié**, en quatre variantes :

* **sans** Lithium ;
* **avec** Lithium ;
* **avec Sodium** (depuis 1.28.1 : le maillage des tronçons par Sodium, pour l'eau cachée dans les pièces) ;
* **avec les mods de décoration**. Furnish, Farmhouse Decorations et Farmer's Delight Refabricated sont téléchargés depuis Modrinth pour le test seulement ; Fabric Loader 0.19.5 est nécessaire à ces mods. Le journal du jeu indique alors « 172 des 188 meubles dessinés depuis les mods installés ». Les 16 autres (Lands of Icaria, introuvable sur Modrinth, et Mebahel, non public) sont remplacés par leurs volumes de remplacement.

Ce qui est vérifié :

* **Mise à l'eau** : il flotte à sa ligne de flottaison et ne touche rien.
* **Déplacements à bord** :
  * marche sur le pont principal ;
  * pont inférieur **sec sous la ligne de flottaison** : pas d'eau, pas de vue sous-marine, l'air reste plein ;
  * depuis 1.28.0, en surface : caméra sur l'échelle de la salle des machines 0,4 bloc sous le niveau de la mer, hors de l'eau
    pour le brouillard (`NONE`), capture `nautilus_cale_niveau_mer` (relue depuis 1.28.1 : moins de 4 % de pixels bleus), et
    aucun bloc d'eau du bassin dessiné dans la coque ;
  * montée de **l'escalier en colimaçon** ;
  * **échelle** jusque sous le panneau fermé, puis sortie sur la coque une fois le panneau ouvert.
* **Plongée** :
  * il refuse de plonger **panneau ouvert** ;
  * il plonge sur commande (14 blocs) et **tient sa profondeur** (au millième) ;
  * le panneau ne s'ouvre pas sous l'eau ;
  * il navigue en plongée en emportant un porte-armure debout dans une salle ;
  * **salles sèches en plongée** (pas d'eau, pas de vue sous-marine, air plein), et on y marche ;
  * il remonte en surface.
* **Équipements** :
  * un **clic sur le levier** du salon ferme les panneaux des baies, et la commande les rouvre ;
  * un **clic sur le canapé** fait asseoir le joueur ;
  * `/ship nautilus lumieres off` éteint les lampes.
* **Sas, cycle complet** :
  1. la porte extérieure reste fermée tant que le sas est sec ;
  2. rempli, le joueur y est sous l'eau et la porte intérieure reste fermée ;
  3. plein, la porte extérieure s'ouvre sur la mer, et les pompes refusent de démarrer tant qu'elle est ouverte ;
  4. vidé, le joueur est de nouveau au sec et la porte intérieure s'ouvre.
* **Canot** : mis à l'eau le long de la coque, puis rembarqué.
* **Profondeur commandée** : `/ship nautilus profondeur 10` l'amène à 9,94 m, et `ballasts vider` le ramène en surface.
* **Itinéraire en 3D** : d'une escale en surface à une escale à 9 blocs sous l'eau, il plonge en chemin, s'arrête à l'escale à 8,93 m et ne touche jamais le bassin.
* **Redémarrage du monde** (solo : le monde est fermé puis rouvert). Le Nautilus retrouve :
  * sa position et sa profondeur ;
  * ses portes ouvertes et fermées ;
  * le sas à moitié plein ;
  * les panneaux fermés, le projecteur allumé et les lampes éteintes ;
  * le canot à l'eau, qui reste rembarquable ;
  * l'ordre de profondeur.
* **Objet** : `/ship give nautilus`, puis clic droit sur l'eau.
* **Captures** :
  * vues extérieures, en surface et en plongée à travers la vitre du bassin ;
  * les **15 panneaux** de la planche ;
  * panneaux des baies fermés, lumières éteintes, sas ouvert sur la mer, sas qui se vide, faisceau du projecteur, canot à l'eau, après redémarrage.

  Elles servent aux planches `docs/comparaison_nautilus_exterieur.png` et `docs/comparaison_nautilus_interieur.png`.

Tests unitaires (`NautilusTest`, 16 tests) :

* forme et dimensions, salles et allées, portes, escalier, échelles, sauvetage ;
* grille relue à l'identique ;
* plongée, maintien de profondeur et fond infranchissable ;
* leviers cliquables et vanne inaccessible à travers une cloison ;
* **eau du sas qui monte** (sous l'eau en dessous du niveau, au sec au-dessus) ;
* **pilote automatique** :
  * croisière à 24 blocs, remontée au-dessus d'une crête avant de l'atteindre, retour en surface à l'escale ;
  * étape à profondeur imposée ;
  * **refus d'un passage de 6 blocs** (plus étroit que la coque) et passage par un couloir de 40 blocs ;
  * escale sous-marine dans le bassin du test en jeu.

Non vérifié automatiquement :

* **plusieurs joueurs réels** à bord en même temps (le test n'a qu'un client) ;
* les **sons**, joués côté client et inaudibles pour le test ;
* le rendu avec **Embeddium** (plus publié pour Fabric 1.21.x) ou **VulkanMod** (moteur entièrement différent, incompatible
  avec Sodium) : l'eau du monde pourrait y rester visible dans les salles qui traversent la ligne de flottaison ; Sodium,
  Iris et Nvidium (qui maillent par Sodium) passent par le gestionnaire de fluides de Fabric API, vérifié par la variante
  `sodium` (voir ci-dessous) ;
* un long voyage automatique en vraie mer, avec récifs et hauts-fonds (seuls les tests unitaires le couvrent) ;
* les meubles de **Lands of Icaria** et de **Mebahel** dessinés depuis leurs mods (absents du test).

### Eau du monde cachée dans les pièces, avec Sodium (1.28.1)

Sur le serveur de l'utilisateur (client avec Sodium), la nappe de la mer restait visible dans la cale du navire au lion
malgré 1.28.0 : Sodium remplace le maillage des tronçons et n'appelle jamais le `FluidRenderer` de Minecraft, sur lequel
portait le mixin. Vérifié dans les sources de Sodium `mc1.21.11-0.8.14` (`fabric/src/main/java/net/caffeinemc/mods/sodium/
fabric/render/FluidRendererImpl.java`) et, à chaque exécution de la variante `sodium`, par `javap` sur le `.jar` téléchargé
(`sodium-fluid-renderer.txt` publié avec les résultats) : `FluidRendererImpl.render` lit le gestionnaire dans
`FluidRenderHandlerRegistry` et appelle `FluidRendering.render(handler, …)`, donc `FluidRenderHandler#renderFluid`, avec son
propre moteur comme géométrie par défaut. Le mod enregistre donc depuis 1.28.1 un gestionnaire pour l'eau qui saute les
blocs cachés et délègue tout le reste au gestionnaire précédent (`DryWaterFluidHandler`) ; le mixin reste en secours sans
Sodium.

Ce que vérifie la variante `sodium` (mêmes vérifications que `vanilla`, sur le moteur de Sodium) : le comptage des blocs
d'eau cachés par la règle, et surtout la relecture des captures `<id>_cale_niveau_mer` (nautilus, Vieux Corsaire, navire
au lion, forteresse, vapeur à engrenages, en solo et sur serveur dédié) : moins de 4 % de pixels bleus dans le cadre.
Les captures sont aussi à regarder : aucune nappe d'eau ne doit traverser la cale.

Filets de sécurité (`DryWater.tick`), indépendants du moteur : second redessin des sections autour d'un navire 2 s après
sa première apparition ; tant que le joueur est dans une pièce sèche à moins de 3 blocs de la surface de l'eau, toutes
les 5 s les sections de la bande d'eau autour de la coque (de 3 blocs sous la surface à la couche du bloc d'eau le plus
haut) qui n'ont pas été maillées depuis le dernier redessin (chaque section maillée avec une coque à portée est horodatée)
sont replanifiées, une seule fois par redessin : la planification horodate la section, car une section sans bloc d'eau
près de la coque (quai, terre) n'est jamais horodatée par le maillage et serait sinon remaillée à chaque vérification. Un tronçon qui se charge près d'un navire déjà
suivi est maillé après la publication de l'instantané (fin du tick client ; le maillage a lieu au rendu qui suit), donc
avec la coque : rien à faire pour `ClientChunkEvents.CHUNK_LOAD` ; un navire arrivé dans le même lot qu'un tronçon est
couvert par le redessin de sa première apparition, puis par le second.

Non couvert : Embeddium (absent pour Fabric 1.21.x) et VulkanMod. Un autre mod dont le point d'entrée client passe
après le nôtre et qui enregistre son propre gestionnaire pour l'eau le remplace dans le registre de Fabric API : le
nôtre est réinstallé à chaque connexion à un monde (`ClientPlayConnectionEvents.JOIN`), autour du gestionnaire trouvé
(idempotent : un gestionnaire déjà enveloppé est laissé tel quel). Reste non couvert un mod qui enregistrerait le sien
*après* la connexion (sans Sodium, le mixin prend le relais ; avec Sodium, l'eau redeviendrait visible dans les pièces).

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

0. **Fonctions communes** : l'aperçu a été testé en jeu avec le dirigeable steampunk et la galère (le
   calcul est le même pour tous). Si l'administrateur change le niveau de permission d'un joueur, le
   client le sait (le jeu le lui envoie) ; si la configuration change sans `/ship reload`, la
   silhouette peut se tromper jusqu'au prochain envoi (le serveur décide toujours). L'inclinaison est
   visuelle : sur le dessus d'un ballon (où l'on peut se tenir), le décalage visuel peut dépasser le
   demi-bloc garanti sur les ponts et dans les pièces. L'abandon d'une destination inaccessible est
   testé par le test unitaire du pilote automatique (il faut 50 s sans progrès), pas en jeu. Une
   destination d'administrateur charge les chunks de son trajet jusqu'à l'arrivée, comme un ferry ;
   un point d'arrivée dont les chunks ne sont pas chargés n'est pas vérifié (un navire qui ne peut pas
   l'atteindre abandonne). Le test multijoueur à deux (un autre joueur à la barre) n'est couvert que
   par le test unitaire des refus.

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
