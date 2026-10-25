# Le Vieux Corsaire (`old_corsair`) — plan, animations, guide du joueur et rapport de test

Sections 1 à 4 : analyse de la planche de référence et plan (phase 1) ; 5 : aménagement des pièces et
mobilier (phase 2) ; 6 : animations et effets (phase 3) ; 7 : **guide du joueur** ; 8 : **rapport de test**. Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical
(0 = ligne de flottaison), z longitudinal (+z = proue). Sources : `tools/corsair_shape.py`
(forme, niveaux), `tools/corsair_interior.py` (grille), `tools/generate_corsair.py` (modèle),
`tools/corsair_decor.py` (mobilier, sièges), `CorsairLayout.java` (mêmes nombres).

## 1. Mesures relevées sur la planche

| Vue | Mesure (px) | Résultat |
|---|---|---|
| Côté | coque 215→870 px, beaupré jusqu'à 15 px, ≈ 16 px/bloc | coque 42, hors-tout 52 |
| Côté | flottaison ≈ 603 px, lisse ≈ 495–505 px | franc-bord ≈ 5,5–6 blocs |
| Côté | têtes de mât ≈ 40 px (misaine et grand mât à la même hauteur) | ≈ 35 blocs au-dessus de l'eau |
| Côté (zoom) | bande crème à la flottaison, 2ᵉ bande ≈ 2,1 blocs au-dessus, remontant vers l'étrave | `LOW_BAND`, `HIGH_BAND` |
| Côté | pied de misaine à 477 px, pied du grand mât à 677 px (flottaison 255 → 865 px) : 36 % et 69 % de la longueur depuis l'étrave | mâts z = 6,5 / −7,5, château z < −14 |
| Dessus | panneaux de cale sur l'axe, un canot sur le gaillard d'arrière, gui dépassant la poupe | panneaux z = 10,6 / 0,8 / −10,6, canot z ≈ −18,8, gui jusqu'à z = −22,7 |
| Avant | 4 lanternes pendues sous la vergue de pied de la misaine, une lanterne sur l'étrave | reproduites (grosses lanternes, la vergue tenue par des balancines) |
| Arrière | 4 fenêtres éclairées au-dessus d'une galerie, balcon supérieur, lanternes d'angle, pavillon à tribord | reproduits ; le pavillon flotte vers tribord, vu de face depuis l'arrière |

Le dessus de la planche montre trois jeux de vergues, mais les vues de côté et en perspective montrent
un **brick à deux mâts** : c'est ce gréement qui est reproduit (demande du joueur : « fais 2 mâts »).

### Gréement mesuré sur la vue de côté (et vérifié sur la perspective)

Hauteurs : y = 5,6 + (497 − y_px) / 15,5 (lisse à 497 px, têtes de mât à 40 px) ; positions le long
de la coque : ≈ 14,5 px par bloc à partir des pieds de mât.

| Élément | Mesure (px) | Modèle (blocs) |
|---|---|---|
| Misaine | pied 477 px ; hune 300 ; barres de perroquet 160 ; chouque 40 | z = 6,5, mât sur la quille (traverse la salle commune et la cale) ; hune 18,3, barres 27,3, tête 34,8 |
| Misaine — basse voile | vergue 315, bordure 455, largeur 225–235 px | vergue 17,3, bordure 8,4, demi-largeur 7,9 / 8,5 ; vergue de pied et 4 lanternes (vue avant) |
| Misaine — hunier | vergue 190, bordure 290, largeur 170–195 | 25,4 → 18,9, demi-largeur 6,1 / 7,1 |
| Misaine — perroquet | vergue 72, bordure 150, largeur 130–155 | 33,0 → 27,9, demi-largeur 4,6 / 5,6 |
| Grand mât | pied 677 px ; hune 270 ; barres 138 ; pomme 40 | z = −7,5, mât sur le pont principal (la coursive dessous reste libre) ; hune 20,2, barres 28,8, tête 35,0 |
| Grand mât — grand-vergue | 290 px, 560 → 790 px, sans voile | 18,9, demi-envergure 8,2, basse voile ferlée dessus (rabans) |
| Grand mât — hunier | vergue 160, bordure 275, largeur 165–180 | 27,3 → 20,8, demi-largeur 5,7 / 6,5 |
| Grand mât — perroquet | vergue 70, bordure 135, largeur 115–135 | 33,1 → 28,9, demi-largeur 4,1 / 4,9 |
| Brigantine (corne et gui) | mâchoire 260, pic (808, 177), point d'écoute (860, 440), gui 445 → 440 jusqu'au pavillon de poupe | corne 19,7 → pic (26,2 ; z −16,5), point d'écoute z −19,7, gui 9,8 → 10,2 jusqu'à z −22,5 ; la plus grande voile du navire |
| Focs | 2 focs « volants » : têtes (370, 155) et (372, 222), points d'amure au-dessus du bout-dehors | foc et grand foc sur les étais de perroquet et de hunier de misaine, têtes à 27,5 et 22,6 |
| Voile d'étai | étroite, entre les mâts contre le grand mât : 595 → 647 px, 310 → 460 px | sur le grand étai (hune → pont z −1,9), tête 17,9, bordure 8,3 |
| Enfléchures | échelles de corde des haubans jusqu'aux hunes, échelles diagonales des galhaubans | haubans + enfléchures (bas-mâts et mâts de hune), galhaubans de hune en échelles jusqu'au plat-bord |
| Pavillons noirs | au pic de la corne (35 × 36 px) et à la poupe, au-dessus du bout du gui (côté) et à tribord (arrière) | 3,0 × 1,9 chacun : pic de la corne, mât de pavillon à tribord du balcon de poupe (flotte vers l'arrière et tribord, visible derrière la brigantine sur la vue de côté) ; pas de flamme en tête de mât |
| Lanternes | bout-dehors, sous le beaupré, vergue de pied de misaine (vue avant) | reproduites |

Les vergues sont brassées de 36° (bras bâbord vers l'arrière) : la planche montre les voiles de face
à la fois sur la vue de côté et sur la vue avant ; le brassage les montre presque de face sur la vue de
côté et en perspective, et encore larges de l'avant. Beaupré allongé : bout-dehors à z = 32 (53 blocs
hors-tout).

## 2. Dimensions retenues

* Coque 42 × 10 blocs, 53 avec le beaupré ; quille −3,4, lisse 5,6 (coque 9 blocs) ; grand mât
  35,0 (hauteur totale 38,4), misaine 34,8.
* Section arrondie (fond en V adouci, légère rentrée des hauts), étrave fine, arrière large à tableau.

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Gaillard d'arrière | 7,0 | barre (roue z = −15,3, pilote debout z = −16,1), canot, balustrades, lanternes |
| Pont principal | 4,5 | du château à l'étrave ; 2 escaliers vers le gaillard (z −14 → −11,5) ; descente bâbord vers la salle commune (x 2–3,5, z 1–4,5) entre les deux mâts ; cabestan z −4,4 |
| Cabine du capitaine | 4,0 | sous le gaillard, z −20,5 → −14,5, porte double (porte 0) ; lit, bureau + chaise, coffre, tapis |
| Pont inférieur | 1,0 | coursive axiale (z −14 → −1,5) ; postes d'équipage bâbord/tribord (portes 3 et 4) ; salle commune (z −1 → 8, porte 1, traversée par la misaine) ; cuisine (z 8,5 → 14, porte 2, foyer de pierre) |
| Cale | −2,0 | z −17 → 13, sous la flottaison mais sèche (grille) ; escalier depuis l'extrémité arrière de la coursive |

Hauteurs libres : pont inférieur 3 blocs, cale 2,5, cabine 2,5. La misaine traverse la salle commune
et la cale jusqu'à la quille (pilier) ; le grand mât repose sur le pont principal, au-dessus de la
coursive qu'il laisse libre.

## 4. Sièges

Pilote + 22 places : 12 sur les bancs de la salle commune (6 de chaque côté de la table), 2 chaises
au bout de la table, le fauteuil du capitaine devant son bureau, le tabouret de la cuisine, un tabouret
dans chaque poste d'équipage, 4 sur les deux bancs du pont principal. Chaque siège a son point de
relevé libre, sur un plancher (vérifié par `CorsairTest.helmAndSeats`).

## 5. Phase 2 : aménagement des pièces (d'après les vues intérieures de la planche)

Les meubles des mods de décoration de l'utilisateur passent en premier : seuls leurs **identifiants de
blocs** sont écrits dans `interiors/old_corsair_decor.json` (190 blocs), jamais leurs modèles ni leurs
textures ; le jeu dessine le modèle du mod installé, embarqué dans le navire (il bouge et tourne avec lui,
garde son orientation, n'est pas une entité du serveur). Si un mod manque, une boîte de remplacement de la
même taille est dessinée. Les pièces modélisées pour le navire (`tools/corsair_furniture.py`, plus les
meubles de `tools/generate_corsair.py`) couvrent ce qu'aucun mod ne propose. Placement :
`tools/corsair_decor.py` ; les meubles pleins entrent dans la grille (cellules FURNITURE : on ne les traverse
pas). Les portes, les escaliers, l'allée centrale de la cale, la coursive et les zones de passage restent
libres. Les lanternes des mods (marquées `glow`) sont dessinées allumées.

### Mobilier pièce par pièce (relevé dans `old_corsair_decor.json`)

| Pièce | Meubles des mods (identifiants, nombre) | Pièces modélisées pour le navire |
|---|---|---|
| Cabine du capitaine | `farmhouse_decorations:` `desk` (bureau), `dining_chair` (chaise du bureau, siège), `night_stand`, `tall_bookshelf`, `coat_hanger` (le manteau du capitaine), `liquor_cabinet`, `pile_of_books` ×3, `cigar_box`, `red_wine_bottle` ×2, `wine_bottle` ×3, `wine_glass`, `kerosene_lantern` ×5, `chained_kerosene_lantern` ; `furnish:` `spruce_shelf` ×4 (livres et bouteilles au-dessus du lit, contre la cloison de poupe), `book_pile` ×2 | lit bas à couverture rouge (aucun lit des mods n'a de couverture rouge), deux coffres de marin cerclés de fer, tapis rouge, deux cartes marines encadrées, carte et compas sur le bureau, longue-vue sur trépied |
| Salle commune | `farmhouse_decorations:` `dining_table_side` ×4 + `dining_table_middle` ×8 (grande table 2 × 6), `dining_chair` ×2 (sièges, bouts de table), `kitchen_wall_shelf` ×3 (chopes et assiettes), `liquor_cabinet`, `wine_bottle` ×5, `red_wine_bottle` ×4, `wine_glass` ×4, `kerosene_lantern`, `chained_kerosene_lantern` ×4 ; `furnish:` `dark_oak_bench` ×12 (sièges), `plate` ×8, `spruce_shelf` ×2 ; `farmersdelight:roast_chicken_block` ; `landsoficaria:` `tapped_cypress_barrel` (le rhum), `cypress_barrel`, `fir_barrel` | tapis rouge sous la table, chopes en bois cerclées, carte marine encadrée, coffre de marin ; le mât de misaine traverse la pièce |
| Cuisine | `farmersdelight:` `stove` ×2, `cooking_pot`, `skillet`, `cutting_board` ×2, `spruce_cabinet`, `potato_crate`, `cabbage_crate`, `onion_crate`, `rice_bag` ×2, `wooden_basket` ; `farmhouse_decorations:` `kitchen_counter` ×2, `kitchen_drawers`, `kitchen_wall_cabinet`, `kitchen_wall_shelf` ×4, `seasoning_rack`, `chained_kerosene_lantern` ×2 ; `furnish:dark_oak_stool` (siège) | grand foyer de pierre avec son ouverture (bûches, braises, flammes, fond noirci de suie), sa hotte et ses jambons pendus ; table de travail ; barres à casseroles (poêles, marmite, louche) ; tonneaux debout |
| Cale / stockage | `landsoficaria:` `cypress_rack` ×3 + `loaded_cypress_barrel` ×2 / `loaded_fir_barrel` (tonneaux couchés sur berceaux), `fir_barrel` ×2, `storage_vase` ×4, `brown_storage_vase` ×4 ; `furnish:` `spruce_crate` ×7, `dark_oak_crate` ×5 (piles de caisses), `amphora`, `spruce_shelf` ×3 (jarres) ; `farmersdelight:` `potato_crate` ×2, `carrot_crate`, `onion_crate`, `cabbage_crate`, `rice_bag` ×6 (sacs) ; `farmhouse_decorations:` `workbench` + `tool_board` (le coin du charpentier), `chained_kerosene_lantern` ×5 | 10 piliers sur socles de pierre, tonneaux debout (la planche les montre debout ; ceux des mods sont couchés), coffres, glènes de cordage |
| Coursive | `farmhouse_decorations:` `kerosene_lantern` ×4 (sur potences), `chained_kerosene_lantern` | tapis de passage rouges, poteaux sous les barrots, potences de fer |
| Postes d'équipage (bâbord, tribord) | `furnish:` `spruce_square_table`, `dark_oak_stool` (siège) dans chacun ; `farmersdelight:canvas_rug` ×2 ; `farmhouse_decorations:` `acoustic_guitar`, `kerosene_lantern` ×2, `chained_kerosene_lantern` ×2, `wine_bottle`, `red_wine_bottle` ; `farmersdelight:wooden_basket` | couchettes doubles avec échelle, hamacs, coffres de marin, tonneau debout |
| Pont principal et gaillard | `furnish:` `spruce_crate` ×2, `dark_oak_crate` ×2 ; `landsoficaria:` `cypress_rack` + `loaded_cypress_barrel` | tonneaux debout (bossoir, entre les mâts, devant le gaillard), glènes de cordage, longue-vue sur trépied près de l'habitacle, panneaux de cale, cabestan, cloche de bronze, deux bancs, canot, roue de barre et habitacle |

Mods utilisés : Farmhouse Decorations (`farmhouse_decorations`, 88 blocs), Furnish (`furnish`, 53), Farmer's
Delight (`farmersdelight`, 28), Lands of Icaria (`landsoficaria`, 21). Aucun bloc de
`mebahelcreaturesdwarven` n'a été retenu (rien ne correspond aux vues de la planche).

Textures : usure et réparations comme sur la planche — bordages remplacés d'autres essences (plus clairs,
plus sombres, rougeâtres) cloués sur le pont, les planchers, les parois et la cale ; tôles rivetées et planches
rapiécées sur la coque ; voiles brique délavées avec pièces beiges cousues ; toile de jute, lin, toile de hamac,
jambons ; tapis rouge sombre à liseré doré passé.

## 6. Phase 3 : animations et effets

Tout ce qui bouge est un **petit os animé** du modèle (`tools/generate_corsair.py`, `build_animations` et
`doors`) ; le reste (coque, ponts, pièces, meubles, mâture) est dessiné depuis le cache statique du moteur de
rendu. Tout part de l'état synchronisé de l'entité (vitesse, barre, voiles, portes) : chaque joueur voit la
même chose. 11 animations dans `blockbench/old_corsair.bbmodel` :

| Élément | Mouvement | Piloté par | Animation (os) |
|---|---|---|---|
| Voiles établies (basse voile, huniers, perroquets, brigantine, focs, voile d'étai) | se gonflent et se relâchent un peu (±10 %) et se balancent de ±1°, chaque voile avec son décalage | le temps, voiles établies | `sail_wind` (3,6 s, boucle) |
| Voiles carguées | à l'arrêt (après 5 s, `furlSailWhenStopped`), les voiles carrées remontent sur leurs vergues, focs, voile d'étai et brigantine disparaissent ; elles se rétablissent quand le navire repart | l'ouverture des voiles (`sailOpen`) | `sail_furl` |
| Roue de barre et safran | la roue tourne de ±150°, le safran de ±28° | la barre (`helmVisual`) | `steer` (`helm_wheel`, `rudder`) |
| Pavillons noirs à tête de mort (pic de la corne, poupe) | ondulent, la moitié flottante en retard sur le guindant (onde qui court le long du pavillon) | le temps | `flag_wave` (1,2 s) |
| Lanternes suspendues (beaupré, bout-dehors, vergue de pied de misaine, galeries et poupe) | se balancent, chacune avec son décalage | le temps | `lantern_sway` (2,4 s) |
| Cordages lâches (bras des vergues bâbord et tribord, deux étais entre les mâts, garde de la corne, deux haubans du bout-dehors) | se balancent lentement autour de leurs points fixes, chacun avec son décalage ; les cordages tendus (haubans, étais de misaine) restent fixes | le temps | `rope_sway` (4,8 s, `rope_slack_*`) |
| Portes (5) | s'ouvrent et se ferment | l'état des portes (sauvegardé) | `door_0` … `door_4` |
| Tout le navire | roulis (±0,36°) et tangage (±0,18°) légers et lents, gîte jusqu'à 2,5° dans les virages en marche | le temps, la barre et la vitesse | dessin seulement (`ShipModels.Visual.rocking` 0,5 × `waveRocking` 0,8) |

Toutes les boucles commencent et finissent sur la même pose (aucun saut à chaque cycle : vérifié par
`CorsairTest.animations`).

**Effets et sons** (client seulement ; `CorsairEffects` pour les sons et la fumée, à moins de 48 blocs du
joueur, et le sillage commun de `ClientShipEvents`, à moins de 96 blocs) :

* **écume à l'étrave et sillage** (particules vanilla) dès 0,8 bloc/s, plus nombreuses avec la vitesse ;
* la **vieille coque grince** de temps en temps, plus souvent en marche et dans les virages ;
* voiles établies : le **gréement craque** dans la mâture, la **toile claque** ; bruissement de la toile quand
  on établit ou cargue les voiles ;
* la **vague d'étrave** clapote le long de la coque, plus fort et plus souvent avec la vitesse ;
* le **feu du foyer** de la cuisine crépite (à moins de 12 blocs) et, navire presque arrêté, laisse monter
  un filet de fumée et quelques étincelles.

Les sons sont des sons vanilla (trappe de bois, laisse, battement d'aile, eau, feu de camp) choisis au hasard
côté client : deux navires ne craquent jamais en même temps.

## 7. Guide du joueur

### Obtenir et poser le navire

* Objet *Le Vieux Corsaire* (*The Old Corsair*) dans l'inventaire créatif (onglet *Navires médiévaux*), ou
  `/ship give old_corsair [joueurs]` (administrateurs). Aucune apparition naturelle, aucune structure.
* **Clic droit sur l'eau** : le navire est mis à l'eau, poupe au point visé, seulement si l'eau est assez
  profonde et dégagée pour toute la coque (quille à 3,4 blocs sous la flottaison), le beaupré et le gui
  (≈ 55 blocs de long, 10 de large) ; sinon un message l'indique et rien n'est posé. `/ship spawn
  old_corsair` le met à l'eau à votre position, proue dans votre direction.
* Récupérer : accroupi + clic gauche sur le navire (administrateurs) ; `/ship remove` le supprime.

### Monter à bord, marcher, portes, escaliers, sièges

* **Clic droit sur la coque** : on est déposé sur le pont principal (ou enjamber le bastingage depuis un quai).
  On marche librement, **pendant la navigation**, sur le pont principal et le gaillard d'arrière et dans
  toutes les pièces : on suit le navire, on ne tombe pas, on ne traverse ni les murs, ni les planchers, ni la
  coque, ni les meubles pleins. La cale et le pont inférieur, sous la flottaison, restent **secs**.
* **Plan** : pont principal (y 4,5) → deux escaliers vers le gaillard d'arrière (barre, canot) ; cabine du
  capitaine sous le gaillard, à l'arrière du pont ; descente bâbord entre les deux mâts vers la salle commune
  du pont inférieur ; de là, la cuisine à l'avant, la coursive vers l'arrière et les deux postes d'équipage
  de part et d'autre ; au bout de la coursive, l'escalier de la cale.
* **Portes** (clic droit pour ouvrir / fermer, état sauvegardé) : cabine du capitaine (0, deux battants),
  salle commune (1), cuisine (2), poste d'équipage bâbord (3), poste d'équipage tribord (4).
* **Sièges** (clic droit, Maj pour se lever ; on se relève à côté du siège) : 23 places — la barre, 12 sur
  les bancs de la salle commune, 2 chaises au bout de la table, la chaise du bureau du capitaine, le tabouret
  de la cuisine, un tabouret dans chaque poste d'équipage, 4 sur les deux bancs du pont principal.

### Piloter

**Prendre la barre** : clic droit sur la roue du gaillard d'arrière (le pilote se tient debout derrière la
roue). Touches (celles de déplacement de Minecraft, changeables dans *Options → Commandes*) :

| Action | Touche (AZERTY) |
|---|---|
| Prendre de l'erre / avancer | Z |
| Freiner, puis reculer | S |
| Barre à bâbord / tribord | Q / D |
| Allure supérieure / inférieure (lente, normale, rapide) | Espace / Ctrl |
| Quitter la barre | Maj |

Un grand voilier lourd : il met longtemps à prendre son erre (≈ 15 s pour l'allure normale) et à s'arrêter
(longue erre), vire large (7°/s au plus, presque pas à l'arrêt), perd de la vitesse en virage ; il flotte à
sa ligne d'eau, roule et tangue un peu, ne passe ni sur la terre ni à travers les quais, les rochers ou les
autres navires. À l'arrêt, les voiles se carguent après 5 s.

### Pilote automatique (itinéraires maritimes)

Comme les autres navires (détails dans [COMMANDES.md](COMMANDES.md), *Itinéraires*) :

```
/ship route create <nom> [pingpong|loop|once]          # itinéraire maritime
/ship route addstop <nom> [secondes] [nom de l'escale] # escale : placez-vous là où doit être le navire
/ship route addpoint <nom>                             # point de passage
/ship route edit <nom> <n°> speed <blocs/s> | wait <secondes> | yaw <degrés>|here | clear
/ship route assign <nom>                               # près du navire : il part et suit l'itinéraire
/ship route depart | /ship ai enable | /ship ai disable | /ship route show <nom> | /ship info
```

Il quitte le port, suit l'itinéraire en évitant les côtes et les rochers (sondes jusqu'au bout du beaupré, au
gui et à la quille), anticipe les virages (rayon de virage d'un grand voilier), ralentit à l'approche,
accoste à l'escale, attend (`aiDefaultWaitSeconds`, 300 s par défaut, ou la durée de l'escale) et repart.
Itinéraires, état de navigation, position, cap, vitesse et portes sont sauvegardés avec le monde.

### Réglages (`config/medievalships.json`, bloc `ships.old_corsair`, `/ship reload`)

Le bloc est ajouté automatiquement au fichier au premier lancement avec ces valeurs :

| Clé | Défaut | Rôle |
|---|---|---|
| `slowSpeed` / `normalSpeed` / `fastSpeed` | 1.8 / 4.2 / 7.0 | allures (blocs/s) |
| `reverseSpeed` | 0.9 | marche arrière |
| `acceleration`, `braking` | 0.28, 0.5 | blocs/s² |
| `waterDrag` | 0.06 | perte de vitesse en roue libre (forte inertie) |
| `maxTurnRate`, `minTurnFactor` | 7.0, 0.08 | rotation maximale (°/s), part disponible à l'arrêt |
| `helmRate`, `helmReturnRate`, `turnResponse`, `turnSpeedLoss` | 0.8, 0.55, 0.5, 0.12 | barre, inertie de rotation, ralentissement en virage |
| `waveRocking` | 0.8 | roulis et tangage visuels (0 = aucun) |
| `aiWaypointRadius`, `aiStopRadius`, `aiLookahead`, `aiProbeDistance` | 14, 3.5, 26, 70 | pilote automatique : rayons, anticipation, portée de détection |
| `aiDefaultWaitSeconds`, `aiStuckSeconds`, `aiTurnAroundSpeed` | 300, 12, 1.8 | attente aux escales, détection de blocage, vitesse en demi-tour |
| `furlSailWhenStopped` | true | carguer les voiles à l'arrêt |

### Modèles et fichiers

* Modèle Blockbench éditable : `blockbench/old_corsair.bbmodel` (6 310 cubes, une texture, 11 animations),
  copié dans `assets/medievalships/models/entity/old_corsair.bbmodel` ; texture
  `textures/entity/old_corsair.png` ; icône `textures/item/old_corsair.png`.
* Générateurs : `tools/corsair_shape.py` (forme), `tools/corsair_interior.py` (grille des pièces),
  `tools/generate_corsair.py` (modèle, gréement, animations), `tools/corsair_furniture.py` (meubles
  modélisés), `tools/corsair_decor.py` (mobilier des mods, sièges), `tools/corsair_texture.py` (texture).
* Java : `CorsairLayout` (mêmes nombres, géométrie, réglages), `OldCorsairEntity`, `CorsairEffects` (sons et
  fumée), tests `CorsairTest`, `NewVehiclesNavigationTest`, `CorsairGameTest`, `NewVehiclesRoutesGameTest`.

### Captures

* Comparaison planche / jeu (variante avec les mods de décoration) :
  [comparaison_old_corsair.png](comparaison_old_corsair.png) — côté, avant, arrière, dessus, perspective,
  détails, pont principal, salle commune, cabine du capitaine, cale, cuisine, coursive. Les vues extérieures
  du jeu sont recadrées sur le navire (prises de loin, champ de 70°).
* Prises de vue du test en jeu (`CorsairGameTest`, branches `test-results-<variante>-<branche>`) :
  `0_voiles_ferlees`, `1_cote` … `5_perspective`, `15_details_lanternes`, `16_details_voile`,
  `17_details_coque`, `18_details_poupe`, `19_pont_vers_la_poupe`, puis à pied `6_main_deck`,
  `7_quarterdeck`, `8_captains_cabin`, `9_common_room`, `10_kitchen`, `11_coursive`, `12_hold`, et en
  marche `13_a_la_barre`, `14_sous_voiles`.

### Limites connues

* La planche montre trois jeux de vergues sur la vue de dessus mais deux mâts sur les vues de côté et en
  perspective : le navire est un brick à deux mâts (demande du joueur).
* Le roulis et le tangage sont seulement dessinés (moins d'un demi-degré, plus la gîte en virage) : les
  collisions et les joueurs à bord ne les suivent pas.
* Les sons sont des sons vanilla : une approximation des craquements d'un vieux navire.
* La fumée du foyer n'apparaît que navire presque arrêté (en marche, des particules du monde traîneraient
  derrière le navire).
* De loin, l'intérieur et les meubles ne sont plus dessinés, ni les petits détails extérieurs.
* Sans les mods de décoration, les meubles des mods sont remplacés par des boîtes de même taille.

## 8. Rapport de test

**Vérifié automatiquement en jeu** (CI, client Minecraft 1.21.11 réel, en **solo** et sur **serveur
dédié**, dans les trois variantes : vanilla, avec Lithium, avec les mods de décoration ; 48 vérifications
du Vieux Corsaire par variante, toutes PASS sur `main` au commit 768c5d88) :

* mise à l'eau (`/ship spawn`) dans un bassin, flottaison à la surface de l'eau ;
* voiles carguées à l'arrêt puis rétablies ; les 6 animations du modèle chargées par le jeu ;
* debout sur le pont principal, le gaillard d'arrière, dans la cabine, la salle commune, la cuisine, la
  coursive et la cale ; la cale est sèche sous la flottaison ;
* ouverture d'une porte (cuisine) ;
* à la barre : le navire avance sous le contrôle du joueur (≈ 9 blocs en 8 s), la roue et le safran
  suivent la barre, les voiles sont établies en marche ; encore en marche vu de l'extérieur, et les sons du
  navire sont joués ;
* pilote automatique (`NewVehiclesRoutesGameTest`) : départ d'une escale après l'attente, route vers le quai,
  arrêt et amarrage à 2,4 blocs du quai, jamais dans les murs du bassin ;
* sauvegarde puis relecture de l'entité (NBT) : position, cap, vitesse, itinéraire, état du pilote
  automatique et portes conservés ;
* captures de toutes les vues ci-dessus (regardées à l'œil pour la comparaison avec la planche).

**Vérifié par les tests unitaires** (`CorsairTest`, `NewVehiclesNavigationTest`, `NoZFightingTest`, …) :
forme identique au générateur Python, dimensions et enregistrement, niveaux et pièces marchables et reliées
(escaliers), portes qui ferment les pièces, barre et 23 sièges avec leur point de relevé sur un plancher, point
d'embarquement sur le pont, cliquer sur le pont ne fait pas remonter à bord, modèle (os, nombre de cubes,
animations : cordages qui se balancent un peu, boucles sans saut, pavillons, lanternes, voiles, barre,
voiles carguées), feu dans le foyer, itinéraire autour d'un rocher (arrêt, attente, départ, aucune collision),
rayon de virage et distance d'arrêt, sondes du pilote automatique jusqu'au beaupré, au gui et à la quille,
itinéraires conservés en JSON.

**Pas vérifié en jeu (à contrôler à la main)** :

* la pose avec l'objet par clic droit sur l'eau (le test utilise `/ship spawn`) et le refus quand l'eau est
  trop peu profonde ou encombrée ;
* l'embarquement par clic droit sur la coque, la prise de barre par clic droit sur la roue (le test assoit
  le joueur directement), les sièges autres que la barre ;
* la marche d'une pièce à l'autre par les escaliers et les portes pendant la navigation (le test place le
  joueur dans chaque pièce ; les liaisons sont vérifiées sur la grille par les tests unitaires) ;
* le clic sur les portes (le test les ouvre côté serveur) et leur animation à l'écran ;
* plusieurs joueurs à bord en même temps, les collisions avec les côtes, les quais et les autres navires
  en jeu, un long itinéraire réel en mer ;
* un vrai redémarrage de serveur avec le navire en route (seule la relecture NBT est testée) ;
* la fluidité visuelle des animations (vérifiée sur les sommets du modèle par les tests unitaires et sur
  des captures fixes, pas en vidéo) et l'écoute des sons ;
* les performances avec beaucoup de navires sur un serveur chargé.
