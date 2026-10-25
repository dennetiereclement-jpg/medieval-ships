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

## 4. Sièges (phase 1)

Pilote + 12 places : 8 sur les bancs de la salle commune, la chaise du capitaine, 4 sur deux bancs
du pont principal (au milieu, entre les deux mâts). Décor complet (mods de décoration) en phase 2.
