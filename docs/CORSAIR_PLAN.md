# Le Vieux Corsaire (`old_corsair`) — plan et mesures

Phase 1 : analyse de la planche de référence, plan des niveaux, modèle extérieur, intérieur marchable,
intégration Java et tests. Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical
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

Les meubles des mods de décoration de l'utilisateur passent en premier (seuls leurs identifiants de
blocs sont utilisés, jamais leurs modèles ni leurs textures ; si un mod manque, un bloc de
remplacement de la même taille est dessiné). Les pièces modélisées pour le navire
(`tools/corsair_furniture.py`, plus les meubles de phase 1 de `tools/generate_corsair.py`) couvrent ce
qu'aucun mod ne propose. Placement : `tools/corsair_decor.py` ; les meubles pleins entrent dans la
grille (cellules FURNITURE). Les portes, les escaliers, l'allée centrale de la cale jusqu'au mât de
misaine, la coursive et les zones de passage testées restent libres.

| Pièce | Meubles des mods (identifiants) | Pièces modélisées |
|---|---|---|
| Cabine du capitaine | `farmhouse_decorations:desk` (bureau), `furnish:dark_oak_chair` (fauteuil à haut dossier, siège), `farmhouse_decorations:night_stand`, `farmhouse_decorations:tall_bookshelf`, `farmhouse_decorations:coat_hanger` (le manteau du capitaine), `farmhouse_decorations:liquor_cabinet`, `furnish:spruce_shelf` + `furnish:book_pile`, `farmhouse_decorations:pile_of_books`, `farmhouse_decorations:kerosene_lantern` ×3, `farmhouse_decorations:chained_kerosene_lantern`, `farmhouse_decorations:red_wine_bottle`, `farmhouse_decorations:wine_bottle` ×2, `farmhouse_decorations:wine_glass`, `farmhouse_decorations:cigar_box` | lit à baldaquin bas et couverture rouge (aucun lit des mods n'a de couverture rouge), deux coffres de marin cerclés de fer, tapis rouge rectangulaire, deux cartes marines encadrées, carte et compas sur le bureau, longue-vue sur trépied |
| Salle commune | `farmhouse_decorations:dining_table_side` / `dining_table_middle` (table de 2 × 6), `furnish:spruce_bench` ×12 (sièges), `farmhouse_decorations:dining_chair` ×2 (sièges), `farmersdelight:roast_chicken_block`, `furnish:plate`, `farmhouse_decorations:wine_bottle` / `red_wine_bottle` / `wine_glass`, `farmhouse_decorations:kerosene_lantern`, `furnish:spruce_shelf` ×2, `farmhouse_decorations:kitchen_wall_shelf` ×3 (chopes et assiettes), `farmhouse_decorations:liquor_cabinet`, `landsoficaria:tapped_cypress_barrel` (le rhum), `landsoficaria:cypress_barrel`, `landsoficaria:fir_barrel`, `farmhouse_decorations:chained_kerosene_lantern` ×4 | tapis rouge sous la table, chopes en bois cerclées, carte marine encadrée, coffre de marin |
| Cuisine | `farmersdelight:stove` ×2, `farmersdelight:cooking_pot`, `farmersdelight:skillet`, `farmersdelight:cutting_board` ×2, `farmersdelight:spruce_cabinet`, `farmhouse_decorations:kitchen_drawers`, `farmhouse_decorations:kitchen_counter` ×2, `farmhouse_decorations:kitchen_wall_cabinet`, `farmhouse_decorations:kitchen_wall_shelf` ×4, `farmhouse_decorations:seasoning_rack`, `farmersdelight:potato_crate`, `farmersdelight:cabbage_crate`, `farmersdelight:onion_crate`, `farmersdelight:rice_bag` ×2, `farmersdelight:wooden_basket`, `furnish:spruce_stool` (siège), `farmhouse_decorations:chained_kerosene_lantern` ×2 | grand foyer de pierre avec son feu, sa hotte et ses jambons pendus, table de travail centrale, barres à casseroles (poêles, marmite, louche), tonneaux debout |
| Cale / stockage | `landsoficaria:cypress_rack` ×3 + `loaded_cypress_barrel` / `loaded_fir_barrel` (tonneaux couchés sur leurs berceaux) et `fir_barrel`, `furnish:spruce_crate` / `furnish:dark_oak_crate` (piles de caisses), `farmersdelight:potato_crate`, `carrot_crate`, `onion_crate`, `cabbage_crate`, `farmersdelight:rice_bag` (sacs), `landsoficaria:storage_vase` / `brown_storage_vase`, `furnish:amphora`, `farmhouse_decorations:workbench` + `farmhouse_decorations:tool_board` (le coin du charpentier), `furnish:spruce_shelf` ×3 (jarres), `farmhouse_decorations:chained_kerosene_lantern` ×5 | 10 piliers sur socles de pierre, tonneaux debout (la planche les montre debout ; ceux des mods sont couchés), coffres, glènes de cordage |
| Coursive et postes d'équipage | `farmhouse_decorations:kerosene_lantern` ×6 (sur potences), `farmhouse_decorations:chained_kerosene_lantern` ×3, `furnish:spruce_square_table` ×2, `furnish:spruce_stool` ×2 (sièges), `farmersdelight:canvas_rug` ×2, `farmhouse_decorations:acoustic_guitar`, `farmersdelight:wooden_basket`, bouteilles | tapis de passage rouges (3), poteaux sous les barrots, potences de fer, couchettes doubles avec échelle, coffres de marin, hamacs, tonneau debout |
| Pont principal et gaillard | `furnish:spruce_crate` ×2, `furnish:dark_oak_crate` ×2, `landsoficaria:cypress_rack` + `loaded_cypress_barrel` | tonneaux debout (bossoir, entre les mâts, devant le gaillard), glènes de cordage, longue-vue sur trépied près de l'habitacle (instruments de navigation) ; déjà en phase 1 : panneaux de cale, cabestan, cloche, bancs, canot |

Textures (phase 2) : usure et réparations comme sur la planche — bordages remplacés d'autres
essences (plus clairs, plus sombres, rougeâtres) et cloués sur le pont, les planchers, les parois et
la cale ; tôles rivetées et planches rapiécées sur la coque (phase 1) ; voiles brique délavées avec
pièces beiges cousues ; nouveaux motifs pour les meubles (toile de jute, lin, toile de hamac,
jambons) ; tapis rouge sombre à liseré doré passé, proche des vues de la cabine et de la coursive.

Captures : `CorsairGameTest` photographie chaque pièce en jeu (pont, gaillard, cabine, salle commune,
cuisine, coursive, cale) ; les rendus hors jeu pièce par pièce, à côté des vues de référence, sont
produits avec les scripts de rendu de l'agent (mods de décoration dessinés comme en jeu).
