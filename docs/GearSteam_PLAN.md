# Le Navire à vapeur à engrenages (`gear_steamship`) — plan

Navire de la ville **Haut-Arsenal (probable)** : l'emblème de l'engrenage doré est celui de la tente marchande
« Arsenal » (`tente_arsenal`), d'où l'attribution, à confirmer par le joueur.

Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical (0 = ligne de flottaison), z longitudinal
(+z = proue). Sources : `tools/gear_steam_shape.py` (forme, niveaux, mâts, cheminée, dôme, grue), `tools/gear_steam_interior.py`
(grille des pièces), `tools/generate_gear_steam.py` (modèle, gréement, animations), `tools/gear_steam_decor.py` (mobilier,
sièges), `tools/gear_steam_texture.py` (textures), `tools/gear_steam_gangplank.py` (passerelle),
`tools/gear_steam_compare.py` (comparaison caméra calée sur la référence), `GearSteamLayout.java` (mêmes nombres).

Règle permanente du joueur pour ce mod : **pas de Valkyrien Skies (ni Eureka), pas de GeckoLib** ; le navire utilise le
système de navires du mod (entité, grille intérieure, modèle Blockbench lu par le mod), aucune apparition naturelle.

## 1. Mesures relevées sur la référence

Une seule image (`ref2/gear_steamship_1_img063.png`, 1672 × 941 px) : vue de tribord, un peu en avant du travers,
proue à droite, coucher de soleil. **Le flanc bâbord est reconstruit en miroir du flanc tribord** (tuyaux, engrenages,
fenêtres, échelles, bandes) ; l'arrière (tableau, galerie vue de dos), l'avant de face, le pont vu de dessus et tout
l'intérieur sont reconstruits (voir § 7).

Méthode : la perspective est estimée sur la taille apparente des blocs (≈ 22 px à la poupe, ≈ 30 px à la proue :
rapport 1,33), les positions le long de la coque sont ramenées en z par une transformation projective de la ligne
de flottaison (poupe x ≈ 100 px → étrave x ≈ 1500 px), les hauteurs par l'échelle verticale locale ; puis une caméra
est **calée par moindres carrés sur 12 points** (étrave à la flottaison, coin de la galerie, haut de la cheminée,
nids de pie, centre du grand engrenage, engrenage de proue, bout du bout-dehors, haut du dôme, cassure du gaillard,
caisse suspendue, tête de proue) : résidu moyen ≈ 14 px sur 1672 (`tools/gear_steam_compare.py`, oeil (-38, 12,6, 14,7),
cap 106°, champ 40°).

| Élément | Mesure sur l'image | Retenu |
| --- | --- | --- |
| Coque | flottaison x 210 → 1350 px (81 % de la longueur au pont) ; francs-bords : passavant 4,8, gaillard 6,5, dunette 7,0 blocs (échelle locale) | **42 blocs** de la galerie de poupe à la tête de proue (45 avec le bout-dehors), 35 à la flottaison, **10 de large** |
| Étrave | très inclinée, bande de laiton de la flottaison (x 1340) à la tête (x 1500, y 10,9) | élancement 0,3 bloc par bloc de hauteur jusqu'à 11 ; tête de proue à y 10,9, z 22 |
| Bout-dehors + lanterne | 120 px vers l'avant, lanterne sur chaîne 1,8 bloc sous lui | espar cuivré jusqu'à z 25,2, grande lanterne (bone `lantern_bow`) |
| Grand engrenage | Ø 130 px, centre (640, 560) | Ø 4 blocs, centre y 4,5, z −0,4, des deux côtés |
| Engrenage de proue | Ø 85 px, centre (1320, 545) | Ø 2,2 blocs, y 5,8, z 17,4 |
| Fenêtres de coque | 2 carrées lumineuses (x 720–855) sous la bande, 2 sous la dunette (x 260–330) | 1,55 bloc (cale, y 3,0, z 2,9 et 5,0) ; 1,15 × 1,45 (quartiers, y 5,65, z −15,1 et −13,3), cadres de laiton |
| Bandes | cuivre riveté bas (≈ 1,8 → 2,2 bloc), décrochements de laiton vers 4,5 au milieu et 3,4 à l'avant, liston cuivré au ras de l'eau | idem, en bandes saillantes rivetées + montants de laiton (décrochements) |
| Tuyaux | coude sortant du flanc arrière, course basse vers le grand engrenage, tuyau vertical dans l'eau ; grand U renversé sur la maison des machines | idem des deux côtés (Ø 0,7 et 1,0), brides de laiton |
| Cheminée | x 485–570, sommet y ≈ 100 px, bague de laiton aux 2/3 | Ø 2,8, de 9,0 à 18,0, bague à 14,0, chapeau évasé à liseré cuivre |
| Dôme | tambour x 600–770, chapeau cuivré à côtes de laiton, garde-corps rond au sommet | tambour Ø 5,7 de 9,0 à 12,4, dôme jusqu'à 14,2, couronne-garde-corps Ø 2,9 |
| Rouf du capitaine | 3 fenêtres éclairées (x 355–500), toit à garde-corps, lanterne | rouf 6 × 7 sur la dunette (7,5 → 11), 3 fenêtres par bord, passerelle de commandement (11,0) sur le toit |
| Grand mât | x ≈ 960, haut coupé par l'image (≈ 27 blocs bruts), cage au sommet, collier de laiton | z 7,5, sommet 19,6, cage 18,5 → 20 ; vergue à 17,2 |
| Grand-voile | noire, liseré doré à droite et en bas, montant doré à 31 %, engrenage doré Ø 36 % ; son pied passe au-dessus du toit des machines | 10,4 × 6,6 (vergue 17,2, pied 10,6), coupée en trapèze (bas plus étroit), engrenage à 8 rayons et 10 dents |
| Artimon | x ≈ 270, sommet ≈ 23 bruts, petite cage, voile étroite | z −15,9, sommet 18, cage 16,9 → 18,1 ; voile 3,9 × 5,1 (montant doré à 25 %, sans emblème comme sur l'image) |
| Vergues | inclinées (extrémité arrière plus haute, ≈ 19° apparents) | brassées de 62° (bras tribord vers l'arrière) et apiquées de 22° (bout tribord plus haut) |
| Grue | poteau sur la dunette arrière, flèche vers l'arrière, caisse sur 2 chaînes (x 63–130, y 395–435) | poteau z −18,8, flèche jusqu'à z −23,6 / y 12,8, caisse 1,7 × 1,3 × 1,6 à y 7,2–8,5 |
| Galerie de poupe | balcon sous le surplomb de la dunette, engrenage et lanterne sur ses faces | galerie z −20 → −17,5 (plancher 4,5), toit = la dunette prolongée sur deux poteaux |
| Échelles | échelle de corde sur le flanc de la dunette, échelle depuis l'eau | idem (décoratives) + échelles praticables (grille) vers le toit des machines et la passerelle |
| Gréement | chaînes sombres « en escalier » | haubans en échelles de chaîne (cubes en escalier + barreaux), étai vers la tête de proue, chaînes vers la passerelle, le dôme et la grue |

## 2. Dimensions retenues

Coque 42 × 10 blocs (45 avec le bout-dehors, la caisse pend jusqu'à z −24,4), quille −3,0, du fond au sommet de la cage du
grand mât ≈ 23 blocs. Comparée aux autres grands navires de `core/Ships.java` : un peu plus courte que la frégate bleue
(46 hors tout) mais plus haute de francs-bords et beaucoup plus massive au-dessus du pont (maison des machines, rouf,
cheminée), plus basse de mâture (vapeur). Coque presque droite (légère rentrée de 0,1), fond arrondi, étrave élancée,
voûte arrière (le fond remonte à 2 blocs sous le tableau, la coque quitte l'eau vers z −16).

## 3. Niveaux et pièces

| Niveau | y | Contenu |
| --- | --- | --- |
| Passerelle (toit du rouf) | 11,0 | barre à roue (z −8,5, pilote debout z −9,3), habitacle, porte-voix, garde-corps, deux lanternes ; échelle depuis la dunette (bâbord, mur arrière du rouf) |
| Toit de la maison des machines | 9,0 | cheminée (z −5,6), dôme (z −0,9), engrenages qui tournent, garde-corps ; échelles depuis le passavant (deux, mur avant) ; trois marches de chaque côté vers la dunette |
| Dunette | 7,5 | rouf du capitaine, artimon, grue, prolongée sur la galerie ; garde-corps et lanternes |
| Cabine du capitaine | 7,5 | le rouf (z −13,5 → −7,5, 3 de haut) : couchette, bureau et fauteuil, coffre ; porte arrière (porte 3) |
| Gaillard d'avant | 6,0 | deux escaliers depuis le passavant, banc, lanternes, tête de proue |
| Passavant (pont principal) | 4,5 | entre la maison des machines (z 5) et le gaillard (z 11,5) : grand mât, descente bâbord vers la cale, passerelle d'embarquement tribord |
| Salle des machines | 4,5 | toute la largeur de la maison (z −6 → 4,5), 3,5 de haut : chaudière lumineuse sous la cheminée (meuble solide), escalier tribord vers la cale ; porte avant (0, sur le passavant), porte arrière bâbord (1, quartiers) |
| Quartiers de l'équipage | 4,5 | sous la dunette (z −17 → −7, 2,5 de haut) : table, deux bancs, couchettes ; porte arrière (2) sur la galerie |
| Galerie de poupe | 4,5 | balcon ouvert sous le surplomb |
| Cale | 1,0 | sous le passavant, la salle des machines et les quartiers (z −15,5 → 15, 3 de haut) : tonneaux |

Toutes les pièces et tous les ponts sont atteignables (rapport de `gear_steam_interior.py` et `GearSteamShipTest`).

## 4. Sièges

20 places : le pilote (debout à la barre de la passerelle) et 19 sièges posés par le mobilier (§ 10) : le fauteuil du
capitaine à son bureau et une chaise de visiteur, huit places aux bancs de la table du carré, le tabouret du chauffeur
devant le foyer, deux places au banc des officiers sur la passerelle, une au banc de la dunette (contre le rouf), deux aux
bancs du gaillard, trois aux bancs de la galerie de poupe. Chaque siège a sa place pour se relever, libre et sur un
plancher (vérifié par `GearSteamShipTest`).

## 5. Matériaux, parties mobiles, contraintes

* **Matériaux** (atlas 512 px + atlas des voiles 512 px) : tôles de fer noires rivetées « un bloc = une plaque » (trois
  teintes, rouille par endroits), bandes de cuivre rivetées, laiton poli, assise de pierre sombre au toit des machines,
  tuyaux de cuivre, dôme de cuivre riveté (un peu de vert-de-gris), cheminée noire à rivets, fenêtres carrées orange en
  cadre de laiton, bois sombre (mâts, garde-corps à poteaux coiffés de laiton), chaînes sombres, voiles noires en
  cellules de toile (ventre plus clair), liseré et engrenage dorés ; intérieur : fer riveté et tôle striée (machines),
  lambris sombre à baguette de laiton (cabine), planches (quartiers, cale).
* **Parties mobiles** : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran (`steer`), **engrenages** (`gear_*` :
  animation `engine`, jouée par le mod sur la distance parcourue : un quart de tour par seconde à l'allure normale, les
  voisins tournent en sens inverse), lanternes et caisse de la grue (`lantern_sway`), portes (`door_0` … `door_3`) ; dans la salle des machines, le volant et
  le vilebrequin (`gear_flywheel`) et les deux pistons (`piston_0`, `piston_1`), joués par la même animation `engine`.
* **Effets** (`GearSteamEffects`, client, près du joueur) : fumée de la cheminée (filet au repos, panache sous vapeur),
  bouffées de vapeur du dôme, battement de la machine (plus rapide avec la vitesse), crépitement du foyer, remous de
  l'hélice sous la voûte, grincements de la coque et du gréement ; écume d'étrave générique.
* **Contraintes** : coque et pièces dessinées sur la grille (ce qui est dessiné est ce qui collisionne) ; rien ne sort de
  la coque sous le pont (test) ; sondes du pilote automatique au bout-dehors et à sa lanterne, à la tête de proue, à la
  grue et à sa caisse, aux coins de la galerie, au safran et aux bouts des vergues (brassées et apiquées).
* **Physique** : vapeur lourd : accélération 0,26, freinage 0,5, virage 6,5°/s, erre longue (`waterDrag` 0,06), allure
  normale 3,8 (rapide 6,2), roulis 0,6 ; pilote automatique comme la frégate (rayon 14, anticipation 28, sondes 75).

## 6. Guide du joueur

* Objet *Navire à vapeur à engrenages* (*Gear Steamship*) dans l'onglet *Navires médiévaux*, ou
  `/ship give gear_steamship` ; clic droit sur l'eau (≈ 48 × 10 blocs d'eau libre, quille à 3 sous la surface) ;
  `/ship spawn gear_steamship`.
* **Monter à bord** : clic droit sur la coque (on arrive sur le passavant) ou par la **passerelle d'embarquement**
  (levier sur le passavant tribord, à l'arrière du portillon du garde-corps).
* **Circuler** : portes au clic droit ; échelles (avancer contre l'échelle pour grimper) du passavant au toit des
  machines et de la dunette à la passerelle ; marches du toit des machines à la dunette ; escaliers vers le gaillard,
  vers la cale (passavant et salle des machines).
* **Piloter** : clic droit sur la roue de la passerelle ; commandes habituelles du mod ; les engrenages tournent, la
  cheminée fume et la machine bat sous vapeur. Pilote automatique : `/ship route …` comme les autres navires.
* **Réglages** : bloc `ships.gear_steamship` de `config/medievalships.json`.

## 7. Parties reconstruites (absentes de l'image)

Flanc bâbord (miroir), arrière vu de dos (tableau plat, bande de cuivre, galerie et surplomb), avant vu de face, pont vu de
dessus (planches, panneau de descente, cheminée et dôme centrés), safran sous la voûte, intérieur complet ; l'hélice
n'est pas dessinée (sous l'eau, invisible sur l'image, seul le remous la suggère).

## 8. Différences restantes avec la référence (fin de phase 1)

* La caméra calée laisse ≈ 14 px d'écart moyen : la galerie et la caisse sont à ± 1 bloc de leur place, la cheminée
  ≈ 0,7 bloc trop en avant (elle est collée au rouf, qu'on ne pouvait pas traverser sans casser la cabine).
* Coque lisse là où l'image montre des blocs « en escalier » sur les fonds de proue et de poupe (choix du brief : pas de
  coque en blocs carrés) ; plaques rivetées peintes dans la texture.
* L'image est un rendu IA : les vergues y semblent plus apiquées et la grand-voile plus étroite au pied ; on a gardé une
  voile carrée crédible (brassée + apiquée), lisible des deux bords.
* La lumière de coucher de soleil n'est évidemment pas reproduite ; les fenêtres et lanternes sont pleine lumière.

## 9. Fichiers et tests

* Modèle `blockbench/gear_steamship.bbmodel` et `models/entity/gear_steamship.bbmodel` (≈ 4 900 cubes, 2 textures,
  9 animations), textures `textures/entity/gear_steamship.png` et `gear_steamship_sails.png`, icône
  `textures/item/gear_steamship.png`, grille `interiors/gear_steamship.grid`, mobilier `interiors/gear_steamship_decor.json`,
  passerelle `gangplanks/gear_steamship.json` + `models/entity/gangplank_gear_steamship.bbmodel` (style acier, 2,4 × 8 ;
  peau de camouflage = case du bateau à vapeur, mêmes couleurs ; l'atlas commun n'est pas modifié), référence
  `src/test/resources/gear_steamship_reference_quads.json` (réécrite par le générateur : **toujours relancer
  `python3 tools/generate_gear_steam.py` après une modification du modèle**), aperçu `docs/preview_gear_steamship.png`.
* Mobilier : `tools/gear_steam_decor.py` (placement, sièges, cases solides) et `tools/gear_steam_furniture.py` (pièces
  modélisées), § 10.
* Java : `GearSteamLayout`, `GearSteamShipEntity`, `GearSteamEffects` ; tests `GearSteamShipTest` (forme, dimensions,
  niveaux, pièces, escaliers et échelles, portes, sièges, mobilier, pièces meublées toutes atteignables, embarquement,
  passerelle, modèle, engrenages, volant et pistons) et
  `GearSteamShipGameTest` (en jeu : mise à l'eau, vues dont celle de la référence, photos des pièces meublées, chaque pont
  et chaque pièce, le fauteuil du capitaine (s'asseoir, se relever sur le plancher), marche, porte, passerelle sortie /
  rangée, barre, engrenages, fumée, sons) ; entrées dans `NoZFightingTest`,
  `NewShipModelsTest`, `GangplankSpecsTest`, `GangplankFoldTest`.
* Comparaison : `python3 tools/gear_steam_compare.py <référence> <sortie.png> [--zoom]` (référence au-dessus, rendu au
  même cadrage en dessous, points de calage, gros plans poupe / milieu / proue).

## 10. Mobilier et décoration (phase 2)

Les blocs des mods de décoration d'abord (Farmhouse Decorations, Furnish, Farmer's Delight, Lands of Icaria : 119 blocs,
dessinés par le navire là où ils sont, jamais posés dans le monde ; une boîte de remplacement de même taille quand le mod
manque) ; ce que les mods n'ont pas est modélisé dans `tools/gear_steam_furniture.py` (machine, soutes, tuyauterie,
instruments, accastillage). Les meubles solides sont dans la grille (cases FURNITURE) : on les contourne ; chaises,
bancs, tabourets et petits objets sur les tables ne le sont pas.

| Pièce / pont | Blocs des mods | Pièces modélisées |
| --- | --- | --- |
| Salle des machines | établi et panneau d'outils (Farmhouse), deux casiers d'acier (Furnish), tonneau d'huile à robinet (Icaria), tabouret du chauffeur, trois lanternes suspendues | **machine à vapeur à deux cylindres** (bâbord avant : socle riveté, paliers, colonnes en A, cylindres cerclés de laiton, coffre à vapeur ; le **volant et le vilebrequin tournent** avec la machine — bone `gear_flywheel`, deux tours par boucle de l'animation `engine` — et les **pistons montent et descendent** sur leurs manivelles, bones `piston_0` / `piston_1`), soute à charbon rivetée avec sa pelle (tribord arrière), tas de charbon devant le foyer, garde-corps de fer autour de la descente vers la cale, conduites de vapeur en cuivre au plafond (chaudière → coffre à vapeur, chaudière → manomètres) avec leurs vannes, deux tableaux de manomètres, leviers, transmetteur d'ordres (répétiteur du télégraphe), porte-voix, coffre à outils |
| Quartiers de l'équipage | table du carré en quatre éléments (Farmhouse) et huit bancs (Furnish), trois couchettes (lits simples Farmhouse, hors des fenêtres), quatre casiers (Furnish), armoire, portemanteau, guitare ; **cuisine** dans l'angle tribord arrière : fourneau en fonte avec bouilloire et marmites, plan de travail, marmite (Farmer's Delight), étagère à épices ; sur la table : assiettes, bouteilles, poulet rôti, lampe | chopes, tuyau du fourneau jusqu'au plafond, les quatre fenêtres vues de l'intérieur |
| Cabine du capitaine | lit (Farmhouse), grand bureau à plateau de cuir et fauteuil à haut dossier (Furnish), bibliothèque haute, cabinet à liqueurs, commode avec boîte à cigares et cadre, chaise de visiteur, tapis rond, coucou, lampe et livres sur le bureau | carte marine, compas, encrier, compas à pointes sur le bureau, carte murale au-dessus, les huit fenêtres vues de l'intérieur (trois par bord, deux à l'avant) |
| Cale | caisses en deux étages et sacs de riz (Furnish, Farmer's Delight) le long du bord bâbord, tonneaux couchés et tonneau à robinet (Icaria) le long du bord tribord, caisses sous les fenêtres, cinq lanternes ; l'axe reste libre | deux grandes soutes à charbon sous la salle des machines, engrenage de rechange appuyé au bordé, tubes de cuivre de rechange sur leurs cales, glène de chaîne, glène de cordage |
| Dunette | caisses empilées dans l'angle tribord arrière et sur le surplomb (la cargaison qui attend la grue, comme la caisse suspendue de l'image), tonneau couché, banc contre le rouf | glène de chaîne au pied de la grue |
| Passerelle | banc des officiers (deux places) | transmetteur d'ordres à la machine près de la barre |
| Toit des machines | — | deux manches à air de cuivre à pavillon, devant le dôme |
| Passavant | deux tonneaux contre le pavois bâbord, près de la descente | glène de cordage au pied du grand mât |
| Gaillard d'avant | deux caisses à bâbord, deux bancs à tribord | guindeau à vapeur (barbotins, freins de laiton, engrenage, petit cylindre, chaînes vers les écubiers), deux bittes d'amarrage, glène de chaîne |
| Galerie de poupe | trois bancs le long de la lisse arrière | — |

Gardés libres (tests et rapport de `tools/gear_steam_interior.py`) : les portes, les escaliers, les échelles, la marche de
la passerelle d'embarquement et le levier sur le passavant tribord, l'axe de la cale, les places où l'on se relève des
sièges ; toutes les pièces, tous les ponts et toutes ces places restent atteignables à pied depuis le passavant, portes
ouvertes (parcours en largeur sur la grille meublée : `GearSteamShipTest.furnishedRoomsAreConnected`). Rien ne dépasse de la
coque : le centre de chaque bloc est dans une case ouverte de sa pièce ou de son pont.

Textures : les régions des meubles (douelles, couvercles, coffres, tôle rivetée, cadrans, bocaux, outils, carte murale…)
sont recopiées de l'atlas intérieur du Léviathan (`tools/leviathan_texture.py`, lu seulement) dans l'atlas de la coque,
sous les mêmes noms « in_* », pour réutiliser les meubles de `tools/leviathan_furniture.py`.
