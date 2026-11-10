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
est **calée par moindres carrés sur 16 points** (étrave à la flottaison, coin arrière de la lisse de la galerie, haut de
la cheminée, nids de pie, centre du grand engrenage, engrenage de proue, bout du bout-dehors, haut du dôme, cassure du
gaillard, caisse suspendue, tête de proue ; depuis la phase 4 aussi le coin arrière du toit du rouf, la fenêtre arrière
des quartiers, le coude avant du grand U de cuivre et la fenêtre avant de la cale, pour que le calage ne compense plus les
erreurs de la poupe par la perspective) : résidu moyen ≈ 12 px sur 1672 (`tools/gear_steam_compare.py`, oeil
(-48,9, 11,7, 18,6), cap 107°, champ 31°). En phase 4 deux points ont été mesurés de nouveau : le haut de la cheminée est
à x 545 px (et non 527 : c'était son bord gauche) et le coin de la galerie à (107, 462) (lisse arrière).

| Élément | Mesure sur l'image | Retenu |
| --- | --- | --- |
| Coque | flottaison x 210 → 1350 px (81 % de la longueur au pont) ; francs-bords : passavant 4,8, gaillard 6,5, dunette 7,0 blocs (échelle locale) | **42 blocs** de la galerie de poupe à la tête de proue (45 avec le bout-dehors), 35 à la flottaison, **10 de large** ; 1.28.0 : l'eau est à y 0,6 du modèle (quille à 3,6 dessous, plancher de la cale 0,4 au-dessus) |
| Étrave | très inclinée, bande de laiton de la flottaison (x 1340) à la tête (x 1500, y 10,9) | élancement 0,3 bloc par bloc de hauteur jusqu'à 11 ; tête de proue à y 10,9, z 22 |
| Bout-dehors + lanterne | 120 px vers l'avant, lanterne sur chaîne 1,8 bloc sous lui | espar cuivré jusqu'à z 25,2, grande lanterne (bone `lantern_bow`) |
| Grand engrenage | Ø 130 px, centre (640, 560) | Ø 4 blocs, centre y 4,5, z −0,4, des deux côtés |
| Engrenage de proue | Ø 85 px, centre (1320, 545) | Ø 2,2 blocs, y 5,8, z 17,4 |
| Fenêtres de coque | 2 carrées lumineuses (x 720–855) sous la bande, 2 sous la dunette (x 260–330) | 1,55 bloc (cale, y 3,0, z 2,9 et 5,0) ; 1,15 × 1,45 (quartiers, y 5,65, z −12,6 et −10,8 : phase 4, sous le rouf comme sur l'image), cadres de laiton |
| Bandes | cuivre riveté bas (≈ 1,8 → 2,2 bloc), décrochements de laiton vers 4,5 au milieu et 3,4 à l'avant, liston cuivré au ras de l'eau | idem, en bandes saillantes rivetées + montants de laiton (décrochements) ; liston de cuivre de −0,15 à 0,75 (visible au-dessus de l'eau, phase 4) |
| Rangs en gradins | sous la bande, les rangs de plaques de l'avant reculent rang par rang vers l'étrave ; la voûte arrière descend en escalier de la galerie (y ≈ 3,4, z ≈ −19,5) à l'eau (z ≈ −15,7), rangs ≈ 0,7 × 0,8 | phase 4 : quatre rangs d'un bloc à l'avant (hauts 0,75 / 1,62 / 2,48 / 3,35), chacun droit, son bout avant 0,52 en retrait de celui du dessus (blocs de laiton de l'étrave en escalier) ; voûte en rangs de 0,7 (pente 0,9) jusque sous la galerie |
| Tuyaux | coude sortant du flanc arrière, course basse vers le grand engrenage, tuyau vertical dans l'eau ; grand U renversé sur la maison des machines | idem des deux côtés (Ø 0,7 et 1,0), brides de laiton |
| Cheminée | chapeau x 482–607 (centre 545), sommet y ≈ 100 px, bague de laiton de 13,9 à 14,8 | Ø 2,8, de 9,0 à 18,0, z −5,6 (à sa place par rapport au dôme : écart 142 px sur l'image, 141 au rendu), bague à 14,35 (0,9 de haut), chapeau à deux étages évasés à liserés cuivre ; elle monte à travers l'avant du rouf (phase 4) |
| Dôme | tambour x 600–770, chapeau cuivré à côtes de laiton, garde-corps rond au sommet | tambour Ø 5,7 de 9,0 à 12,4, calotte lisse (ellipse de révolution, 7 rangs de 20 plaques inclinées) jusqu'à 14,2, couronne-garde-corps Ø 2,9 |
| Rouf du capitaine | 3 fenêtres éclairées (x 367, 416, 483), coin arrière du toit x 314, la cheminée à son extrémité avant ; toit à garde-corps, lanterne | rouf 6 × 7 sur la dunette (7,5 → 11), z −12 → −5 (phase 4 : 2 blocs plus en avant), son avant posé sur le toit des machines et traversé par la cheminée ; 3 fenêtres par bord (z −10,25, −8,25, −6,25), passerelle de commandement (11,0) sur le toit |
| Grand mât | x ≈ 960, haut coupé par l'image (≈ 27 blocs bruts), cage au sommet, collier de laiton | z 7,5, sommet 19,6, cage 18,5 → 20 ; vergue à 17,2 |
| Grand-voile | noire, liseré doré à droite et en bas, montant doré à 31 %, engrenage doré Ø 36 % ; son pied passe au-dessus du toit des machines toile pendante (phase 3) : têtière le long de la vergue de x −3,6 à +5,85 (bras arrière nu), chutes verticales, chute 6,6 au guindant → 5,9 à la chute + ventre au point d'écoute avant, engrenage à 8 rayons et 10 dents peint rond |
| Artimon | x ≈ 270, sommet ≈ 23 bruts, petite cage, voile étroite | z −15,9, sommet 18, cage 16,9 → 18,1 ; voile pendante de x −1,75 à +3,25, haute de 4,3 au guindant et 2,4 à la chute (montant doré à 25 %, sans emblème comme sur l'image) |
| Vergues | inclinées (extrémité arrière plus haute, ≈ 19° apparents) | brassées de 62° (bras tribord vers l'arrière) et apiquées de 22° (bout tribord plus haut) ; demi-vergues 6,0 et 3,45 |
| Grue | haut socle sur le bord arrière de la dunette (chapiteau ≈ 2 blocs au-dessus du pont), poteau, flèche horizontale à jambe de force, caisse sur 2 chaînes (x 63–130, y 395–435) | socle de 2 blocs (z −18,0) à chapiteau, bandes de laiton et lampes ; poteau, flèche horizontale (y 13,35) jusqu'à z −23,0 avec jambe de force et entretoises, caisse 1,9 × 1,3 × 1,8 à y 7,4–8,7 |
| Galerie de poupe | balcon de ≈ 4 blocs (x 97–205) au bout de la coque, engrenage et lanterne sur ses faces ; la dunette s'arrête ≈ 1,5 bloc avant son bout, la voûte en escalier sous elle | galerie z −20 → −16 (plancher 4,5 ; phase 4 : la coque finit à −16 au lieu de −17,5), la dunette prolongée au-dessus jusqu'à −18,5 sur deux poteaux, l'arrière de la galerie à ciel ouvert ; voûte en gradins dessous |
| Échelles | échelle de corde sur le flanc de la dunette, échelle depuis l'eau | idem (décoratives) + échelles praticables (grille) vers le toit des machines et la passerelle |
| Gréement | chaînes sombres « en escalier » | haubans en échelles de chaîne (cubes en escalier + barreaux), étai vers la tête de proue, chaînes vers la passerelle, le dôme et la grue |

## 2. Dimensions retenues

Coque 42 × 10 blocs (45 avec le bout-dehors, la caisse pend jusqu'à z −24,0), quille −3,0, du fond au sommet de la cage du
grand mât ≈ 23 blocs. Comparée aux autres grands navires de `core/Ships.java` : un peu plus courte que la frégate bleue
(46 hors tout) mais plus haute de francs-bords et beaucoup plus massive au-dessus du pont (maison des machines, rouf,
cheminée), plus basse de mâture (vapeur). Coque presque droite (légère rentrée de 0,1), fond arrondi, étrave élancée,
voûte arrière en gradins (phase 4 : la coque quitte l'eau vers z −15,7, son tableau est à z −16, à 1,4 au-dessus de l'eau ;
les rangs de la voûte continuent sous la galerie jusqu'à son plancher).

## 3. Niveaux et pièces

| Niveau | y | Contenu |
| --- | --- | --- |
| Passerelle (toit du rouf) | 11,0 | barre à roue juste derrière la cheminée (z −7,75, pilote debout z −8,55), habitacle, porte-voix, garde-corps, deux lanternes ; échelle depuis la dunette (bâbord, mur arrière du rouf) ; l'avant du toit autour de la cheminée est fermé par un garde-corps |
| Toit de la maison des machines | 9,0 | cheminée (z −5,6), dôme (z −0,9), engrenages qui tournent, garde-corps ; échelles depuis le passavant (deux, mur avant) ; trois marches de chaque côté vers la dunette |
| Dunette | 7,5 | rouf du capitaine, artimon, grue (sur le bord arrière), prolongée sur la galerie jusqu'à z −18,5 ; garde-corps et lanternes |
| Cabine du capitaine | 7,5 | dans le rouf (z −11,5 → −7, 3 de haut ; son mur avant est le coffrage de la cheminée) : couchette, bureau et fauteuil, coffre ; porte arrière (porte 3) |
| Gaillard d'avant | 6,0 | deux escaliers depuis le passavant, banc, lanternes, tête de proue |
| Passavant (pont principal) | 4,5 | entre la maison des machines (z 5) et le gaillard (z 11,5) : grand mât, descente bâbord vers la cale, passerelle d'embarquement tribord |
| Salle des machines | 4,5 | toute la largeur de la maison (z −6 → 4,5), 3,5 de haut : chaudière lumineuse sous la cheminée (meuble solide), escalier tribord vers la cale ; porte avant (0, sur le passavant), porte arrière bâbord (1, quartiers) |
| Quartiers de l'équipage | 4,5 | sous la dunette (z −15,5 → −7, 2,5 de haut) : table, deux bancs, couchettes ; porte arrière (2) sur la galerie |
| Galerie de poupe | 4,5 | balcon de 4 blocs (z −20 → −16), à moitié sous le surplomb de la dunette, l'arrière à ciel ouvert |
| Cale | 1,0 | sous le passavant, la salle des machines et les quartiers (z −15,5 → 15, 3 de haut) : tonneaux |

Toutes les pièces et tous les ponts sont atteignables (rapport de `gear_steam_interior.py` et `GearSteamShipTest`).

## 4. Sièges

20 places : le pilote (debout à la barre de la passerelle) et 19 sièges posés par le mobilier (§ 10) : le fauteuil du
capitaine à son bureau et une chaise de visiteur, huit places aux bancs de la table du carré, le tabouret du chauffeur
devant le foyer, deux places au banc des officiers sur la passerelle, une au banc de la dunette (contre le rouf), deux aux
bancs du gaillard, trois aux bancs de la galerie de poupe. Chaque siège a sa place pour se relever, libre et sur un
plancher (vérifié par `GearSteamShipTest`).

## 5. Matériaux, parties mobiles, contraintes

* **Matériaux** (atlas 1024 px + atlas des voiles 1024 px, 32 px par bloc depuis la 1.27.1, § 13) : tôles de fer noires rivetées « un bloc = une plaque » (trois
  teintes, rouille par endroits), bandes de cuivre rivetées, laiton poli couleur bronze orangé (phase 4, comme l'image),
  poutre sombre boulonnée au toit des machines, tuyaux de cuivre, dôme de cuivre riveté (un peu de vert-de-gris) sur un
  tambour de cuivre brun sombre, cheminée noire à rivets, fenêtres carrées orange en
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

* Modèle `blockbench/gear_steamship.bbmodel` et `models/entity/gear_steamship.bbmodel` (≈ 6 200 cubes, 2 textures
  1024 × 1024, 9 animations), textures `textures/entity/gear_steamship.png` et `gear_steamship_sails.png`, icône
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
| Quartiers de l'équipage | table du carré en quatre éléments (Farmhouse) et huit bancs (Furnish), deux couchettes (lits simples Farmhouse, hors des fenêtres : une en travers du mur arrière à bâbord, une le long du bord tribord avant), quatre casiers (Furnish) contre la cloison avant, armoire le long du bord bâbord avant, portemanteau, guitare ; **cuisine** dans l'angle tribord arrière : fourneau en fonte avec bouilloire et marmites, plan de travail, marmite (Farmer's Delight), étagère à épices ; sur la table : assiettes, bouteilles, poulet rôti, lampe | chopes, tuyau du fourneau jusqu'au plafond, les quatre fenêtres vues de l'intérieur |
| Cabine du capitaine | lit (Farmhouse), grand bureau à plateau de cuir et fauteuil à haut dossier (Furnish), bibliothèque haute, cabinet à liqueurs, commode avec boîte à cigares et cadre, chaise de visiteur, tapis rond, coucou, lampe et livres sur le bureau | carte marine, compas, encrier, compas à pointes sur le bureau, carte murale au-dessus (sur le coffrage de la cheminée), les quatre fenêtres vues de l'intérieur (les deux arrière de chaque bord ; la troisième vitre éclaire le coffrage) |
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

## 11. Fidélité, phase 3 (regard neuf)

Rendus à la caméra de la référence (`tools/gear_steam_compare.py`, 12 points, ≈ 14,6 px d'écart moyen), comparés côte à
côte en vue entière et en gros plans poupe / milieu / proue : `docs/comparaison_gear_steamship.png` (référence à gauche,
modèle à droite). Différences relevées, de la plus visible à la moins visible, et ce qui a été fait :

1. **Grand-voile** (la plus grande surface de l'image) : en phase 2 c'était un rectangle tourné de 22° avec la vergue,
   chutes penchées, centré sur le mât et cachant le dôme. Sur l'image la toile **pend** de sa vergue apiquée : chutes
   verticales, têtière et bordure en escalier le long de la vergue, toile sur l'avant de la vergue (bras arrière nu),
   pied arrondi vers le point d'écoute avant. → Toiles refaites en colonnes de cases droites
   (`hanging_sail` / `hanging_patch`) : la bande dorée reste droite, l'engrenage est peint rond sur la toile inclinée
   (`gt.SAIL_COLUMNS`) ; serrée, chaque voile se rassemble entre son guindant et sa chute sur la vergue (échelle de
   ferlage calculée, les écoutes suivent).
2. **Artimon** : même défaut ; maintenant haut au guindant, court à la chute, comme sur l'image.
3. **Dôme** : il se lisait comme une pyramide à gradins de briques saumon. → Calotte lisse de plaques inclinées,
   cuivre sombre à rivets de laiton, côtes qui suivent la courbe.
4. **Couleurs** : cuivre saumon « neuf » → cuivre brun-rouge (bandes, tuyaux, dôme) ; tôles et voiles d'un noir chaud au
   lieu d'un gris-bleu ; plus de gris « pierre » : les rebords des toits (maison des machines, rouf) sont des poutres
   sombres à boulons de laiton.
5. **Proue** : murs pleins en gradins → cou incliné à face de laiton + arc-boutant en escalier d'un bloc d'épaisseur,
   ajouré dessous (le ciel passe entre lui et la lisse, comme sur l'image) ; l'étrave porte une large bande de laiton
   (joues des deux bords) de l'eau jusqu'à la tête ; pièce de laiton devant l'engrenage de proue, bande de cuivre plus
   bas, une seule course de cuivre en tête du gaillard.
6. **Rouf du capitaine** : les fenêtres étaient à moitié cachées par la lisse de la dunette. → Grandes fenêtres éclairées
   de 1,5 bloc, centrées à 9,85 (vues de l'intérieur à la même hauteur).
7. **Grue** : flèche en treillis (membrures, croisillons, boulons de laiton) au lieu d'un fin longeron ; caisse plus
   grande.
8. **Gréement** : les bras de la grand-vergue sont des chaînes « en escalier » (bras arrière vers la couronne du dôme,
   comme la grosse chaîne de l'image).

Restaient (classés ; traités en phase 4, § 12) :
* La poupe du modèle est ≈ 1,5 à 2 blocs plus longue que sur l'image : galerie, échelle de flanc, fenêtres des quartiers
  et rouf tombent un peu trop à gauche au même cadrage (changer la longueur toucherait la grille, Java, le mobilier).
* Cheminée ≈ 0,5 bloc trop en avant (collée au rouf).
* Coque lisse là où l'image montre des rangs de blocs en retrait sur les fonds de proue et de poupe.
* Socle de la grue moins haut que sur l'image ; tambour du dôme cuivré (plus sombre sur l'image).
* Lumière de coucher de soleil non reproduite (l'image est un rendu IA chaud).

## 12. Structure, phase 4 (poupe, cheminée, couleurs, rangs en gradins, grue)

Méthode : la caméra est calée sur 16 points (§ 1), dont quatre le long de la poupe et du milieu ; deux mesures de phase 1
ont été refaites (cheminée 545 px, galerie (107, 462)). Les positions de la poupe sont lues sur l'image en résolvant, pour
chaque repère (fenêtres, échelles, tuyaux, coins du rouf et de la galerie, gradins de la voûte), le z qui tombe sur son
pixel à hauteur et bord connus. Rendus comparés côte à côte en vue entière et en gros plans, cinq itérations ; vues
bâbord, 3/4 avant et arrière, dessus et pièces meublées vérifiées à chaque fois.
`docs/comparaison_gear_steamship.png` (référence à gauche, modèle à droite).

1. **Poupe** : ce n'était pas la galerie (son bout est à sa place, z −20) mais tout ce qui est devant elle : la coque
   finissait 1,5 bloc trop loin et le rouf, les fenêtres des quartiers, l'échelle de flanc et les tuyaux tombaient 1,5 à
   2,5 blocs trop en arrière.
   * Coque raccourcie : le tableau passe de z −17,5 à **−16** ; la galerie fait 4 blocs (−20 → −16, comme sur l'image) ;
     la dunette ne la couvre plus que jusqu'à −18,5 : son arrière est à ciel ouvert.
   * **Rouf** avancé de 2 blocs (z −12 → −5) : son avant repose sur le toit des machines et la **cheminée monte à travers
     lui**, comme sur l'image où elle se dresse à l'extrémité avant du rouf. La cabine du capitaine
     (z −11,5 → −7) a pour mur avant le coffrage de la cheminée ; elle a été remeublée. La barre passe juste derrière
     la cheminée (z −7,75), et un garde-corps ferme l'avant du toit.
   * Fenêtres des quartiers (z −12,6 et −10,8), longue bande de cuivre (−8,85), échelle de flanc (−7,85), tuyau bas
     (sortie −11,4, colonne et tuyau dans l'eau −7,2), échelle depuis l'eau (−4,7), jambe arrière du grand U (−3,4) :
     toutes à leurs places sur l'image.
   * Quartiers de l'équipage raccourcis (z −15,5 → −7) et remeublés : deux couchettes hors des fenêtres, casiers contre la
     cloison avant, armoire à bâbord, cuisine dans l'angle tribord arrière. Les caisses, le tonneau et le banc de la
     dunette ont suivi.
   * Tout a été remis à jour : grille, portes, échelles, sièges, places où l'on se relève, sondes, `GearSteamLayout`, tests
     JUnit et en jeu.
2. **Cheminée** : remesurée, elle était déjà à sa place (écart cheminée–dôme 142 px sur l'image, 141 au rendu). Le
   « 0,5 à 0,7 bloc trop en avant » des phases 1 à 3 venait d'un point mal pointé : 527 px, qui est son bord gauche. Ce qui
   la faisait paraître trop en avant, c'est le rouf trop reculé : il est maintenant percé par elle comme sur l'image.
   Chapeau refait en deux étages évasés, et sa bague de laiton est remontée à la hauteur mesurée.
3. **Couleurs** :
   * le laiton (engrenages, cadres, bandes, rivets, fenêtres, plaque) passe d'un jaune or pâle au bronze orangé de
     l'image (#a8622a → #eeae58) ;
   * le cuivre (bandes, tuyaux, garde-corps) est plus chaud ;
   * le tambour du dôme a sa propre région de plaques cuivre brun sombre (#4e2a1c → #5c3322) sous une calotte cuivrée ;
   * l'or des voiles tire vers l'or bronze ;
   * les tôles noires rivetées ne changent pas.
4. **Rangs en gradins** :
   * à l'avant, sous la bande, quatre rangs d'un bloc reculent l'un sous l'autre vers l'étrave. Chaque rang est droit, son
     bout avant 0,52 en retrait de celui du dessus, et les blocs de laiton de l'étrave suivent en escalier ;
   * à l'arrière, la voûte descend en rangs de 0,7 de la galerie à l'eau (mesurés : 0,7 de haut, 0,8 de long), avec un
     liseré de cuivre sur chaque rang, jusque sous la galerie. Ces rangs sont pleins dans la grille ;
   * le liston de cuivre se voit maintenant au-dessus de l'eau (−0,15 → 0,75).
   Ce sont des courbes Python seulement : la coque Java (flottaison, sondes) ne change pas.
5. **Grue** : un haut socle riveté de 2 blocs sur le bord arrière de la dunette (bandes de laiton, chapiteau, lampes),
   un poteau plus gros, une flèche horizontale à deux membrures avec jambe de force et entretoises boulonnées, et un petit
   engrenage. Elle est 0,8 bloc plus en avant (z −18), comme la caisse (z −23).

Restent (classés) :
* La lumière chaude du coucher de soleil et le relief des blocs (rendu IA) : les tôles paraissent plus bleues au rendu.
* Les gradins de l'avant sont plus discrets que sur l'image : la coque reste lisse en plan.
* La troisième fenêtre de chaque bord du rouf éclaire le coffrage de la cheminée et ne se voit pas de l'intérieur.
* Le dôme de l'image est un peu plus haut et plus étroit, à bandeaux de laiton plus épais.

## 13. Visuel, version 1.27.1 (lumière peinte dans les textures)

Constat sur les captures en jeu de la 1.27.0 : Minecraft éclaire les entités à plat (une face n'est que plus ou moins
sombre selon son orientation, environ × 0,5 à × 0,75 sur les flancs), si bien que les grandes surfaces d'une seule teinte
paraissaient plates : tôles d'un gris neutre lu bleuté à côté du cuivre, joints presque invisibles, cuivre et laiton
plats, fenêtres beige pâle. La lumière et l'usure sont donc **peintes dans les textures**, sans coût en jeu.

* **Résolution** : les deux atlas passent à 1024 × 1024, **32 px par bloc** (`gear_steam_texture.K = 2`). Les régions
  restent écrites en unités de l'ancien atlas (`LAYOUT`) et sont doublées (`REGIONS`) ; le générateur double la densité UV
  des faces qui prennent la région à leur taille (`_face_uv_hd`), les faces étirées ou à sous-rectangle ne changent pas.
  L'ancienne peinture (pièces, mobilier, petites pièces) est gardée, agrandie ; les régions extérieures sont repeintes
  par-dessus (`_paint_hd`).
* **Tôles** (`_plates_hd`) : noir chaud brun (plus de gris bleuté), un ton par plaque, certaines plus brunes, marbrure
  douce, chaque plaque un peu plus claire en haut, **biseau éclairé** en haut et à gauche, **biseau ombré** en bas et à
  droite, joint sombre, quatre rivets ronds éclairés en haut à gauche avec leur petite ombre, quelques rayures et
  coulures de rouille. Les régions de tôles font maintenant 8 × 4 plaques (au lieu de 4 × 2) avant de se répéter ; les
  tôles du fond sont plus sombres (assombrissement vers la quille).
* **Bandes** (`_band_hd`) : cuivre, laiton, poutre sombre et fer arrondis (bord haut éclairé, reflet, bord bas ombré),
  joint biseauté à chaque bloc, gros rivets de laiton en relief, un peu de vert-de-gris sur le cuivre.
* **Laiton poli** (`_polished_hd`) plus orangé, reflets larges ; **engrenages** : chaque pièce (jante, dents, rayons)
  montre une barre de laiton biseautée entière (`gear_bevel`), la roue se lit en relief.
* **Fenêtres** : verre orange profond (cœur chaud, bords saturés : le jeu assombrit aussi les faces lumineuses selon leur
  orientation, un orange pâle y devenait beige), croisillon de bronze, cadre de laiton biseauté à rivets ; appuis et
  linteaux plus profonds (relief).
* **Tuyaux** cylindriques (reflet au tiers haut, dessous sombre, bague à chaque bloc) ; **cheminée** en tôles noires à
  colonnes de rivets ; **lanternes** et feux plus saturés ; bois (planches, mâts, garde-corps, caisse) à veinage, joints,
  clous et biseaux.
* **Dôme** : chaque plaque de la calotte montre un fuseau de cuivre entier (`dome_gore` : reflet vertical, rivets de
  laiton le long des coutures, vert-de-gris), les fuseaux s'alignent de rang en rang comme sur l'image. Proportion : le
  tambour s'arrête 0,2 plus bas (y 12,2) et la calotte est plus haute (2,2 au lieu de 1,76) et plus ronde (superellipse,
  épaule plus pleine), sommet inchangé ; bandeau de laiton épais (0,72 de haut, 0,24 d'épaisseur) au pied de la calotte et
  une couronne de laiton sous la vigie. Le tambour est 0,08 plus étroit que la calotte (le bandeau couvre le ressaut).
* **Voiles** (`_black_sail_hd`, 40 px par laize) : noir brun, armure fine, couture de laize au milieu de chaque laize
  (points), deux bandes de ris piquées avec garcettes, ralingue torsadée sur le pourtour, plis doux verticaux et plis en
  diagonale depuis les points d'écoute, dégradé du haut vers le bas ; liseré doré à reflet et ombre, piqûres ; engrenage
  cerné de sombre, biseauté (haut-gauche clair, bas-droite sombre) et dégradé.
* **Vérifié en jeu** (captures CI, variante décor, premier envoi) : les tôles se lisent en blocs biseautés d'un noir
  chaud, les bandes rivetées et les engrenages en relief, le dôme à fuseaux. Mais le jeu n'utilise pas de mipmaps pour
  les entités : à distance normale, un joint d'1 px sur 32 et les petits rivets clairs scintillaient en mouchetis, le
  croisillon fin des fenêtres disparaissait et le liseré sombre de l'engrenage des voiles, peint à l'intérieur de l'or,
  rongeait les rayons. Corrigé : joints de 2 px, biseaux plus larges, rivets des tôles plus doux, plus de rayures ;
  croisillon plus épais et verre plus clair ; engrenage plus épais, liseré sombre posé sur la toile autour de l'or.
* Coût : 6 199 cubes (+16 : la couronne du dôme), aucune entité, rien par tick ; textures 1024 (≈ 0,4 Mo et 0,25 Mo).
* `docs/comparaison_gear_steamship.png` : référence | en jeu avant ; en jeu après (premier envoi) | rendu final à la caméra
  de la référence ; flanc de près en jeu avant | après ; rendus avant | après du milieu et du dôme.

Restent : la lumière dorée du coucher de soleil de l'image (rendu IA) ; les gradins de l'avant restent discrets ; la
cheminée de l'image a des tôles plus brunes ; le relief réel des blocs de l'image (chaque bloc légèrement en saillie)
n'est imité que par les biseaux peints.

### 13.1 Retouches après la revue des captures en jeu

La revue des captures du commit précédent (0511cc4f) relevait : des fenêtres ternes (beige ou brun), un engrenage de
proue fondu dans la coque, un mouchetis à distance (rivets et joints), une coque trop brune qui étouffait le cuivre et le
laiton, un or des voiles pâle et une bande de cheminée réduite à un pointillé.

* **Fenêtres qui brillent** : le moteur de rendu des navires (`ShipRenderer`, commit à part, commun à tous les navires)
  donne aux faces « glow » une normale vers le haut, si bien que l'ombrage des entités reste à 1 sur les flancs (il les
  assombrissait d'environ × 0,5 à × 0,75 malgré la lumière maximale) ; lampes éteintes, rien ne change. Le verre
  (`_glow_window_hd`) passe à un orangé clair (cœur `fff8d8`, bords `ff9c30`), cadre peint de 3 px (le cadre en cubes de
  laiton fait le reste), croisillon d'un seul bronze de 6 px centré sur les texels : deux tiers de la case sont du verre.
* **Coque** : charbon presque neutre (tons autour de `2c2826`, plaques brunes plus rares), biseau éclairé limité à
  environ +20 de luminance ; rivets des tôles plus doux. Sous la bande de cuivre basse (`plate_c`), joints, rivets et
  rouille sont d'un tiers moins contrastés (les rangs bas de la poupe scintillaient).
* **Bandes** : têtes de rivets proches de la couleur de la bande, reflet doux (les points de laiton pâle sur le cuivre se
  lisaient comme de la poussière) ; le laiton des bandes (`brass_band` : cheminée, étrave, cadres, bandeaux du dôme) passe
  à un or vif et saturé (`c8842a` → `fcc868`) : la bande de la cheminée se lit comme un anneau d'or plein. Tôles de la
  cheminée assorties à la coque.
* **Engrenages** (`gear_bevel`) : laiton plus clair et plus saturé (milieu `d08c2c`, reflet `f0b040`), ombre plus douce,
  plus de liseré sombre en haut et à gauche. L'engrenage de proue reçoit derrière lui une **plaque de fer noir** (un disque
  octogonal, 4 cubes par bord) : ses rayons et sa jante se lisent sur du noir, comme sur l'image.
* **Voiles** : or plus saturé (`7a3e10` / `d8902c` / `ffc860`), reflet du liseré et de l'emblème moins pâle ; chaque laize
  est arrondie comme un coussin éclairé à gauche (± 15 %), visible à distance, toile un peu moins brune.
* Coût : 6 207 cubes (+8 : les deux plaques de l'engrenage de proue ; 6 183 en 1.27.0), aucune entité, rien par tick.

## 14. Portes élargies, version 1.28.0

Constat du joueur : « le joueur ne passe pas » les portes. Causes trouvées (`tools/gear_steam_interior.py`,
`ShipGeometry.collectBoxes`) :

1. **Les portes « 1,5 bloc » n'ouvraient qu'un bloc dans la grille.** Leurs boîtes (x ± 0,75 ; 2,25 → 3,75 ; −1,25 → 0,25)
   avaient leurs bords sur des *centres* de cases de 0,5 ; `Grid.sel` ne garde que les cases dont le centre est strictement
   dans la boîte, donc une demi-case était perdue de chaque côté : ouverture réelle 1,0 × 2,5 (machines), 1,0 × 2,0 (quartiers,
   galerie), 1,0 × 2,5 (cabine), derrière des vantaux et un cadre dessinés à 1,5.
2. **Un bloc ne se passe que cap sur un axe.** Chaque case solide devient en jeu une boîte alignée sur le monde de demi-côté
   0,25 (|cos| + |sin|) : à 45° les cases grossissent de 41 %. Simulation (le même calcul que `GearSteamShipTest.doorsPassableAtAnyHeading`, joueur de 0,6) :
   une ouverture de 1,0 se passe à 0° et 10° de cap (tolérance latérale 0,39), plus du tout à partir de 20° ; une ouverture
   de 2,0 se passe à tous les caps (tolérance 1,39 à 0°, 0,67 à 45°).
3. Ni marche au seuil (planchers au même niveau des deux côtés), ni plafond trop bas (2,0 ou 2,5 libres), ni trou entre la
   porte et les cases DRY.

Correction : les quatre portes font **2 blocs de large (deux vantaux de 1), bords sur les frontières de cases** ; 2,5 de haut
dans la salle des machines et la cabine, 2,0 sous le plafond de 2,5 des quartiers (portes des quartiers et de la galerie, un
linteau de 0,5 reste). Boîtes : machines x −1 → 1 ; quartiers x 2 → 4 ; galerie x −1 → 1 ; cabine x −1 → 1 (recentrée : elle
était décalée à bâbord, l'échelle de la passerelle reste à 1,5 → 2,5). Les trous des murs extérieurs (façade de la maison des
machines, mur arrière du rouf) sont pris sur `gi.DOORS` ; `GearSteamLayout.DOORS` porte les mêmes boîtes. Meubles déplacés :
les deux casiers bâbord de la cloison avant des quartiers (x 0,4 et 1,4), l'armoire (z −9,42, dégagée de l'entrée), le coucou
de la cabine (x 1,9), le porte-voix des machines (x −1,35). Une assertion du générateur refuse une boîte de porte hors des
frontières de cases, et `python3 tools/gear_steam_interior.py` imprime l'ouverture réelle de chaque porte.

Tests : `GearSteamShipTest.doorOpeningsFillTheirBoxes` (chaque case de la boîte est une case de la porte, mur à côté, linteau
au-dessus, même plancher des deux côtés) et `doorsPassableAtAnyHeading` (le parallélépipède du joueur, 0,6 × 1,8, balaye
chaque porte ouverte à 11 caps de 0° à 304° sans toucher une boîte, tolérance latérale ≥ 0,3, le mur à côté arrête bien) ;
en jeu, `GearSteamShipGameTest` fait marcher le joueur (sans sauter) du passavant à la salle des machines, de la salle des
machines aux quartiers, des quartiers à la galerie et de la dunette à la cabine, et retour, cap 0° puis navire tourné de 35°
(captures `21_porte_salle_des_machines`, `22_porte_cabine`).

## 15. Visuel, version 1.28.0 (troisième passe)

Point de départ : les captures en jeu de la 1.27.2 (branche `test-results-decor`, vue de la référence, flanc, arrière,
dessus, en route) et le rendu à la caméra de la référence (`tools/gear_steam_compare.py`), comparés à l'image 063 en vue
entière et en gros plans poupe / milieu / proue. Ce qui restait plat ou terne : les tôles d'un seul ton (la coque se lisait
comme une surface unie, sans le relief ni la variation bloc par bloc de l'image, dont les blocs vont du noir au gris-bleu
ardoise) ; le cuivre des bandes et des tuyaux un peu brun à côté du laiton ; les fenêtres jaune pâle, presque blanches de
loin, alors que l'image les montre ambre-orange ; les voiles d'un noir plat (l'image montre une toile en blocs, chaque bloc
d'un ton différent, arêtes éclairées) ; le dôme un peu sombre.

Trois itérations de rendu (caméra de la référence, gros plans milieu / poupe / proue / voiles, vue à 60 blocs à la densité
de pixels du jeu, le passavant et la dunette avec les portes ouvertes ; `/tmp/claude-0/agent_g/r1..r3`), textures seules
(`tools/gear_steam_texture.py`, 32 px par bloc, rien ne change dans le modèle ni dans la grille) :

1. **Tôles** (`_plates_hd`) : biseau éclairé plus large (5 × 4 px) et plus clair (× 1,5), lumière de haut de plaque plus
   forte (1,09 → 0,89), ton par plaque tiré de 0,8 à 1,22 au lieu de 0,86 à 1,14, et dix tons au lieu de sept, du presque noir
   (`231f1e`) au charbon clair (`3a3531`) avec deux tons d'acier froid (`2a2b2f`, `2f3136` ; parois des châteaux `2e3035`,
   `34363c`) : les blocs de l'image, noirs et gris-bleu mêlés, se lisent de loin, là où rivets et joints disparaissent. Les
   tôles de la cheminée suivent (cinq tons, biseau × 1,45), celles du fond un peu (× 1,3). Cuivre et laiton gardent un fond
   neutre pour ressortir (critique de la 1.27.2 : « coque trop brune qui étouffait le cuivre »).
2. **Cuivre** (`copper`, `copper2`) : plus saturé et plus clair (`bc5c28` → `c86028`, reflet `ffb06a` / `ffb874`), reflet
   plus marqué (0,42), rivets de la couleur de la bande ; **tuyaux** un peu plus clairs (× 0,9 au lieu de 0,82, reflet
   `ffc48e`) ; **laiton des bandes** (`brass_band` : cheminée, étrave, cadres, bandeaux du dôme) `d48c2a` → `ffd470`.
3. **Engrenages** (`gear_bevel`) : biseau plus contrasté (lumière 1,0 / 0,8, ombre 0,85 / 0,7), or plus saturé
   (`d48c28` → `ffd878`) : jante, dents et rayons se lisent en relief de la quai.
4. **Fenêtres** (`_glow_window_hd`) : verre ambre (cœur `fff2c4`, bords `ff8a28`) au lieu du jaune pâle ; elles restent les
   faces les plus claires (faces « glow » à pleine lumière depuis le `ShipRenderer` de la 1.27.2) mais chaudes, comme sur
   l'image.
5. **Dôme** (`_gore_hd`) : fuseaux de cuivre plus clairs (`b4582a` → `f8b484`), reflet vertical plus fort.
6. **Voiles** (`_black_sail_hd`) : six tons de toile au lieu de cinq, du noir chaud (`252020`) au gris (`4a4746`), tirage par
   laize 0,9 → 1,12 ; arête éclairée de 2,5 px (× 1,4) et arête ombrée de 3 px (× 0,55) : chaque bloc de toile se lit, comme
   sur l'image.

Pas de détail d'un texel : joints de 2 px, rivets de 4 px adoucis, biseaux larges ; à 60 blocs (rendu à la densité du jeu) la
coque se lit en blocs sombres variés sous les bandes de cuivre et d'or, sans mouchetis. Coût : textures seules (≈ 0,4 Mo et
0,25 Mo), 6 205 cubes (−2 : les cadres de portes élargis), aucune entité, rien par tick.

`docs/comparaison_gear_steamship.png` : référence | en jeu 1.27.2 ; rendu 1.27.2 | 1.28.0 à la caméra de la référence ;
milieu, poupe, voiles, vue à 60 blocs avant | après ; en jeu 1.28.0 et les portes.

Restent : la lumière dorée du coucher de soleil de l'image ; le relief réel des blocs (chaque bloc en saillie), imité par les
biseaux peints ; les gradins de l'avant restent discrets ; le dôme de l'image a des bandeaux plus épais.
