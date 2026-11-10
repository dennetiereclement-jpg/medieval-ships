# Le Grand navire aux voiles bleues (`blue_frigate`) — plan

Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical (0 = ligne de flottaison),
z longitudinal (+z = proue). Sources : `tools/frigate_shape.py` (forme, niveaux),
`tools/frigate_interior.py` (grille des pièces), `tools/generate_frigate.py` (modèle, gréement,
animations), `tools/frigate_decor.py` (mobilier, sièges), `tools/frigate_texture.py` (textures),
`FrigateLayout.java` (mêmes nombres).

## 1. Mesures relevées sur l'image de référence (768 × 512 px, vue de trois-quarts avant tribord)

| Élément | Mesure (px) | Lecture |
|---|---|---|
| Coque visible | étrave (tête de proue) x ≈ 190 → tableau x ≈ 660 ; hauteur du bordé flottaison (y ≈ 440) → lisse (y ≈ 305) | vue à ≈ 30° du travers : longueur vraie ≈ 540 px ; franc-bord ≈ 0,24 × la longueur → **36 blocs de coque, lisse à 7 au-dessus de l'eau** |
| Beaupré | de x ≈ 190 (tête de proue) à x ≈ 95, montée ≈ 22° | 12 blocs au-delà de l'étrave, pointe à y 12,6 : **46 blocs hors-tout** |
| Largeur | poupe large et carrée (tableau ≈ 0,8 de la largeur maximale), étrave fine et élancée | **10 blocs** de large, tableau 8 |
| Mâts (colonnes dorées) | misaine x ≈ 362, grand mât x ≈ 500, artimon court x ≈ 590 ; têtes à y ≈ 15 (misaine et grand mât), y ≈ 170 (artimon) | hauteurs au-dessus de l'eau : misaine 28,5, grand mât 30, artimon 21 ; misaine à 33 % de la coque depuis l'étrave (z = 6), grand mât à 61 % (z = −4), artimon sur le gaillard (z = −14) |
| Voiles carrées | 3 par grand mât : basse voile y 240–340, hunier y 145–230, perroquet y 65–135 ; largeur de la basse voile ≈ 165 px ≈ 11 blocs à cette distance (≈ 16 avec le gonflement et la perspective) | basse voile 16 × 9, hunier 13 × 7, perroquet 10 × 5 (demi-largeurs 8 / 6,5 / 5) ; artimon : un petit hunier 9 × 4,5 et une brigantine |
| Fleurs de lys | taches bleu marine de ≈ 45 × 60 px sur le hunier de misaine, le hunier et le perroquet du grand mât, soit ≈ 1/3 de la largeur de la voile | emblème peint dans la texture des voiles (hunier et perroquet des deux grands mâts), ≈ 4,5 × 5,5 blocs |
| Focs | deux grands triangles blanc-bleuté entre le beaupré et la tête de misaine, têtes (340, 100) et (350, 150) | deux focs sous la hune de misaine : le grand foc sur l'étai de hunier (point d'amure au cap du beaupré), la trinquette sur l'étai de misaine (amure à mi-beaupré) |
| Coque | bois brun sombre sous la bande dorée de flottaison ; bleu roi entre la bande basse (y ≈ 395) et la lisse dorée ; rangée de **7 sabords rouges** à cadre doré (x ≈ 195 … 575, y ≈ 345) ; balustrade dorée à poteaux au-dessus de la lisse | bande basse à y 1,0–1,5, huit sabords par bord tous les 3 blocs (z −10,5 … 10,5, couvercles rouges relevés, décoratifs) à y 3,9, bordé bleu en mosaïque de blocs (lapis, bleu clair, bleu ciel), planche dorée à la tombée du bordé (y 5,4–5,9), bastingage bleu puis lisse dorée crénelée (merlons et poteaux à pommeau) jusqu'à y 7 |
| Poupe | château haut : rangée de 3 grandes fenêtres à cadre doré sur le tableau, fenêtres latérales, bandes dorées, lanterne pendue à chaque angle arrière | gaillard d'arrière à 8,5 sur la cabine du capitaine (plancher 5,5) ; tableau haut (couronnement 2,65 blocs au-dessus du gaillard) à deux rangs de fenêtres éclairées (5 + 4) + 3 latérales ; galeries de quart dorées en saillie à marches d'or ; pilastres dorés et préceinte d'or sur le tableau ; safran en coin à ferrures dorées |
| Proue | lisse de proue dorée qui s'élève fortement, beaupré doré, lanterne pendue sur le côté de l'étrave | relevé avant de la lisse 2,2 blocs, lisses de tête dorées (courbes) de la tête d'étrave au bastingage |
| Pavillons | tricolore (bleu-blanc-rouge, à queue d'aronde) en tête de misaine et, plus petit, en tête d'artimon | tricolores en tête de misaine (le plus grand) et de grand mât, pavillon rouge à croix blanche en tête d'artimon |
| Haubans | échelles de corde sombres jusqu'aux hunes des deux grands mâts, galhaubans en échelles | haubans + enfléchures (bas-mâts et mâts de hune), galhaubans |

## 2. Dimensions retenues

* Coque 36 × 10 blocs, 46 avec le beaupré ; quille −3,4, lisse 7,0 (coque 10,4 blocs de haut) ;
  grand mât 30, misaine 28,5, artimon 21 (hauteur totale 33,4).
* Section arrondie (fond en V adouci, rentrée des hauts de 0,36), étrave fine et inclinée, arrière
  large à tableau.
* Beaupré de (0, 7,6, 15,5) à (0, 12,6, 27,5) ; gui de brigantine jusqu'à z = −19,6.

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Gaillard d'arrière | 8,5 | barre (roue z = −11,5, pilote debout z = −12,3), artimon (z = −14), balustrades dorées, lanternes de poupe |
| Pont principal | 5,5 | du château (z = −9,5) à l'étrave ; 2 escaliers vers le gaillard (z −9,5 → −6,5, x 2,5–4,0) ; descente bâbord vers la cale (x 2–3,5, z 0,5–4) entre les deux mâts ; cabestan, panneaux de cale, canons de pont |
| Cabine du capitaine | 5,5 | sous le gaillard, z −17,5 → −10, porte double (porte 0) sur la cloison avant ; bureau, chaise, lit, cartes, lanternes |
| Cale | 2,0 | z −9 → 11,5, hauteur 3 ; tonneaux, caisses, sacs, et les canons derrière les sabords ; la misaine et le grand mât la traversent jusqu'à la quille |

Hauteurs libres : cale 3 blocs, cabine 2,5.

## 4. Sièges

Pilote + sièges des pièces (`frigate_decor.py`) : le fauteuil du capitaine devant son bureau, les
bancs du pont principal, un tabouret dans la cale. Chaque siège a son point de relevé libre, sur un
plancher (vérifié par `FrigateTest.helmAndSeats`).

## 5. Matériaux, parties mobiles, contraintes

* **Matériaux** : bordé bleu roi en mosaïque de blocs (lapis, bleu clair, bleu ciel ; bande haute un peu
  plus claire) entre la bande dorée de flottaison et la préceinte dorée, sabords ouverts à
  couvercle rouge relevé et bouche de canon, fond de coque et pont en bois brun, beaupré doré, mâts en
  bois doré à cercles d'or, vergues dorées, voiles bleu glacier et blanc à cellules de toile (blocs de laine
  de la référence, plus claires au ventre, plus sombres aux chutes) avec grandes fleurs de lys bleu nuit
  (basses voiles, huniers, perroquets), haubans et enfléchures en chanvre brun, château arrière à panneaux
  bleus encadrés d'or : deux rangs de fenêtres éclairées (cinq sur le pont de la cabine, quatre sous le
  couronnement, fleur de lys d'or entre elles), galeries de quart en saillie à marches d'or, couronnement
  sculpté, grand fanal et lanternes d'angle, proue dorée massive à bandes étagées, lion doré en figure de
  proue, lisse de bastingage crénelée d'or.
* **Parties mobiles** (os du modèle) : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran
  (`steer`), pavillons (`flag_wave`), lanternes (`lantern_sway`), cordages lâches (`rope_sway`),
  porte de la cabine (`door_0`).
* **Contraintes** : coque et pièces dessinées sur la grille (ce qui est dessiné est ce qui collisionne) ;
  grille fermée sous le pont principal (aucune sortie par la coque, vérifié par
  `FrigateTest`) ; sondes du pilote automatique jusqu'au bout du beaupré, du gui (qui s'arrête un bloc avant le
  couronnement), du safran, du lion de proue et des vergues ;
  cube count visé : quelques milliers.
* **Physique** : grand voilier lourd : accélération 0,22 bloc/s², freinage 0,4, virage 6°/s au
  plus, longue erre (`waterDrag` 0,05), roulis 0,7 ; pilote automatique : rayon 14, anticipation
  28, sondes 75.

## 6. Guide du joueur

* Objet *Grand navire aux voiles bleues* (*Blue-Sailed Frigate*) dans l'onglet créatif *Navires
  médiévaux*, ou `/ship give blue_frigate [joueurs]` ; **clic droit sur l'eau** pour le mettre à l'eau
  (eau assez profonde et dégagée pour la coque, le beaupré et le gui : ≈ 48 blocs de long, 10 de large,
  quille à 4,0 blocs sous la flottaison depuis 1.28.0 : l'eau est à y 0,6 du modèle, la bande dorée basse à la surface) ;
  `/ship spawn blue_frigate` à votre position.
* **Monter à bord** : clic droit sur la coque (on est déposé sur le pont principal). On marche pendant
  la navigation sur le pont principal, le gaillard d'arrière, dans la cabine (porte double, clic droit)
  et dans la cale (descente bâbord entre les deux mâts). **Sièges** (clic droit) : la barre, le fauteuil
  du capitaine et le tabouret de la cabine, les deux bancs du pont, les deux bancs du gaillard, le
  tabouret de la cale.
* **Piloter** : clic droit sur la roue du gaillard d'arrière ; touches de déplacement de Minecraft
  (avancer, freiner / reculer, barre, allure avec Espace / Ctrl, Maj pour quitter). Le plus lourd des
  voiliers du mod : ≈ 16 s pour prendre l'allure normale, longue erre, 6°/s en virage au plus ; les
  voiles se carguent après 5 s à l'arrêt ; écume à l'étrave, craquements de la coque, gréement et
  toile (sons vanilla).
* **Pilote automatique** : comme les autres navires (`/ship route create|addstop|addpoint|assign|depart`,
  `/ship ai enable|disable`, voir [COMMANDES.md](COMMANDES.md)) ; sondes jusqu'au bout du beaupré, du gui
  et des vergues.
* **Réglages** : bloc `ships.blue_frigate` de `config/medievalships.json` (`slowSpeed` 1.5, `normalSpeed`
  3.6, `fastSpeed` 6.0, `acceleration` 0.22, `braking` 0.4, `waterDrag` 0.05, `maxTurnRate` 6.0,
  `waveRocking` 0.7, `aiWaypointRadius` 14, `aiLookahead` 28, `aiProbeDistance` 75…).

## 7. Fichiers, tests, limites

* Modèle `blockbench/blue_frigate.bbmodel` (≈ 5 500 cubes, 2 textures : coque + voiles, 7 animations),
  textures `textures/entity/blue_frigate.png` et `blue_frigate_sails.png`, icône `textures/item/blue_frigate.png`,
  grille `interiors/blue_frigate.grid`, mobilier `interiors/blue_frigate_decor.json` (80 blocs des mods :
  Farmhouse Decorations, Furnish, Farmer's Delight, Lands of Icaria ; boîtes de remplacement si un mod manque).
* Java : `FrigateLayout` (géométrie, réglages), `BlueFrigateEntity`, `FrigateEffects` (sons), tests
  `FrigateTest` (forme, pièces, escaliers, porte, sièges, coque fermée, modèle, animations) et
  `FrigateGameTest` (en jeu : mise à l'eau, voiles, vues de la référence, pont, gaillard, cabine, cale,
  marche sur le pont, porte, barre, sons).
* Comparaison planche / rendu : [comparaison_blue_frigate.png](comparaison_blue_frigate.png).
* Limites : les fenêtres de la cabine ne se voient que de l'extérieur (parois de la grille pleines) ;
  les canons sont décoratifs ; le roulis est seulement dessiné ; sans les mods de décoration, les meubles
  des mods sont remplacés par des boîtes.
