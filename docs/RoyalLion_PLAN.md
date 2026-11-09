# Le Navire royal au lion (`royal_lion_ship`) — plan

Navire de la cité de **Lion Port** (lot 2, version 1.27.0). Navire marchand royal : richesse, puissance commerciale,
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
| Franc-bord | flottaison ≈ y 900 → lisse du milieu ≈ y 690 | ≈ 6 blocs : **lisse à 6,2** au-dessus de l'eau |
| Château arrière | sommet du toit ≈ y 480 | ≈ 12,4 blocs : **toit à 12,1 (+ lanterne de faîte à 15,5)** |
| Grand mât | pomme ≈ y 30 (044) ; plus haut sur 071 (huniers) | 25,6 (044) à ≈ 34 (071) : **30,5** (misaine 29, artimon 22,5) |
| Grand-voile | vergue ≈ y 215, bordure ≈ y 560, largeur ≈ 410 px | **8 → 19 de haut, 17,6 → 19,2 de large** (élargie, voir § 5 bis) |
| Hune du grand mât | ≈ y 130 | **20,0** (misaine 19,2, artimon 18,4) |
| Bandes de coque (071) | bois sombre ≈ 40 % du franc-bord, puis or / bleu / or / bleu / or | brun jusqu'à 2,0 (sabords éclairés à 1,3), préceinte d'or 2,0–2,3, bande bleue, préceinte d'or 3,3–3,6, bande bleue des écus, lisse d'or à 5,0 |
| Écus (071) | 2 visibles par bord sur la moitié vue, ≈ 1,7 × 2 blocs | **5 écus par bord** (z −14,5, −8,5, −2,5, 6,5, 12,5), lanternes entre eux |

Cohérence avec les autres navires (`core/Ships.java`) : frégate bleue 36 × 10 (46 hors-tout, 33,4 de haut),
galion 35 × 9, vaisseau de guerre 55 × 13. Le navire royal (40 × 12, 51 hors-tout, ≈ 34 de la quille à la pomme du
grand mât) est plus grand et plus lourd que la frégate, plus petit que le vaisseau de guerre.

## 2. Dimensions retenues

* Coque 40 × 12 blocs, 51 avec le beaupré ; quille −3,6, lisse 6,2 au milieu (relevée à 8,0 à l'étrave, 6,6 à la
  poupe) ; avant plein et arrondi (puissance 2,6), arrière large sous le château (tableau 9,2 de large) ; rentrée des
  hauts 0,4 ; étrave inclinée.
* Mâts : misaine z = 9,5 (pomme 29), grand mât z = −1 (30,5), artimon z = −12,2 sur le gaillard (22,5) ; beaupré de
  (0, 7,2, 17) à (0, 13, 31).
* Voiles carrées orientées de −10° (vergues bâbord vers l'avant) : elles montrent leur face sur la vue de 071 comme sur
  celles de 044 et 126.

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Toit du château | 11,0 → 12,1 | toit bleu en mansarde (ardoises bleues, arêtiers et égouts dorés), crête dorée, fleurons dorés aux angles, lanterne de faîte à coupole bleue et flèche d'or, étendard royal au lion (décoratif, non praticable) |
| Salle d'apparat (dunette) | 8,0 → 11,0 | **royal state room** à l'arrière du gaillard (z −19,5 → −16,5), porte double sur sa façade, fenêtres en arc (4 à l'arrière, 2 par côté, 2 en façade) |
| Gaillard d'arrière | 8,0 | barre (roue z = −14, pilote debout z = −14,8) sous l'**auvent rayé bleu et blanc** festonné, artimon, balustrades dorées |
| Gaillard d'avant | 6,0 | de z = 13 à l'étrave, balustrade dorée, cloche ; 2 escaliers depuis le pont (3 marches) |
| Pont principal | 4,5 | du château (z −10,5) au gaillard d'avant ; 2 escaliers vers le gaillard d'arrière (7 marches, z −7 → −10,5) ; descente tribord vers les quartiers (x −2,2…−0,7, z −3,5 → −7), descente bâbord vers la cale (x 2…3,5, z 7 → 3,5) ; cabestan, caillebotis, râteliers, cargaison |
| Cabine du capitaine | 4,5 | sous le gaillard, z −19,5 → −11, porte double sur la cloison avant ; fenêtres en arc (4 au tableau derrière la galerie dorée, 3 par côté) |
| Quartiers de l'équipage | 1,0 | pont inférieur arrière, z −15 → −3 |
| Cale | 1,0 | pont inférieur avant, z −2,5 → 14,5, cloison avec porte double entre les deux ; la misaine et le grand mât la traversent jusqu'à la quille |

Hauteurs libres : pont inférieur 3 blocs, cabine 3, salle d'apparat 3. Toutes les pièces sont dans la coque (grille
fermée sous le pont : aucune sortie par la coque, vérifié par `RoyalLionShipTest`).

## 4. Sièges (17 places assises en plus de la barre)

La barre (pilote debout) ; dans la cabine du capitaine, le fauteuil à haut dossier devant le bureau et deux places sur
la banquette sous les fenêtres de poupe ; dans la salle d'apparat, trois chaises dorées en velours rouge et deux
trônes aux bouts de la table ; dans les quartiers de l'équipage, quatre places sur les bancs du carré ; dans la cale, le
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

Laissé libre (vérifié par `RoyalLionShipTest` et par `apply_to_grid` de l'outil) : les portes et leurs abords, les
escaliers et descentes avec leur pied, l'axe de la cabine, des quartiers et de la cale, une bande de 1,9 bloc de part et
d'autre de l'axe du pont principal (points d'embarquement), l'escalier et le levier de la passerelle (tribord, z 1,2 à
5,3), le passage vers les escaliers du gaillard d'arrière, les points de relevé des sièges. Aucun meuble n'entre dans
la coque, les cloisons ou les ponts (l'outil refuse plus de 0,3 bloc dans une case pleine ; le test vérifie qu'aucun
bloc n'est dans une paroi ni au-delà des flancs). Textures ajoutées à l'atlas de la coque (`tools/royal_lion_texture.py`,
cases libres) : tapis au lion, toile blanche des ballots, velours bleu, cire, pièces d'or, globe, étoffes rouge et or,
registre, tapisserie au lion. Planche des pièces : `docs/interieur_royal_lion_ship.png`.

## 5. Extérieur : matériaux, ornements, parties mobiles

* **Coque** : bois brun sombre (mosaïque de blocs) avec une rangée de petits sabords éclairés à cadre doré ; préceintes
  d'or ; deux bandes bleu roi en mosaïque ; **écus bleu roi en forme d'écu à pointe, bordure d'or et lion rampant
  d'or**, sur rondelle sombre à clous dorés ; lanternes pendues à des potences de fer entre les écus ; lisse dorée,
  bastingage bleu et **balustrade dorée** (balustres, poteaux à pommeau, lanternes sur certains poteaux).
* **Proue** : étrave dorée, lisses d'éperon dorées en gradins jusqu'au beaupré, bossoirs à tête de lion, ancres,
  **figure de proue : lion doré** (grosse tête à crinière, gueule rugissante, langue rouge, crocs, pattes avant tendues
  griffes dehors, console sculptée), lanterne pendue sous le beaupré, beaupré brun cerclé d'or et bout-dehors.
* **Château arrière** : panneaux bleus encadrés d'or, pilastres dorés, corniche en volutes dorées, fenêtres en arc
  éclairées, **galerie de poupe** dorée sur consoles, panneau au lion sur la voûte, bannières au lion sur les flancs,
  salle d'apparat sous le **toit bleu en mansarde**, lanternes d'angle sur potences, lanterne de faîte.
* **Mâture** : mâts bruns cerclés d'or, **hunes rondes à garde-corps doré et quatre lanternes**, chouques dorés ;
  **voiles bleu roi en blocs de toile, larges bordures d'or et filet d'or le long des chutes, grand lion rampant d'or
  sur la grand-voile et la misaine** ; huniers ; voile carrée d'artimon ; deux focs bleus bordés d'or ;
  **flammes bleues bordées d'or à queue d'aronde** (petit lion d'or au guindant) aux trois pommes ; étendard royal au
  lion au mât de pavillon arrière ; **enfléchures (échelles de corde) claires** jusqu'aux hunes, galhaubans, étais,
  bras, écoutes.
* **Parties mobiles** (os du modèle) : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran (`steer`),
  flammes et étendard (`flag_wave`), lanternes (`lantern_sway`), cordages lâches (`rope_sway`), portes
  (`door_0` cabine, `door_1` salle d'apparat, `door_2` cloison du pont inférieur).
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

Écarts restants (pour la phase 3) : voiles un peu moins grandes que sur les images (qui les exagèrent) ; la coque
reste plus longue et plus basse que sur 071 (perspective exagérée de l'image) ; les bannières pendantes de 044 sont
remplacées par les écus demandés ; la tête du lion de proue reste plus simple que la sculpture de 126. La cargaison
des références (caisses bâchées de blanc, ballots) est faite en phase 2 (§ 4 bis).

## 6. Passerelle d'embarquement

Système existant (`docs/PASSERELLES.md`, `core/Gangplank.java`) : spécification ajoutée à `tools/gangplank/ships_g2.py`
(une entrée `place(...)` et une entrée `COMPACT`), camouflage ajouté à `tools/gangplank/gangplanklib.py` (une entrée
`CAMO_SHIPS` / `CAMO`, atlas `textures/entity/gangplank.png` régénéré : seule la nouvelle case change).

| Côté | Charnière (x, y, z) | Largeur × longueur | Style | Escalier intérieur | Pentes | Dénivelé max | Levier |
|---|---|---|---|---|---|---|---|
| tribord | −5,47 ; 6,40 ; 3,0 | 3,0 × 9,0 | bois sombre ferré | 5 marches (pont 4,5 → 6,4) | −15° à 42° | 6,02 | −4,55 ; 4,5 ; 4,95 |

Posée sur la lisse dorée au milieu du pont, entre les haubans du grand mât et de la misaine (l'écoutille de la cale est
à bâbord). Rangée : paquet compact de 16 segments télescopiques, pendu à 1,0 sous la charnière, à plat contre le
bastingage (`stow_offset` 0,14, `stow_tilt` 13°, mesurés par `ships_g2.py compact`), peau dorée échantillonnée par
`ships_g2.py camo`. Testée par `GangplankSpecsTest` / `GangplankFoldTest` (le navire est ajouté à leurs listes) et en
jeu par `RoyalLionShipGameTest` (quai de pierre, levier, déployée puis repliée).

## 7. Guide du joueur

* Objet *Navire royal au lion* (*Royal Lion Ship*) dans l'onglet *Navires médiévaux*, ou `/ship give royal_lion_ship`
  ; **clic droit sur l'eau** pour le mettre à l'eau (eau profonde et dégagée : ≈ 53 blocs de long, 12 de large, quille à
  3,6 sous la flottaison) ; `/ship spawn royal_lion_ship` à votre position.
* **Monter à bord** : clic droit sur la coque (dépôt sur le pont principal) ou par la passerelle (levier sur le pont,
  côté tribord) depuis un quai. On marche pendant la navigation sur le pont, les deux gaillards, dans la cabine du
  capitaine, la salle d'apparat (portes doubles, clic droit), les quartiers de l'équipage et la cale (descentes).
* **S'asseoir** : clic droit sur un siège (fauteuil du capitaine, banquette de poupe, chaises et trônes de la salle
  d'apparat, bancs du carré et du pont, tabouret de la cale) ; touche de sneak pour se relever à côté.
* **Piloter** : clic droit sur la roue du gaillard d'arrière ; navire très lourd (≈ 17 s pour prendre l'allure normale,
  longue erre, 5,5°/s en virage au plus) ; écume à l'étrave.
* **Réglages** : bloc `ships.royal_lion_ship` de `config/medievalships.json` (`slowSpeed` 1.4, `normalSpeed` 3.4,
  `fastSpeed` 5.6, `acceleration` 0.2, `braking` 0.36, `waterDrag` 0.045, `maxTurnRate` 5.5, `waveRocking` 0.6,
  `aiWaypointRadius` 15, `aiLookahead` 30, `aiProbeDistance` 80…). Pilote automatique comme les autres navires.

## 8. Fichiers, tests, limites

* Modèle `blockbench/royal_lion_ship.bbmodel` (≈ 6 300 cubes dont ≈ 1 070 de meubles, 2 textures : coque + voiles/flammes, 9 animations),
  textures `textures/entity/royal_lion_ship.png` et `royal_lion_ship_sails.png`, icône
  `textures/item/royal_lion_ship.png`, grille `interiors/royal_lion_ship.grid`, mobilier
  `interiors/royal_lion_ship_decor.json` (blocs des mods de décoration ; boîtes de remplacement si un mod manque),
  passerelle `gangplanks/royal_lion_ship.json` + `models/entity/gangplank_royal_lion_ship.bbmodel`.
* Java : `RoyalLionLayout` (géométrie, sondes, réglages), `RoyalLionShipEntity` ; tests `RoyalLionShipTest` (forme,
  dimensions, pièces, escaliers, portes, sièges, embarquement, coque fermée, pièces meublées, modèle, animations) et
  `RoyalLionShipGameTest` (en jeu, solo et serveur dédié : mise à l'eau, flottaison, vues des références, toutes les
  pièces, marche sur le pont, portes, pièces meublées photographiées, assis puis relevé sur trois sièges, marche entre
  les meubles de la cale et de la cabine, passerelle, barre).
* Comparaisons rendu / référence : `docs/preview_royal_lion_ship.png` (planche de la phase 1) ; la planche
  `docs/comparaison_royal_lion_ship.png` est faite en phase 3.
* Limites : les fenêtres de la cabine et de la salle d'apparat sont vues de l'intérieur comme des vitres (on ne voit pas
  la mer au travers : parois de la grille pleines) ; le toit du château n'est pas praticable ; la figure de proue et les écus sont décoratifs ; sans les mods de décoration, les meubles des mods sont
  remplacés par des boîtes.
