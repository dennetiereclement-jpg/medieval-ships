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
| Côté | tête de mât ≈ 15–45 px | ≈ 35 blocs au-dessus de l'eau |
| Côté (zoom) | bande crème à la flottaison, 2ᵉ bande ≈ 2,1 blocs au-dessus, remontant vers l'étrave | `LOW_BAND`, `HIGH_BAND` |
| Dessus | mâts à 22 %, 44 %, 68 % de la longueur depuis l'étrave, château arrière sur les 16 % arrière | mâts z = 11,5 / 2,5 / −7,5, château z < −14 |
| Dessus | 3 panneaux de cale sur l'axe, un canot sur le gaillard d'arrière, gui d'artimon dépassant la poupe | panneaux z = 8 / −0,8 / −10,3, canot z ≈ −18,8, gui jusqu'à z = −24,6 |
| Avant | 4 lanternes pendues sous la vergue basse de misaine, une lanterne sur l'étrave | reproduites |
| Arrière | 4 fenêtres éclairées au-dessus d'une galerie, balcon supérieur, lanternes d'angle, pavillon à tribord | reproduits (galeries de poupe et de hanche) |

Gréement : trois mâts (le dessus en montre trois jeux de vergues) — misaine et grand mât : basse
voile, hunier, perroquet ; artimon : brigantine à corne et gui + hunier et perroquet ; trois focs sur
le beaupré et le bout-dehors, une voile d'étai entre misaine et grand mât. Échelles de corde
(enfléchures) sur chaque hauban, deux pavillons noirs à tête de mort (pic de la brigantine, mât de
pavillon à tribord arrière) et une flamme au grand mât.

## 2. Dimensions retenues

* Coque 42 × 10 blocs, 52 avec le beaupré ; quille −3,4, lisse 5,6 (coque 9 blocs) ; grand mât
  34,6 (hauteur totale 38).
* Section arrondie (fond en V adouci, légère rentrée des hauts), étrave fine, arrière large à tableau.

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Gaillard d'arrière | 7,0 | barre (roue z = −15,3, pilote debout z = −16,1), canot, balustrades, lanternes |
| Pont principal | 4,5 | du château à l'étrave ; 2 escaliers vers le gaillard (z −14 → −11,5) ; descente bâbord vers la salle commune (x 2–3,5, z 1–4,5) |
| Cabine du capitaine | 4,0 | sous le gaillard, z −20,5 → −14,5, porte double (porte 0) ; lit, bureau + chaise, coffre, tapis |
| Pont inférieur | 1,0 | coursive axiale (z −14 → −1,5) ; postes d'équipage bâbord/tribord (portes 3 et 4) ; salle commune (z −1 → 8, porte 1) ; cuisine (z 8,5 → 14, porte 2, foyer de pierre) |
| Cale | −2,0 | z −17 → 13, sous la flottaison mais sèche (grille) ; escalier depuis l'extrémité arrière de la coursive |

Hauteurs libres : pont inférieur 3 blocs, cale 2,5, cabine 2,5. Les mâts de misaine et grand mât
traversent les pièces jusqu'à la cale (piliers), l'artimon repose sur le pont.

## 4. Sièges (phase 1)

Pilote + 12 places : 8 sur les bancs de la salle commune, la chaise du capitaine, 4 sur deux bancs
du pont principal. Décor complet (mods de décoration) en phase 2.
