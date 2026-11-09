# Le Navire royal au lion (`royal_lion_ship`) — plan

Navire de la cité de **Lion Port** (lot 2, version 1.27.0 ; structure revue en phase 4, § 5 quater). Navire marchand royal : richesse, puissance commerciale,
prestige. Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical (0 = ligne de flottaison), z
longitudinal (+z = proue). Sources : `tools/royal_lion_shape.py` (forme, niveaux), `tools/royal_lion_interior.py`
(grille des pièces), `tools/generate_royal_lion.py` (modèle, gréement, animations), `tools/royal_lion_decor.py`
(mobilier, sièges), `tools/royal_lion_texture.py` (textures, lion héraldique), `RoyalLionLayout.java` (mêmes nombres).

**Règle permanente du mod** : le navire utilise le système de navires du mod lui-même (entité, grille intérieure,
collisions, pilotage, pilote automatique) — **ni Valkyrien Skies / Eureka, ni GeckoLib** ; pas d'apparition naturelle.

## 1. Les quatre références (le même navire vu quatre fois)

| Image | Vue | Ce qu'on y mesure |
|---|---|---|
| `royal_lion_ship_1_img071.png` (principale) | trois-quarts avant **tribord**, voxel, port | silhouette, ordre des bandes de la coque, voiles carrées bleu roi à bordure dorée, lion d'or sur la grand-voile, huniers, flammes, auvent rayé bleu/blanc, château arrière à deux rangs de fenêtres en arc, éperon doré en gradins |
| `royal_lion_ship_2_img044.png` | trois-quarts **bâbord** proche du travers, fond sombre | proportions (le moins déformé), position et hauteur des mâts, hunes à garde-corps doré et lanternes, enfléchures, foc, toit bleu du château, bannières au lion, cargaison sur le pont |
| `royal_lion_ship_3_img123.png` | bâbord, caméra basse près de la proue, port | **figure de proue : lion doré** bondissant (crinière, gueule ouverte, pattes avant tendues), toit bleu à lucarne et flèche, bannières |
| `royal_lion_ship_4_img126.png` | rendu orné, bâbord avant | tête de lion de proue, château arrière riche : fenêtres en arc éclairées, toit bleu en mansarde à fleurons dorés, auvents bleus festonnés, lanterne d'angle |

Mesures (044, la vue la moins déformée ; 1 bloc ≈ 34 px au maître-couple) :

| Élément | Mesure (px) | Lecture |
|---|---|---|
| Coque | étrave x ≈ 230 → poupe x ≈ 1450, vue à ≈ 20° du travers | ≈ 38 blocs ; **40 blocs retenus** (52 avec le beaupré) |
| Franc-bord | flottaison ≈ y 900 → lisse du milieu ≈ y 690 ; coque profonde (lisse → quille ≈ 12 blocs sur 044) | ≈ 6 blocs : **lisse à 6,7** au-dessus de l'eau (phase 4 : +0,5), tonture forte vers l'avant (+3,6) et l'arrière (+1,2) |
| Château arrière | sommet du toit ≈ y 480 ; château ≈ 12,5 blocs de long, étage ≈ 8 blocs (044) | phase 4 : **château de 12 blocs, étage de 8, toit de 12,0 à 13,2 (+ lanterne de faîte à 16,2)** |
| Grand mât | pomme ≈ y 30 (044) ; plus haut sur 071 (huniers) | 25,6 (044) à ≈ 34 (071) : **30,5** (misaine 29,5, artimon 26) ; flèches de 2,7 au-dessus des huniers (071) |
| Grand-voile | vergue ≈ y 215, bordure ≈ y 560, largeur ≈ 410 px | phase 4 : **8,5 → 20,2 de haut, 21,8 → 24 de large** (misaine 9,2 → 19,8, 20,2 → 22,2) |
| Hune du grand mât | ≈ y 130 | phase 4 : **21,0** (misaine 20,6, artimon 21,0) ; nids de pie au ton des mâts de hune (27,5 et 26,7) |
| Bandes de coque (071) | bois sombre ≈ 40 % du franc-bord, puis or / bleu / or / bleu / or | brun jusqu'à 2,25 (sabords éclairés à 1,45), préceinte d'or 2,25–2,6, bande bleue, préceinte d'or 3,8–4,15, bande bleue des écus, lisse d'or à 5,5 (relevées avec la tonture) |
| Écus (071) et bannières (044, 123, 126) | 2 écus visibles par bord sur la moitié vue ; longues bannières pendues entre eux | **4 écus par bord** sur le pont (z −5,5, 0,5, 6,5, 12,5), **bannières au lion** entre eux (z −2,5, 3,5, 9,5 ; pas à tribord devant la passerelle), lanternes à côté |
| Mâts (044, 071 : rétroprojection sur le plan axial avec les caméras recalées) | misaine à ≈ 0,83 de la longueur depuis la poupe, grand mât ≈ 0,5, artimon ≈ 0,2 à 0,3 | **misaine 12,5, grand mât −0,5 (13 blocs), artimon −11,5** (phase 4) |

Cohérence avec les autres navires (`core/Ships.java`) : frégate bleue 36 × 10 (46 hors-tout, 33,4 de haut),
galion 35 × 9, vaisseau de guerre 55 × 13. Le navire royal (40 × 12, 51 hors-tout, ≈ 34 de la quille à la pomme du
grand mât) est plus grand et plus lourd que la frégate, plus petit que le vaisseau de guerre.

## 2. Dimensions retenues

* Coque 40 × 12 blocs, 51 avec le beaupré ; quille −3,6 (relevée de 2,6 aux extrémités, puissance 2,6 : flottaison
  plus courte), lisse 6,7 au milieu, **tonture forte** : relevée à 10,3 à l'étrave et 7,9 à la poupe (puissance 2,
  la silhouette trapue en croissant de 044 et 126) ; avant plein et arrondi (puissance 2,6), arrière large sous le
  château (tableau 9,2 de large) ; rentrée des hauts 0,4 ; étrave très inclinée (0,42 par bloc au-dessus de l'eau).
* Mâts : misaine z = 12,5 (pomme 29,5), grand mât z = −0,5 (30,5), artimon z = −11,5 sur le gaillard, contre la
  façade de la salle d'apparat (26) ; flèches courtes au-dessus des huniers (2,7) ; beaupré de (0, 9, 17,5) à
  (0, 14,8, 31).
* Voiles carrées orientées de 6° (bras bâbord en arrière : leur face tournée vers bâbord avant, comme sur trois
  références sur quatre ; meilleur compromis entre les quatre cadrages, voir § 5 ter).

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Toit du château | 12,0 → 13,2 | toit bleu en mansarde (ardoises bleues, arêtiers et égouts dorés), **trois lucarnes éclairées par pente**, crête et balustrade dorées, fleurons dorés aux angles, lanternes sur poteaux aux coins du faîte, lanterne de faîte à coupole bleue et flèche d'or, étendard royal au lion (décoratif, non praticable) |
| Salle d'apparat (étage du château) | 8,5 → 12,0 | **royal state room** sur l'arrière du gaillard, **8 blocs de long** (z −20 → −12), deux portes doubles sur sa façade de part et d'autre de l'artimon ; grandes fenêtres en arc (4 à l'arrière, **5 par côté**, 2 en façade), balcon doré le long de son pied |
| Gaillard d'arrière | 8,5 | de la façade de la salle d'apparat (z −12) au front du château (z −8) : artimon, barre (roue z = −9,4, pilote debout z = −10,2) sous l'**auvent rayé bleu et blanc** festonné, deux bancs, balustrades dorées |
| Gaillard d'avant | 7,0 | de z = 13 à l'étrave, balustrade dorée, cloche ; 2 escaliers depuis le pont (4 marches) ; la misaine se dresse juste à l'arrière de sa balustrade |
| Pont principal | 5,0 | du château (z −8) au gaillard d'avant ; 2 escaliers vers le gaillard d'arrière (7 marches, z −4,5 → −8) ; descente tribord vers les quartiers (x −2,2…−0,7, z −3,5 → −7), descente bâbord vers la cale (x 2…3,5, z 7 → 3,5) ; cabestan, caillebotis, râteliers, cargaison |
| Cabine du capitaine | 5,0 | sous le gaillard, **z −19,5 → −8,5 (11 blocs)**, porte double sur la cloison avant ; fenêtres en arc (4 au tableau derrière la galerie dorée, **4 par côté**, 2 sur la cloison) |
| Quartiers de l'équipage | 1,5 | pont inférieur arrière, z −15 → −3 |
| Cale | 1,5 | pont inférieur avant, z −2,5 → 14,5, cloison avec porte double entre les deux ; la misaine et le grand mât la traversent jusqu'à la quille |

Hauteurs libres : pont inférieur 3 blocs, cabine 3, salle d'apparat 3,5. Toutes les pièces sont dans la coque (grille
fermée sous le pont : aucune sortie par la coque, vérifié par `RoyalLionShipTest`).

## 4. Sièges (22 places assises en plus de la barre)

La barre (pilote debout) ; dans la cabine du capitaine, le fauteuil à haut dossier devant le bureau, deux places sur
la banquette sous les fenêtres de poupe et les deux fauteuils de velours du coin lecture ; dans la salle d'apparat,
six chaises dorées en velours rouge le long de la table et deux trônes à ses bouts ; dans les quartiers de l'équipage, quatre places sur les bancs du carré ; dans la cale, le
tabouret du commis aux écritures ; sur le pont, deux bancs au pied du grand mât et deux bancs sous l'auvent du gaillard
d'arrière. Chaque siège a son point de relevé libre sur un plancher (`RoyalLionShipTest.helmAndSeats`), vérifié en jeu
pour trois d'entre eux (`RoyalLionShipGameTest`).

## 4 bis. Décoration des pièces (phase 2)

Source : `tools/royal_lion_decor.py` (placement, sièges, tableaux) et `tools/royal_lion_furniture.py` (meubles
modélisés). **Les blocs des mods de décoration d'abord** (Farmhouse Decorations, Furnish, Farmer's Delight, Lands of
Icaria : 136 blocs dessinés par le navire, jamais posés dans le monde ; boîte de remplacement si un mod manque) ;
modélisé seulement ce qui manque aux mods ou doit être royal. Les meubles pleins entrent dans la grille (cases
FURNITURE) : on en fait le tour, on ne passe pas au travers.

| Pièce | Blocs des mods | Meubles modélisés |
|---|---|---|
| Cabine du capitaine | lit double à oreillers vers la poupe, table de nuit et sa lampe, commode (boîte à cigares, cadre), grande bibliothèque, bureau à dessus vert (livres, lampe, vin et verre), fauteuil à haut dossier, armoire contre la cloison, lanterne à chaîne, lampes sur potences | banquette de velours bleu sous les quatre fenêtres de poupe (coussins, traversins), **intérieur des fenêtres en arc** (verre et cadres dorés : poupe, flancs, cloison), tapis bleu roi à bordure d'or et lion d'or en médaillon, lustre d'or à six bougies, tapisserie au lion au-dessus du lit, **coffre ouvert plein de pièces d'or** (gobelet renversé), carte marine encadrée, carte et compas sur le bureau, piles de pièces, longue-vue sur trépied, globe terrestre, tableau « sea » dans un cadre doré |
| Salle d'apparat | longue table de salle à manger (deux bouts à pieds tournés, une rallonge), trois chaises dorées en velours rouge, deux trônes à haut dossier, assiettes de porcelaine, verres, bouteilles, volaille rôtie, cabinet à liqueurs, deux commodes, cadre, lampes sur potences | intérieur des dix fenêtres en arc, tapis au lion sous la table, candélabres d'or, tapisserie royale entre les fenêtres du milieu, portraits « bust » et « wanderer » dans des cadres dorés de part et d'autre de la porte, lustre d'or |
| Quartiers de l'équipage | table du carré en long, six bancs, coin cuisine (fourneau et marmite, plan de travail et planche à découper), deux tonneaux à robinet, tonneau sur chantier, sac, portemanteau, lanternes à chaîne | deux couchettes doubles contre la coque, quatre coffres de marin, deux hamacs, vaisselle d'étain et chopes, batterie de cuisine pendue au plafond, râtelier de hallebardes de la garde (pompons dorés) sur la cloison |
| Cale | caisses empilées sur deux rangs, caisses de provisions (pommes de terre, carottes, choux), pyramides de tonneaux sur chantiers, sacs de riz, bottes de paille et d'épeautre, amphores (terre cuite, bleue, jaune), jarres, lanternes à chaîne, tabouret | pupitre du commis aux écritures (registre ouvert, encrier et plume, balance, piles de pièces), **ballots blancs** de toile cordés, râtelier de **rouleaux d'étoffes** bleu roi, rouge et or (marchandises du prince marchand), sacs d'épices, second coffre de pièces d'or |
| Pont et gaillards | caisses sur deux rangs, tonneaux couchés, sacs, deux bancs au grand mât, deux bancs sous l'auvent | **caisses bâchées de toile blanche** et cordées et ballots blancs (la cargaison de 044 et de 071), tonneaux debout, glènes de cordage au pied des mâts |

Phase 4 (château agrandi) : la cabine (11 blocs) reçoit en plus un coin lecture (deux fauteuils de velours, table de
nuit et livres), le cabinet à liqueurs, un second tapis au lion et un second lustre à l'avant ; la salle d'apparat
(7 blocs utiles) a sa longue table dans l'axe (six chaises de velours, deux trônes aux bouts, deux candélabres,
porcelaine, volaille, vins), le cabinet à liqueurs et deux commodes entre les fenêtres, la tapisserie royale entre les
fenêtres de poupe, un portrait « bust » au-dessus du milieu de la façade (l'artimon est dehors, entre les deux portes),
deux lustres ; un tableau « kebab » sur la cloison des quartiers de l'équipage ; la cargaison du pont recule devant les
escaliers du gaillard d'arrière (z −4,5) et la passerelle (tribord, z 1,5 à 5,4).

Laissé libre (vérifié par `RoyalLionShipTest` et par `apply_to_grid` de l'outil) : les portes et leurs abords, les
escaliers et descentes avec leur pied, l'axe de la cabine, des quartiers et de la cale, une bande de 1,9 bloc de part et
d'autre de l'axe du pont principal (points d'embarquement), l'escalier et le levier de la passerelle (tribord, z 1,2 à
5,3), le passage vers les escaliers du gaillard d'arrière, les points de relevé des sièges. Aucun meuble n'entre dans
la coque, les cloisons ou les ponts (l'outil refuse plus de 0,3 bloc dans une case pleine ; le test vérifie qu'aucun
bloc n'est dans une paroi ni au-delà des flancs). Textures ajoutées à l'atlas de la coque (`tools/royal_lion_texture.py`,
cases libres) : tapis au lion, toile blanche des ballots, velours bleu, cire, pièces d'or, globe, étoffes rouge et or,
registre, tapisserie au lion. Planche des pièces : `docs/interieur_royal_lion_ship.png`.

## 5. Extérieur : matériaux, ornements, parties mobiles

* **Coque** : haute, à forte tonture (relevée de 3,6 à l'étrave, 1,2 à la poupe) ; bois brun sombre (mosaïque de blocs)
  avec une rangée de petits sabords éclairés à cadre doré ; préceintes d'or ; deux bandes bleu roi en mosaïque ;
  **grands écus bleu roi (2,5 × 3 blocs) en forme d'écu à pointe, bordure d'or et lion rampant d'or**, détachés du
  bordé devant les préceintes, sur planche sombre à clous dorés ; **longues bannières bleues au lion d'or** (1,3 × 3,9)
  pendues sous la lisse à des tringles dorées entre les écus, une lanterne sur potence à côté de chacune ; lisse dorée,
  bastingage bleu et **balustrade dorée** (balustres, poteaux à pommeau, lanternes sur certains poteaux).
* **Proue** : étrave dorée, lisses d'éperon dorées en gradins jusqu'au beaupré, bossoirs à tête de lion, ancres,
  **figure de proue : lion doré** (grosse tête à crinière, gueule rugissante, langue rouge, crocs, pattes avant tendues
  griffes dehors, console sculptée) — **en phase 4 le lion bondissant entier de 123** : arrière-train et pattes
  arrière repliées contre l'étrave, corps tendu vers l'avant et le haut, poitrail, pattes avant lancées vers l'avant
  et le bas, tête rugissante à crinière, queue enroulée le long de l'étrave ; lanterne pendue sous le beaupré, beaupré
  brun cerclé d'or et bout-dehors.
* **Château arrière** (phase 4 : 12 blocs de long, étage de 8 blocs) : panneaux bleus encadrés d'or, pilastres dorés,
  corniche en volutes dorées ; **deux rangs de fenêtres en arc éclairées** (cabine : 4 par bord et 4 au tableau ;
  salle d'apparat : 5 grandes par bord sous moulures dorées et 4 au tableau), un troisième rang de **lucarnes
  éclairées** dans le toit ; **deux galeries de poupe** dorées (celle de la cabine sur consoles, le balcon de la salle
  d'apparat), balcon doré le long du pied de l'étage, cartouche au lion sur la voûte et écusson au lion entre les deux
  rangs, trois bannières au lion sur chaque flanc de la cabine, **toit bleu en mansarde** à balustrade dorée, fleurons
  dorés aux angles, lanternes sur poteaux, lanternes d'angle sur potences, lanterne de faîte.
* **Mâture** : mâts bruns cerclés d'or, **hunes rondes à garde-corps doré et quatre lanternes**, **nids de pie** dorés à deux lanternes au ton
  des mâts de hune, chouques dorés, **vergues épaisses** à bagues et bouts dorés ;
  **voiles bleu roi en blocs de toile, larges bordures d'or et filet d'or le long des chutes, grand lion rampant d'or
  sur la grand-voile et la misaine** (phase 4 : lion héraldique redessiné — tête de profil gueule ouverte, oreille,
  crinière, deux pattes avant levées griffes écartées, patte arrière levée, queue en S à touffe —, 0,8 de la hauteur
  de la voile, dessiné 1,45 fois plus large que nature pour rester lisible de biais, cerné de marine, relief doré) ;
  grand-voile 11,7 × 24, misaine 10,6 × 22, huniers 6 à 6,4 de haut ; voile carrée d'artimon ; deux focs bleus bordés d'or ;
  **flammes bleues bordées d'or à queue d'aronde** (petit lion d'or au guindant) aux trois pommes ; étendard royal au
  lion au mât de pavillon arrière ; **enfléchures (échelles de corde) claires** jusqu'aux hunes, galhaubans, étais,
  bras, écoutes.
* **Parties mobiles** (os du modèle) : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran (`steer`),
  flammes et étendard (`flag_wave`), lanternes (`lantern_sway`), cordages lâches (`rope_sway`), portes
  (`door_0` cabine, `door_1` et `door_3` salle d'apparat de part et d'autre de l'artimon, `door_2` cloison du pont
  inférieur).
* **Ce qui a été reconstitué** (non visible sur les références) : le flanc tribord du château et le flanc bâbord de la
  proue sont symétriques des côtés vus ; le tableau arrière (vu seulement de biais sur 071/126) reçoit les mêmes
  fenêtres en arc et une galerie ; l'intérieur entier (aucune image) ; la voile d'artimon est carrée comme sur 071 (126
  montre une voile latine). 071 montre des huniers, 044 n'en montre pas : huniers gardés (071 est l'image principale).

## 5 bis. Itérations de comparaison (rendus aux angles des références, mer à la flottaison)

| Itération | Écarts relevés | Corrections |
|---|---|---|
| 1 | coque presque toute bleue (la référence a ≈ 40 % de bois sombre au-dessus de l'eau) ; mâts trop hauts (pomme 33) et voiles trop petites en proportion ; voiles vues par la tranche sur 071 (vergues orientées de 24°) ; lion de proue petit, informe ; lion des voiles fin et peu lisible ; pas de cargaison sur le pont | bandes redistribuées (bois sombre jusqu'à 2,0 avec les sabords, préceintes d'or à 2,0 et 3,3, bandes bleues au-dessus) ; mâts à 30,5 / 29 / 22,5 ; lion des voiles agrandi (72 % et 64 % de la hauteur) ; écus remontés ; flammes plus longues ; caisses, tonneaux et sacs sur le pont et le gaillard d'avant |
| 2 | voiles encore étroites ; enfléchures trop fines et sombres ; quille visible sous la coque dans les rendus (pas d'eau) | vergues moins orientées ; enfléchures en chanvre clair plus épaisses ; plan d'eau ajouté aux rendus de comparaison |
| 3 | lion de proue : silhouette de « singe » ; grand-voile et misaine un peu étroites ; caméra de 071 trop lointaine (perspective plus forte sur la référence) | figure de proue refaite (grosse tête à crinière, gueule rugissante, pattes avant tendues, console sculptée) ; voiles élargies ; caméra rapprochée, focale plus large |
| 4 | les références vues de bâbord (044, 123, 126) montrent la face des voiles, 071 (tribord) aussi : impossible des deux côtés à la fois ; lion de proue encore petit devant 123 ; lions des emblèmes sans détails ; auvent rayé caché par la voile d'artimon ; pavois du milieu trop bleu | vergues orientées de 6° (vers bâbord : trois références sur quatre) ; figure de proue agrandie (×1,35, sondes déplacées) ; traits ciselés dans le lion (crinière, œil, gueule, pattes) ; auvent élargi à tout le gaillard et abaissé ; pavois du milieu en bois sombre |

| 5 | les voiles restent moins larges que sur les quatre images (qui remplissent presque l'espace entre les mâts) | basses voiles, huniers et voile d'artimon élargis (≈ +1 bloc), sondes des vergues suivies |

Écarts restants à la fin de la phase 1 (repris et classés en phase 3, § 5 ter) : voiles un peu moins grandes que sur les images (qui les exagèrent) ; la coque
reste plus longue et plus basse que sur 071 (perspective exagérée de l'image) ; les bannières pendantes de 044 sont
remplacées par les écus demandés ; la tête du lion de proue reste plus simple que la sculpture de 126. La cargaison
des références (caisses bâchées de blanc, ballots) est faite en phase 2 (§ 4 bis).

## 5 ter. Phase 3 : relecture critique (« yeux neufs ») et retouches

**Méthode.** Rendus du modèle aux angles de chacune des quatre images, la mer à la flottaison : direction de vue lue
sur l'image (tribord avant à ≈ 28° du travers pour 071, bâbord avant à ≈ 20° pour 044, à ≈ 35° pour 126, caméra basse à
≈ 38° pour 123), distance et décalage calculés pour que l'emprise du navire (beaupré, poupe, pommes, flottaison)
tombe au même endroit que sur l'image. Les rendus des phases 1 et 2 étaient faits de trop loin et de trop biais (071
vu à 36° du travers, le navire au tiers du cadre), ce qui masquait les écarts. Un recalage de caméra sur des points
repérés (pommes, vergues, étrave, safran, ligne d'horizon de 071) montre aussi que les quatre images ne sont pas
cohérentes entre elles (aucune caméra unique ne les explique : les voiles y sont toujours tournées vers le
spectateur, la coque de 044 et 126 est plus trapue que celle de 071). Couleurs mesurées sur les images (médiane des
pixels bleus de la coque et des voiles).

**Écarts relevés, du plus visible au moins visible, et ce qui a été fait :**

| Rang | Écart (vu par un joueur) | Itération | Correction |
|---|---|---|---|
| 1 | voiles étroites, vues de biais ; le lion des voiles maigre, « en hippocampe », illisible dès qu'on ne voit pas la voile de face | 1, 2 | voiles élargies de ≈ 14 % (grand-voile 20 → 21,8 de large, misaine 18,4 → 20,2, huniers et artimon de même) et plus creuses (creux 2,9 / 2,6) ; lion des voiles redessiné trapu (corps, pattes, crinière, queue épaissis) et ramené à ≈ 0,65 de la hauteur de la voile comme sur les images (lion des écus un peu épaissi aussi) |
| 2 | coque et voiles d'un bleu trop vif et trop clair : les images ont un bleu roi profond, presque marine (mesuré ≈ 26, 42, 91 sur la coque éclairée, ≈ 29, 43, 95 sur les voiles ; le modèle donnait ≈ 27, 51, 126) | 1 | bleus de la coque, des panneaux du château, des écus, bannières, toit, auvent assombris et désaturés vers ce marine ; bleu des voiles un peu moins (`_navy` dans `royal_lion_texture.py`) |
| 3 | écus trop petits (1,8 × 2,1) : sur 071 ce sont de grands écus qui couvrent les deux bandes, sur 044, 123 et 126 de grandes bannières | 1 | écus de 2,5 × 3 blocs, détachés du bordé devant les préceintes dorées (qui ne les barrent plus) |
| 4 | artimon trop court (0,74 du grand mât, ≈ 0,85 à 0,9 sur 071, 044, 126) et sa voile basse qui cache le château arrière et l'auvent rayé | 1 | artimon relevé : pomme 25,8, hune 20,2, vergue 19,0, bordure de la voile à 12,8 (la salle d'apparat et ses fenêtres se voient dessous) |
| 5 | figure de proue petite (≈ 2,5 blocs) : sur 123 et 126 le lion est énorme, à hauteur de la lisse, les pattes avant presque à l'eau | 2 | lion de proue agrandi × 1,37 (tête à 7,3, pattes à 3,4, ≈ 4 blocs de haut), pattes moins écartées ; sondes de la figure de proue déplacées dans `RoyalLionLayout` |
| 6 | enfléchures presque invisibles (fines et sombres) ; sur 071 et 044 ce sont de grosses échelles de corde claires | 2 | haubans et enfléchures plus épais (0,15) et en chanvre clair |
| 7 | vergues en bâtons fins (0,32) ; sur les images ce sont de grosses poutres sombres à bagues et bouts dorés | 3 | vergues de 0,52 (basses vergues) et 0,42 (huniers), bagues, suspente et bouts dorés à l'échelle |
| 8 | auvent rayé bleu et blanc vu par la tranche depuis l'avant (071 montre ses rayures) | 3 | auvent plus incliné vers l'avant (10,9 → 9,7) |
| 9 | têtes de mâts : 044 et 126 ont une hune ronde à garde-corps juste sous la flamme, 071 une caisse au ton du mât | 4 | nids de pie ronds à garde-corps doré et deux lanternes au ton des mâts de hune (misaine, grand mât) |

**Écarts restants (classés), et pourquoi :**

1. **Voiles vues de biais** : les quatre images montrent les voiles de face quel que soit le côté (071 tribord, 044,
   123, 126 bâbord) ; une voile réelle ne peut faire face aux deux bords. Les vergues restent orientées de 6° (bras
   bâbord en arrière : meilleur compromis mesuré sur les quatre cadrages) ; les voiles sont élargies et creusées
   pour compenser, mais elles paraissent encore moins larges que sur les images, surtout sur 071.
2. **Lion des voiles tourné vers la poupe sur le flanc tribord (071)** : il regarde l'avant sur les vues bâbord (044,
   123, 126) ; une même voile ne peut montrer le lion tourné vers l'avant des deux côtés.
3. **Coque plus longue et plus basse** que sur 044 et 126 (coques trapues, franc-bord haut, fort relèvement à l'avant) ;
   changer la forme toucherait la grille des pièces, la flottaison, la passerelle et les tests : gardé (40 × 12, la
   longueur demandée).
4. **Étage du château arrière plus court** : la salle d'apparat fait 4 blocs de long ; 044 et 071 montrent un étage
   long de ≈ 8 blocs, à 4 ou 5 fenêtres par côté. Le gaillard, la barre et l'auvent occupent l'avant du château.
5. **Huniers** : présents (071, 123) alors que 044 et 126 n'ont qu'une basse voile par mât ; les flèches au-dessus des
   huniers restent un peu longues (≈ 4 blocs au lieu de 2 à 3).
6. **Écartement des mâts** : sur 044 et 071 la misaine est un peu plus en avant et le grand mât un peu plus en arrière
   (≈ 12,8 blocs entre eux au lieu de 10,5) ; les mâts traversent les pièces, gardés.
7. **Figure de proue** : buste de lion agrandi (tête, crinière, pattes avant), mais pas le lion bondissant entier de 123 ;
   071 n'a pas de lion (éperon doré en gradins) : le lion de 123/126 est gardé, comme le demande la consigne.
8. **Bannières pendantes** de 044, 123 et 126 remplacées par les grands écus de 071 (demandés par la consigne).
9. Éclairage chaud et reflets des images (rendu de jeu plus plat) ; ferrures grises de 044 rendues en or.

Les écarts 3 à 8 sont traités en phase 4 (§ 5 quater).

## 5 quater. Phase 4 : fidélité de structure

**Ce qui a été changé** (les écarts de structure laissés par la phase 3, qui touchaient la grille, la flottaison, la
passerelle et les tests) :

| Changement | Avant (phase 3) | Après (phase 4) | Ce qui a suivi |
|---|---|---|---|
| Franc-bord | pont 4,5, lisse 6,2 | **tous les niveaux +0,5** : pont 5,0, cabine 5,0, gaillard d'arrière 8,5, gaillard d'avant 7,0 (4 marches), pont inférieur 1,5, lisse 6,7 | grille, escaliers, descentes, sièges, passerelle (charnière 6,95, longueur 9,5, dénivelé max 6,35), test en jeu |
| Tonture | +1,8 à l'avant, +0,4 à l'arrière (puissance 2,6) | **+3,6 à l'avant, +1,2 à l'arrière (puissance 2)**, quille relevée de 2,6 aux extrémités : coque trapue en croissant (044, 126) | préceintes, bandes, bastingage, beaupré relevé, `HullShape` Java, valeurs du test |
| Château arrière | 9,5 blocs ; salle d'apparat 4 blocs (2 fenêtres par côté) | **12 blocs** (cloison à −8), **étage de 8 blocs** (plafond 12,0) : 5 grandes fenêtres en arc par côté, 4 au tableau, balcon, lucarnes, balustrade et lanternes sur le toit, deux galeries de poupe | cabine de 11 blocs (4 fenêtres par côté, coin lecture), salle d'apparat réaménagée, deux portes, sondes, test en jeu |
| Mâts | misaine 9,5, grand mât −1, artimon −12,2 (10,5 entre misaine et grand mât) | **misaine 12,5, grand mât −0,5, artimon −11,5** (13 blocs ; artimon contre la façade de l'étage, entre ses deux portes) | barre et auvent devant l'artimon (roue −9,4), escaliers du gaillard d'arrière (−4,5 → −8), cales et cargaison, tests |
| Voiles | grand-voile 11 × 21,8, flèches de 4,9 au-dessus des huniers | **grand-voile 11,7 × 24, misaine 10,6 × 22, huniers 6 à 6,4**, flèches 2,7 ; pommes 29,5 / 30,5 / 26 | sondes des vergues (`YARD_HALF` 11,4) |
| Lions des voiles | 0,65 de la hauteur, silhouette en bloc | **rampant héraldique redessiné**, 0,8 de la hauteur, 1,45 fois plus large, cerné, relief doré (aussi sur les écus, bannières, tapis, flammes) | texture des voiles (régions agrandies) |
| Figure de proue | buste (tête, crinière, pattes avant) | **lion bondissant entier** (123) | sondes `FIGUREHEAD_PROBE` (0 ; 9,4 ; 28,5), `FIGUREHEAD_PAW_PROBE` (0 ; 6,9 ; 29,5) |
| Bannières | sur les flancs du château seulement | **bannières pendues sous la lisse entre les écus** (044, 123, 126), écus ramenés sur le pont (4 par bord) | pas de bannière à tribord devant la passerelle |

**Méthode.** Mêmes caméras recalées que la phase 3 (`cams.json`), plus des caméras à longue focale (20°) pour 071 et
126, dont la perspective est plus plate que celle d'un objectif de 35° ; rétroprojection des pommes de mât des images
sur le plan axial (044 : misaine ≈ 13,5 à 14, grand mât ≈ −0,5, artimon ≈ −13 ; 071 : 14,8, 2,0, −8,4) ; fondus image
et rendu superposés pour la silhouette ; quatre itérations :

| Itération | Écarts relevés | Corrections |
|---|---|---|
| 1 | (nouvelle structure) mâts trop hauts sur 071 (flammes hors du cadre) ; lion des voiles illisible de biais ; pied des basses voiles trop bas sur 044 | pommes ramenées à 29,5 / 30,5 / 26, huniers relevés jusqu'à 2,7 sous les pommes, pied de la grand-voile remonté ; lion élargi (1,45) et épaissi |
| 2 | sur 126 et 071 l'étage du château paraît bas ; fenêtres de l'étage petites | étage porté à 3,5 de haut (plafond 12,0), fenêtres 1,1 × 2,0 sous moulures dorées |
| 3 | bannières courtes (044 : elles descendent presque jusqu'à la flottaison) ; sommet du château nu (071 : lanternes sur poteaux) | bannières de 3,9, lanternes déplacées à côté ; lanternes sur poteaux aux coins du toit |
| 4 | basses voiles encore un peu petites devant les images | grand-voile 11,7 × 24, misaine 10,6 × 22 ; contrôles : silhouette de 044 superposée (mâts, coque, château et voiles au même endroit), lions lisibles de biais |

**Écarts restants (classés) :**

1. **Voiles vues de biais** : les images les montrent de face quel que soit le côté ; vergues orientées de 6° (bras
   bâbord en arrière) comme en phase 3 ; elles paraissent donc plus étroites que sur les images dès qu'on n'est pas
   dans l'axe.
2. **Lion des voiles tourné vers la poupe vu de tribord (071)** : une même voile ne peut montrer le lion tourné vers
   l'avant des deux côtés (il l'est sur les trois vues bâbord).
3. **071 montre le château plus grand que la proue** (perspective de l'image, plus plate qu'un vrai objectif) : avec
   une caméra à longue focale l'écart se réduit ; la hauteur du château (toit à 13,2, lanternes à 14,5) est celle de
   044.
4. **126 a des mâts disposés autrement** (grand mât très en avant, artimon au milieu du toit) : la disposition suit
   044 et 071, comme le demande la consigne (126 sert pour la proue et le château).
5. **Huniers** gardés (071, 123) alors que 044 et 126 n'ont qu'une voile par mât.
6. Coque un peu plus bleue que sur 044 (plus brune) : les bandes suivent 071, l'image principale.
7. Éclairage chaud et reflets des images ; ferrures grises de 044 rendues en or.

## 6. Passerelle d'embarquement

Système existant (`docs/PASSERELLES.md`, `core/Gangplank.java`) : spécification ajoutée à `tools/gangplank/ships_g2.py`
(une entrée `place(...)` et une entrée `COMPACT`), camouflage ajouté à `tools/gangplank/gangplanklib.py` (une entrée
`CAMO_SHIPS` / `CAMO`, atlas `textures/entity/gangplank.png` régénéré : seule la nouvelle case change).

| Côté | Charnière (x, y, z) | Largeur × longueur | Style | Escalier intérieur | Pentes | Dénivelé max | Levier |
|---|---|---|---|---|---|---|---|
| tribord | −5,47 ; 6,95 ; 3,0 | 3,0 × 9,5 | bois sombre ferré | 5 marches (pont 5,0 → 6,95) | −15° à 42° | 6,35 | −4,55 ; 5,0 ; 4,95 |

Posée sur la lisse dorée au milieu du pont, entre les haubans du grand mât et de la misaine (l'écoutille de la cale est
à bâbord). Rangée : paquet compact de 16 segments télescopiques, pendu à 0,9 sous la charnière, à plat contre le
bastingage (`stow_offset` 0,07, `stow_tilt` 9°, mesurés par `ships_g2.py compact`), peau dorée échantillonnée par
`ships_g2.py camo`. Testée par `GangplankSpecsTest` / `GangplankFoldTest` (le navire est ajouté à leurs listes) et en
jeu par `RoyalLionShipGameTest` (quai de pierre, levier, déployée puis repliée).

## 7. Guide du joueur

* Objet *Navire royal au lion* (*Royal Lion Ship*) dans l'onglet *Navires médiévaux*, ou `/ship give royal_lion_ship`
  ; **clic droit sur l'eau** pour le mettre à l'eau (eau profonde et dégagée : ≈ 53 blocs de long, 12 de large, quille à
  3,6 sous la flottaison) ; `/ship spawn royal_lion_ship` à votre position.
* **Monter à bord** : clic droit sur la coque (dépôt sur le pont principal) ou par la passerelle (levier sur le pont,
  côté tribord) depuis un quai. On marche pendant la navigation sur le pont, les deux gaillards, dans la cabine du
  capitaine, la salle d'apparat (à l'étage du château : deux portes doubles de part et d'autre de l'artimon, clic
  droit), les quartiers de l'équipage et la cale (descentes).
* **S'asseoir** : clic droit sur un siège (fauteuil du capitaine, banquette de poupe, fauteuils du coin lecture,
  chaises et trônes de la salle d'apparat, bancs du carré et du pont, tabouret de la cale) ; touche de sneak pour se relever à côté.
* **Piloter** : clic droit sur la roue du gaillard d'arrière ; navire très lourd (≈ 17 s pour prendre l'allure normale,
  longue erre, 5,5°/s en virage au plus) ; écume à l'étrave.
* **Réglages** : bloc `ships.royal_lion_ship` de `config/medievalships.json` (`slowSpeed` 1.4, `normalSpeed` 3.4,
  `fastSpeed` 5.6, `acceleration` 0.2, `braking` 0.36, `waterDrag` 0.045, `maxTurnRate` 5.5, `waveRocking` 0.6,
  `aiWaypointRadius` 15, `aiLookahead` 30, `aiProbeDistance` 80…). Pilote automatique comme les autres navires.

## 8. Fichiers, tests, limites

* Modèle `blockbench/royal_lion_ship.bbmodel` (≈ 7 300 cubes dont ≈ 1 100 de meubles, 2 textures : coque + voiles/flammes, 10 animations),
  textures `textures/entity/royal_lion_ship.png` et `royal_lion_ship_sails.png`, icône
  `textures/item/royal_lion_ship.png`, grille `interiors/royal_lion_ship.grid`, mobilier
  `interiors/royal_lion_ship_decor.json` (blocs des mods de décoration ; boîtes de remplacement si un mod manque),
  passerelle `gangplanks/royal_lion_ship.json` + `models/entity/gangplank_royal_lion_ship.bbmodel`.
* Java : `RoyalLionLayout` (géométrie, sondes, réglages), `RoyalLionShipEntity` ; tests `RoyalLionShipTest` (forme,
  dimensions, pièces, escaliers, portes, sièges, embarquement, coque fermée, pièces meublées, modèle, animations) et
  `RoyalLionShipGameTest` (en jeu, solo et serveur dédié : mise à l'eau, flottaison, vues des références, toutes les
  pièces, marche sur le pont, les quatre portes, pièces meublées photographiées, assis puis relevé sur trois sièges, marche entre
  les meubles de la cale et de la cabine, passerelle, barre).
* Comparaisons rendu / référence : `docs/comparaison_royal_lion_ship.png` (phase 4 : les quatre images, chacune à côté
  du rendu au même cadrage — 071 à longue focale —, puis le château arrière, le lion de proue, le profil et les lions
  des voiles) ; `docs/preview_royal_lion_ship.png` (même planche, refaite avec le modèle de la phase 4) ;
  `docs/interieur_royal_lion_ship.png` (les pièces, refaites avec la cabine et la salle d'apparat agrandies).
* Limites : les fenêtres de la cabine et de la salle d'apparat sont vues de l'intérieur comme des vitres (on ne voit pas
  la mer au travers : parois de la grille pleines) ; le toit du château n'est pas praticable ; la figure de proue et les écus sont décoratifs ; sans les mods de décoration, les meubles des mods sont
  remplacés par des boîtes.
