# Le Navire forteresse (`fortress_ship`) — plan

Ville : **Havre-Fort** (déduit du fort des images). Nom : fr « Navire forteresse », en « Fortress Ship ».

Coordonnées du navire en blocs : x latéral (+x = bâbord), y vertical (0 = ligne de flottaison), z longitudinal
(+z = proue). Sources : `tools/fortress_shape.py` (forme, niveaux), `tools/fortress_interior.py` (grille des pièces),
`tools/generate_fortress.py` (modèle, gréement, animations), `tools/fortress_texture.py` (textures),
`tools/fortress_decor.py` (mobilier, sièges), `tools/fortress_gangplank.py` (passerelle), `FortressLayout.java`
(mêmes nombres).

**Règle permanente du mod** : le navire utilise le système de navires du mod lui-même (entité `ShipEntity`, grille
intérieure, collisions et transport des joueurs du mod) — **pas de Valkyrien Skies / Eureka, pas de GeckoLib** ; aucune
apparition naturelle (objet, `/ship give`, `/ship spawn`).

## 1. Mesures relevées sur les images de référence

Trois images du même navire (variantes) : `fortress_ship_1_img112.png` (principale, voxel, flanc bâbord presque de
travers, fond sombre), `_2_img151.png` (voxel, trois-quarts avant bâbord, en mer devant le fort : grue et caisse
suspendue, tauds), `_3_img149.png` (peinture, flanc tribord de trois-quarts arrière : bandes de fer, écu sur l'avant,
bannière au beaupré). Proportions prises sur 112 (≈ 33 px par bloc pour une coque de ≈ 43 blocs de la tête de l'étrave
au couronnement du château).

| Élément (image 112, 1536 × 1024 px) | Mesure (px) | Lecture |
|---|---|---|
| Coque | tête de l'étrave x ≈ 40 → château x ≈ 1460 en haut ; quille x ≈ 290 → 1300 en bas | **43 blocs** hors tout (étrave très élancée : la tête dépasse le pied d'étrave de ≈ 7 blocs), 48,5 avec le beaupré |
| Hauteurs (flottaison y ≈ 900 sous la préceinte basse) | lisse de pierre du passavant y ≈ 735 ; gaillard d'avant y ≈ 680 ; tête de proue y ≈ 575 ; quille y ≈ 1000 | lisse du passavant 5,5 ; pavois du gaillard 7,5 ; bec de pierre 10,1 ; quille −3,0 |
| Bordé | bandeau de pierre 700–740, bande sombre cloutée 740–770, panneaux rouges 775–850, préceinte de pierre 860–905, bois sombre dessous | bandeau de pierre clouté (4,4–5,3) sous la lisse, bande sombre cloutée (3,3–4,35), panneaux rouges entre les nervures (1,5–3,3), préceinte de pierre à la flottaison (0–0,8), bois sombre dessous |
| Nervures de pierre | colonnes verticales tous les ≈ 180 px, flanquées de plaques de fer cloutées | 8 nervures par bord (z −19 … 15, tous les ≈ 5 blocs), plaques de fer de chaque côté |
| Château arrière | parapet crénelé y 500–540 (x 1180–1460), étage bas à fenêtres éclairées y 650–720, tourelle x 1230–1400 y 380–500, toit rouge pyramidal 300–400, épi + lanterne y 260–330 | dunette 8,0 sur la cabine du capitaine (4,5), donjon jusqu'au toit-terrasse 11,0 (parapet 12,0 + merlons), tourelle 11,0–14,5, toit rouge en gradins jusqu'à 18,6, épi et lanterne à ≈ 21 |
| Mâts | misaine x ≈ 500, grand mât x ≈ 800, artimon x ≈ 1140 ; pommes y ≈ 150 / 95 / 95 | misaine z = 8 (sur le gaillard), grand mât z = −1, artimon z = −11,5 (sur la dunette, devant le donjon) ; têtes 24 / 27,5 / 24,5 |
| Voiles | misaine : basse voile + petit hunier ; grand mât : grande basse voile (tour) + hunier ; artimon : une voile | rouges à bandes blanches sur les chutes et en tête ; tour crénelée beige à porte sur les basses voiles de misaine et du grand mât (comme 151) ; huniers encadrés de blanc ; voile d'artimon rayée ; bas des voiles en escalier, usé |
| Foc | grand triangle blanc à bande rouge vers le beaupré | un foc blanc à bande rouge sur l'étai de hunier de misaine |
| Flammes | rouges, longues, à queue d'aronde en escalier, en tête de chaque mât | trois flammes rouges (4,0 / 5,2 / 4,4 de long) |
| Hunes | caisses grises crénelées | hunes carrées à parapet de pierre et merlons |
| Bannières | rouges à tour blanche, pied en pointe : flanc du gaillard (2,5 × 5 blocs), flanc et coin arrière du château | bannières sur les flancs du gaillard, du château, au coin arrière du donjon, au tableau, au beaupré (149) |
| Détails 151 / 149 | grue à flèche horizontale et caisse suspendue près de l'artimon ; taud blanc ; écu à tour sur l'avant (149) ; bannière au beaupré (149) | grue sur l'artimon (flèche au-dessus du passavant, caisse balancée), taud sur la dunette tribord, écus à tour sur les deux joues de l'avant |

**Parties reconstruites** (non visibles ou variables selon les images) : le flanc tribord est le symétrique du flanc
bâbord de 112 ; le tableau arrière (non visible en 112 / 151) reprend le château de 149 : trois fenêtres éclairées pour
la cabine, deux pour le donjon, parapet crénelé sur consoles, grande bannière centrale, lanternes d'angle ; l'avant
reprend 112 (gaillard à balustrade de bois sur bordure de pierre, bec de pierre) avec le beaupré et la bannière de 149
(112 n'en montre qu'un étai) ; 151 (château plus massif à trois étages, voiles rouge sombre déchirées) est une variante
dont on garde la grue, le taud et les créneaux de pierre du passavant.

## 2. Dimensions retenues

* Coque 43 × 13 blocs (48,5 avec le beaupré) ; quille −3,0, lisse du passavant 5,5, bec de proue 10,1 ; hauteur de la
  quille à la pomme du grand mât 30,5.
* Coque massive et ronde (fond en V adouci, rentrée des hauts de 0,45), étrave très inclinée (0,42 bloc par bloc de
  hauteur), arrière large à tableau (9 blocs) ; murs du château et pavois verticaux au-dessus de la lisse.
* Beaupré de (0, 8,4, 19,5) à (0, 11,6, 28,0) ; vergues brassées de 38° (côté bâbord vers l'arrière) : les voiles
  montrent leur face sur les vues de flanc comme sur les images.

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Tourelle | 11,0 | sur le toit du donjon (z −19 … −15), porte vers l'avant, fenêtres éclairées, tabouret de vigie |
| Toit du donjon | 11,0 | terrasse crénelée autour de la tourelle ; trappe de l'escalier du donjon (bâbord) |
| Dunette | 8,0 | devant le donjon (z −13 … −9) : barre (roue z −9,7, pilote debout z −10,5), artimon (z −11,5), grue, taud ; porte du donjon ; parapet crénelé |
| Salle des officiers (donjon) | 8,0 | z −19 … −13,5, hauteur 2,5 ; table, tabourets, bibliothèque ; escalier intérieur (bâbord, 6 marches) vers le toit |
| Gaillard d'avant | 7,0 | z 6 … 19 ; misaine, cloche, balustrade de bois, deux escaliers depuis le passavant |
| Passavant (pont principal) | 4,5 | du château (z −9) au gaillard (z 6) ; deux escaliers vers la dunette (bords, z −5,5 → −9), deux vers le gaillard (z 3,5 → 6), descente bâbord vers le pont inférieur (z −1,5 → −5) ; caillebotis, cabestan, grand mât |
| Cabine du capitaine | 4,5 | sous la dunette, z −19 … −9,5, hauteur 3 ; porte double sur la cloison avant ; lit, coffre, bureau, carte, compas, fauteuil, table |
| Réfectoire de l'équipage | 4,5 | sous le gaillard, z 6,5 … 17, hauteur 2 ; porte double ; grande table et bancs |
| Cale | 1,0 | z −15 … 5,5, hauteur 3 ; tonneaux, caisses, sacs ; le grand mât la traverse |
| Quartiers de l'équipage | 1,0 | z 6 … 14, hauteur 3, porte double depuis la cale ; couchettes doubles, coffres ; la misaine les traverse |

Portes : 0 cabine, 1 donjon, 2 réfectoire, 3 quartiers de l'équipage, 4 tourelle (toutes doubles, clic droit).

## 4. Sièges

Pilote (debout à la barre) + 11 sièges (`fortress_decor.py`) : fauteuil du capitaine et tabouret de la cabine, deux
tabourets de la salle des officiers, tabouret de vigie de la tourelle, quatre places sur les bancs du réfectoire, deux
bancs du passavant. Chaque siège a son point de relevé libre sur un plancher (`FortressShipTest.helmAndSeats`). La
phase 2 (décoration) complète le mobilier.

## 5. Matériaux, parties mobiles, contraintes

* **Matériaux** : bordé de bois brun sombre ; pierre grise en blocs (16 px par bloc, joints sombres, clous de fer) pour
  la préceinte basse, le bandeau sous la lisse, les nervures, la lisse et ses merlons, les parapets, le bec et les
  hunes ; panneaux rouges (planches rouges) entre les nervures, plaques de fer cloutées ; château : étage bas en bois
  sombre à fenêtres éclairées entre pilastres de pierre, parapet de pierre courant sur tout le flanc, donjon à
  panneaux rouges et parapet crénelé en encorbellement sur consoles ; tourelle en planches sombres à poteaux, base de
  pierre, toit de tuiles rouges en gradins sur bandeau de pierre ; voiles rouges en blocs de laine (bords blancs,
  bandes blanches, tour beige), foc blanc à bande rouge ; échelles de corde en chanvre doré ; bannières rouges à tour,
  écus rouges à tour et bord d'or.
* **Parties mobiles** (os du modèle) : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran (`steer`), flammes
  (`flag_*`, `flag_wave`), lanternes, bannières et caisse de la grue (`lantern_*` / `banner_*`, `lantern_sway`),
  cordages lâches (`rope_sway`), portes (`door_0` … `door_4`).
* **Contraintes** : coque, ponts, pavois et pièces dessinés sur la grille (ce qui est dessiné est ce qui collisionne :
  surfaces des pièces tirées des cellules, doublage intérieur des pavois sur la face de collision) ; grille fermée sous
  le pont principal (aucune sortie par la coque, vérifié par `FortressShipTest`) ; sondes du pilote automatique au bout
  du beaupré, au bec, au safran, au parapet arrière et aux bouts de vergues ; ≈ 4 250 cubes.
* **Physique** (le plus lourd des voiliers) : accélération 0,18 bloc/s², freinage 0,35, virage 5°/s au plus, longue
  erre (`waterDrag` 0,045), roulis 0,55 ; vitesses 1,3 / 3,2 / 5,4 ; pilote automatique : rayon 15, anticipation 30,
  sondes 80.

## 6. Passerelle d'embarquement

Système existant (`docs/PASSERELLES.md`, `core/Gangplank.java`) : spec `gangplanks/fortress_ship.json` et modèle
`gangplank_fortress_ship.bbmodel` écrits par `tools/fortress_gangplank.py` (ajoute la spec à `ships_g2.py` à l'exécution,
sans le modifier). Tribord, au milieu du passavant (z 1,6, 3 blocs de large, 9 de long, style bois sombre), charnière
en haut du pavois (6,0) sur la face extérieure, escalier du pont (4,5) à la charnière, levier sur le pont à l'arrière ;
aucun merlon ni lisse dessiné au-dessus de la planche. Paquet rangé posé à plat sur le bandeau de pierre
(`stow_drop` 0,75, `stow_offset` 0,44, `stow_tilt` 8, mesurés par `fortress_gangplank.py compact`), peau grise de pierre
et liseré de fer (case `fortress_ship` de l'atlas `gangplank.png`, ajoutée dans `gangplanklib.py` à une place fixe, 13).

## 7. Guide du joueur

* Objet *Navire forteresse* (*Fortress Ship*) dans l'onglet créatif *Navires médiévaux*, ou
  `/ship give fortress_ship [joueurs]` ; **clic droit sur l'eau** pour le mettre à l'eau (eau profonde d'au moins 3,5
  blocs et dégagée : ≈ 50 × 20 blocs avec les vergues) ; `/ship spawn fortress_ship` à votre position.
* **Monter à bord** : clic droit sur la coque, ou la passerelle (levier sur le passavant tribord) depuis un quai. On
  marche pendant la navigation sur tous les niveaux : passavant, gaillard d'avant, dunette, toit du donjon (par
  l'escalier intérieur du donjon), tourelle, cabine, salle des officiers, réfectoire, cale, quartiers de l'équipage.
* **Piloter** : clic droit sur la roue de la dunette ; touches de déplacement de Minecraft (avancer, freiner / reculer,
  barre, allure Espace / Ctrl, Maj pour quitter). Très lent à prendre de l'erre et à s'arrêter, larges virages ; les
  voiles se carguent après 5 s à l'arrêt ; écume à l'étrave.
* **Pilote automatique** : comme les autres navires (`/ship route …`, `/ship ai …`, voir [COMMANDES.md](COMMANDES.md)).
* **Réglages** : bloc `ships.fortress_ship` de `config/medievalships.json`.

## 8. Fichiers, tests, limites

* Modèle `blockbench/fortress_ship.bbmodel` (2 textures : coque + voiles, 11 animations), textures
  `textures/entity/fortress_ship.png` et `fortress_ship_sails.png`, icône `textures/item/fortress_ship.png`, grille
  `interiors/fortress_ship.grid`, mobilier `interiors/fortress_ship_decor.json`. Aperçu : [preview_fortress_ship.png](preview_fortress_ship.png).
* Java : `FortressLayout`, `FortressShipEntity` ; tests `FortressShipTest` (forme, dimensions, pièces, escaliers, portes,
  sièges, coque fermée, embarquement, modèle, animations), `FortressShipGameTest` (en jeu : mise à l'eau près d'un
  quai, vues des trois références, tous les niveaux, marche, portes, passerelle déployée puis repliée, barre).
* Fichiers partagés modifiés (une entrée chacun) : `Ships.java`, `MedievalShips.java`, `ShipModels.java`, `en_us.json`,
  `fr_fr.json`, `NoZFightingTest`, `NewShipModelsTest` (+ `fortress_ship_reference_quads.json`), `GangplankSpecsTest`,
  `GangplankFoldTest` (taille nominale de l'ancien paquet en accordéon, que ce navire n'a jamais eu),
  `ShipClientGameTest` (un appel), `tools/gangplank/gangplanklib.py` + `textures/entity/gangplank.png` (case de
  camouflage). À la fusion des trois navires de la 1.27.0 : garder les lignes de chacun et régénérer l'atlas
  (`python3 tools/fortress_gangplank.py` réécrit l'atlas avec toutes les cases déclarées).
* Limites : les fenêtres du château ne se voient que de l'extérieur (murs de la grille pleins) ; pas de canons (rien de
  tel sur les images) ; la grue et sa caisse sont décoratives ; sans les mods de décoration, les meubles des mods sont
  remplacés par des boîtes ; le château de 151 (plus massif, à trois étages) n'est pas reproduit tel quel.
