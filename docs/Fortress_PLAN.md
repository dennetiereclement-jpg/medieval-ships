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
| Hauteurs (flottaison y ≈ 900 sous la préceinte basse ; 1.28.0 : l'eau est à y 0,6 du modèle, juste sous la préceinte de pierre, quille à 3,6 dessous) | lisse de pierre du passavant y ≈ 735 ; gaillard d'avant y ≈ 680 ; tête de proue y ≈ 575 ; quille y ≈ 1000 | lisse du passavant 5,5 ; pavois du gaillard 7,5 ; bec de pierre 10,1 ; quille −3,0 |
| Bordé (relevé avec la caméra recalée de la phase 3) | lisse de pierre 730–755, bande sombre cloutée 755–785, panneaux rouges 785–850, préceinte de pierre 850–872, bois sombre jusqu'à la quille (970), nervures descendant en gradins dessous | bandeau de pierre clouté (4,5–5,3) et sa lisse, bande sombre cloutée (3,55–4,5), panneaux rouges entre les nervures (1,45–3,55), préceinte de pierre juste dessous (0,75–1,45), bois sombre dessous avec les contreforts de pierre des nervures en gradins ; bordé sombre sans panneaux rouges sous le gaillard d'avant |
| Nervures de pierre | colonnes verticales tous les ≈ 180 px, flanquées de plaques de fer cloutées | 8 nervures par bord (z −19 … 15, tous les ≈ 5 blocs), plaques de fer de chaque côté |
| Château arrière | parapet crénelé y 500–540 (x 1180–1460), étage bas à fenêtres éclairées y 650–720, tourelle x 1230–1400 y 380–500, toit rouge pyramidal 300–400, épi + lanterne y 260–330 | dunette 8,0 sur la cabine du capitaine (4,5), donjon jusqu'au toit-terrasse 11,0 (parapet 12,0 + merlons), tourelle 11,0–14,5, toit rouge bas en gradins jusqu'à 17,0 (relevé : avant-toit 15,2, faîte 16,9), épi et lanterne jusqu'à ≈ 19,4 |
| Mâts | misaine x ≈ 500, grand mât x ≈ 800, artimon x ≈ 1140 ; pommes y ≈ 150 / 95 / 95 | misaine z = 8 (sur le gaillard), grand mât z = −1, artimon z = −11,5 (sur la dunette, devant le donjon) ; têtes 24 / 27,5 / 24,5 ; hunes 18,1 / 21,1 / 20,9 (phase 4 : relevées, les vergues des basses voiles juste dessous) |
| Voiles (caméra recalée, superposition phase 4) | misaine : basse voile (vergue 17,65 → bordure 9,6) + petit hunier (19,0–21,4) ; grand mât : grande basse voile à la tour (20,65 → 9,0) + petit hunier (22,0–24,95) ; artimon : une voile (20,4 → 13,0) ; la tour de la grande voile réduite aux 3/4 de sa largeur (vergues brassées ≈ 45°) | basses voiles rouge cramoisi à larges chutes blanc-gris (≈ 1/7 de la largeur chacune), têtière rouge aux coins blancs ; grande tour crénelée beige à porte, centrée (≈ 1/3 de la largeur), sur la grande basse voile seulement (comme sur les trois images) ; petits huniers encadrés de blanc ; voile d'artimon rayée ; bas des voiles en escalier, usé |
| Foc | petit triangle blanc à bande rouge devant la misaine, amure au-dessus de l'étrave (≈ z 18, y 10,3) | un petit foc (trinquette, ≈ 60 % de celui de la phase 3) blanc à bande rouge sur l'étai de misaine, amure au-dessus de l'étrave, point d'écoute au-dessus du gaillard |
| Flammes | rouges, longues, à queue d'aronde en escalier, en tête de chaque mât | trois flammes rouges (4,0 / 5,2 / 4,4 de long) |
| Hunes | caisses grises crénelées (112), hunes rondes en bois crénelées (149) | hunes rondes en bois (12 douelles, cercle de fer) à créneaux de bois (phase 4, comme 149) |
| Bannières | rouges à tour blanche, pied en pointe : flanc du gaillard (2,5 × 5 blocs), flanc et coin arrière du château | bannières sur les flancs du gaillard, du château, au coin arrière du donjon, au tableau, au beaupré (149) |
| Détails 151 / 149 | grue à flèche horizontale et caisse suspendue près de l'artimon ; taud blanc ; écu à tour sur l'avant (149) ; bannière au beaupré (149) | grue sur l'artimon (flèche au-dessus du passavant, caisse balancée), taud sur la dunette tribord, écus à tour sur les deux joues de l'avant |

**Parties reconstruites** (non visibles ou variables selon les images) : le flanc tribord est le symétrique du flanc
bâbord de 112 ; le tableau arrière (non visible en 112 / 151) reprend le château de 149 : trois fenêtres éclairées pour
la cabine, l'étage du donjon en encorbellement au-dessus du tableau sur une rangée de grosses consoles (le château
déborde l'arrière en 112) avec deux fenêtres, parapet crénelé sur consoles, grande bannière centrale, lanternes
d'angle ; l'avant
reprend 112 (gaillard à balustrade de bois sur bordure de pierre, bec de pierre) avec le beaupré et la bannière de 149
(112 n'en montre qu'un étai) ; 151 (château plus massif à trois étages, voiles rouge sombre déchirées) est une variante
dont on garde la grue, le taud et les créneaux de pierre du passavant.

## 2. Dimensions retenues

* Coque 43 × 13 blocs (48,5 avec le beaupré) ; quille −3,0, lisse du passavant 5,5, bec de proue 10,1 ; hauteur de la
  quille à la pomme du grand mât 30,5.
* Coque massive et ronde (fond en V adouci, rentrée des hauts de 0,45), étrave très inclinée (0,42 bloc par bloc de
  hauteur) ; à l'arrière (phase 4, comme 112) la coque rentre sous le château : voûte inclinée en gradins depuis le
  dessous du plancher de la cabine (y 4,0, z −19,15) jusqu'à la quille (y −1,6, z −16,55), l'étage de la cabine sur la
  ligne du tableau (z −19,5, 9 blocs de large) et le donjon en encorbellement d'un bloc (z −20,5) sur une rangée de
  consoles ; murs du château et pavois verticaux au-dessus de la lisse.
* Beaupré de (0, 8,4, 19,5) à (0, 11,6, 28,0) ; vergues brassées de 45° (côté bâbord vers l'arrière) : les voiles
  montrent leur face sur les vues de flanc comme sur les images (la tour de la grande voile y paraît aux 3/4 de sa largeur).

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Tourelle | 11,0 | sur le toit du donjon (z −18,5 … −14,5, centre −16,5 comme sur 112), porte vers l'avant, grandes fenêtres éclairées ; poste de vigie (table, longue-vue, coffre à pavillons) |
| Toit du donjon | 11,0 | terrasse crénelée autour de la tourelle, prolongée sur l'encorbellement (z −20 … −13,5) ; trappe de l'escalier du donjon (bâbord) ; râtelier de lances, tonneau de flèches (derrière la tourelle), brasero |
| Dunette | 8,0 | devant le donjon (z −13 … −9) : barre (roue z −9,7, pilote debout z −10,5), artimon (z −11,5), grue, taud ; porte du donjon ; parapet crénelé |
| Salle du conseil (donjon) | 8,0 | z −19 … −13,5, hauteur 2,5 ; table de guerre et ses sept chaises, bibliothèque, armure ; escalier intérieur (bâbord, 6 marches) vers le toit |
| Gaillard d'avant | 7,0 | z 6 … 19 ; misaine, cloche, balustrade de bois, deux escaliers depuis le passavant |
| Passavant (pont principal) | 4,5 | du château (z −9) au gaillard (z 6) ; deux escaliers vers la dunette (bords, z −5,5 → −9), deux vers le gaillard (z 3,5 → 6), descente bâbord vers le pont inférieur (z −1,5 → −5) ; caillebotis, cabestan, grand mât |
| Cabine du capitaine | 4,5 | sous la dunette, z −19 … −9,5, hauteur 3 ; porte double sur la cloison avant ; bureau face à la porte, lit, coffres, armure, râtelier |
| Réfectoire de l'équipage | 4,5 | sous le gaillard, z 6,5 … 17, hauteur 2 ; porte double ; grande table et bancs, cuisine |
| Cale | 1,0 | z −15 … 5,5, hauteur 3 ; vivres, armurerie, pierre et bois pour le fort ; le grand mât la traverse |
| Quartiers de l'équipage | 1,0 | z 6 … 14, hauteur 3, porte double depuis la cale ; couchettes doubles, coffres ; la misaine les traverse |

Portes : 0 cabine, 1 donjon, 2 réfectoire, 3 quartiers de l'équipage, 4 tourelle (toutes doubles, clic droit).

## 4. Sièges

Pilote (debout à la barre) + 24 sièges (`fortress_decor.py`) : le fauteuil du capitaine derrière son bureau et deux
chaises de velours devant ; à la table de guerre du donjon, le haut fauteuil du commandant, six chaises de velours (dont
une en bout de table) ; le tabouret de vigie de la tourelle ; six places sur les bancs du réfectoire et le tabouret en
bout de table ; deux tabourets à la table de jeu des quartiers de l'équipage ; deux bancs du passavant ; deux bancs sous
le taud de la dunette. Chaque siège a son point de relevé libre sur un plancher (`FortressShipTest.helmAndSeats`,
contrôlé aussi par `fortress_decor.check`) ; le test en jeu s'assoit sur trois d'entre eux et se relève.

## 4 bis. Décoration (phase 2)

Les blocs des mods de décoration d'abord (154 : Farmhouse Decorations, Furnish, Farmer's Delight, Lands of Icaria ; ils
sont dessinés par le navire là où ils sont posés et bougent avec lui, remplacés par une boîte de même taille si le mod
manque), les meubles modélisés (`tools/fortress_furniture.py`, 85 pièces) seulement pour ce qui leur manque ou doit
porter les armes de Havre-Fort (la tour blanche sur fond rouge). Planche des pièces : [interieur_fortress_ship.png](interieur_fortress_ship.png).

* **Cabine du capitaine** : le bureau en travers, face à la porte, le haut fauteuil du capitaine derrière lui contre les
  trois fenêtres de poupe (l'intérieur de chaque fenêtre dessiné, et celles de la cloison avant), deux chaises de
  velours rouge devant ; sur le bureau la carte marine, le compas, l'encrier et sa plume, une lettre scellée, le sablier,
  une lampe, des livres, le vin. Bâbord : le lit (tête à la poupe), le coffre du capitaine à son pied, une commode
  (boîte à cigares, chandelier), l'écu à la tour et ses épées croisées, un coffre sous la fenêtre, le râtelier
  (hallebardes, épées, lance) contre la cloison. Tribord : l'armure du capitaine sur son support (surcot rouge à la tour,
  heaume à crête, lance), la carte marine encadrée, une commode, la bibliothèque, l'armoire. Au milieu le tapis rouge à la
  tour blanche bordé de pierre et d'or, un lustre de fer forgé à bougies.
* **Salle du conseil** (donjon) : la table de guerre en travers de la salle, la carte de campagne (la côte, Havre-Fort,
  les routes) avec ses pions rouges et blancs, une dague plantée, deux chandeliers, le vin ; le haut fauteuil du
  commandant entre deux officiers côté poupe, trois chaises côté avant, une en bout de table ; la grande bannière à la
  tour entre les fenêtres de poupe, la bibliothèque, l'écu aux épées croisées entre les fenêtres de tribord, une armure
  au bouclier près de la porte, un râtelier de lances derrière le haut de l'escalier ; un lustre de fer au-dessus de la
  table. L'escalier du toit et son accès restent libres.
* **Tourelle** : la table du guetteur (carte, lampe) et son tabouret, la longue-vue sur trépied à la fenêtre de bâbord,
  le coffre des pavillons de signaux (rouges et blancs), la bannière, l'intérieur des fenêtres. Le socle de pierre de la
  tourelle n'est plus dessiné à l'intérieur (il couvrait le plancher de 0,6 bloc).
* **Réfectoire et cuisine** : la longue table au milieu, un banc de chaque côté et un tabouret en bout, couverte
  d'assiettes, de chopes, de pain et de fromage, d'un rôti et de vin ; la cuisine dans l'angle bâbord arrière (plan de
  travail, planche à découper, épicier, fourneau et marmite, poêles suspendues, tonneau en perce, jambons) ; les vivres
  à tribord (caisses de légumes, tonneau, sac) ; des tonneaux à l'avant ; l'intérieur des fenêtres de la cloison.
* **Quartiers de l'équipage** : quatre couchettes doubles le long des bords, deux hamacs au-dessus des coffres de marin à
  l'arrière, la table de jeu (dés, cartes, chopes, bougie) et ses deux tabourets, un portemanteau, deux lanternes.
* **Cale** : à bâbord les tonneaux couchés en pyramides sur leurs chantiers, des tonneaux, des caisses sur deux rangs,
  les caisses de pommes de terre, carottes, choux, oignons, betteraves, les sacs de riz, la paille et l'épeautre, un
  panier, des jarres ; à tribord l'armurerie (deux râteliers de lances, hallebardes et épées, deux écus aux épées
  croisées sur la cloison arrière, une armure, deux tonneaux de flèches, l'enclume de l'armurier), les palettes de
  pierre de taille et la pile de bois équarri pour le fort, une voile rouge de rechange roulée, des caisses sous une
  bâche amarrée, des caisses sur deux rangs, des jarres, un coffre, une glène ; trois lanternes. L'allée du milieu, le
  pied de la descente et la porte des quartiers restent libres.
* **Ponts** : la cargaison des références le long des pavois du passavant (caisses sur deux rangs, une caisse bâchée,
  tonneaux, sacs), des glènes au grand mât et au cabestan ; deux bancs sous le taud de la dunette, un tonneau et une
  glène à bâbord ; tonneaux, caisses, sac et câble de l'ancre lové sur le gaillard d'avant ; sur le toit du donjon un
  râtelier de lances contre les créneaux, un tonneau de flèches et le brasero de signal (braises et flammes lumineuses).
* **Dégagements** (vérifiés par `fortress_decor.check` à chaque génération et par `FortressShipTest`) : portes et
  leurs abords, escaliers et descente avec leurs pieds et leurs têtes, la trappe du toit, les allées de la cabine, de la
  cale et des quartiers, la bande d'embarquement du passavant (2,3 blocs de part et d'autre de l'axe), l'escalier et le
  levier de la passerelle, les points de relevé des sièges, les places du test en jeu ; aucune pièce n'entre dans les
  murs, les ponts ou la coque, et toutes les pièces restent accessibles depuis le passavant (portes ouvertes).

## 5. Matériaux, parties mobiles, contraintes

* **Matériaux** (refaits en phase 4 d'après 112) : la coque se lit en **bois sombre** (bordé brun foncé, joints plus
  sombres) ; la **pierre grise** (plus sombre et plus variée, chaque bloc biseauté avec un joint sombre, posée un bloc
  par face de cube pour que les joints suivent les arêtes) n'est qu'en bandes étroites et en nervures : une assise sous
  la lisse (0,65 + la lisse), la préceinte sous les panneaux rouges, les nervures (0,9 de large, une **plaque de fer
  noire à gros clous** sur leur face) et leurs contreforts en gradins, les quoins et cordons du château, les parapets et
  merlons ; **panneaux rouges** = planches rouges en carreaux d'un bloc à joints sombres, **encadrés** de chaque côté
  par un montant de bois sombre à clous de fer et dessus par la bande sombre cloutée ; sous le gaillard d'avant, bordé
  sombre clouté, planches rouges contre l'étrave ; château : étage de la cabine en planches sombres avec fenêtres en
  arc éclairées (149) entre des quoins de pierre, cordon de pierre, parapet de dunette en bois sombre à chaperon de
  pierre, merlons et lisse de bois ; donjon en planches sombres à panneaux rouges encadrés et fenêtres en arc,
  parapet de pierre sur consoles, merlons hauts avec lisse de bois ; tourelle en planches sombres à poteaux, toit de
  tuiles rouges en gradins sur bandeau de pierre ; voiles rouge cramoisi en blocs de laine (chutes blanc-gris, tour
  beige), foc blanc à bande rouge ; échelles de corde en chanvre doré ; bannières rouges à tour, grands écus rouges à
  tour et bord d'or sur l'avant.
* **Parties mobiles** (os du modèle) : voiles (`sail_*` : `sail_wind`, `sail_furl`), roue et safran (`steer`), flammes
  (`flag_*`, `flag_wave`), lanternes, bannières et caisse de la grue (`lantern_*` / `banner_*`, `lantern_sway`),
  cordages lâches (`rope_sway`), portes (`door_0` … `door_4`).
* **Contraintes** : coque, ponts, pavois et pièces dessinés sur la grille (ce qui est dessiné est ce qui collisionne :
  surfaces des pièces tirées des cellules, doublage intérieur des pavois sur la face de collision) ; grille fermée sous
  le pont principal (aucune sortie par la coque, vérifié par `FortressShipTest`) ; sondes du pilote automatique au bout
  du beaupré, au bec, au safran, au parapet arrière et aux bouts de vergues ; ≈ 5 860 cubes (phase 5).
* **Physique** (le plus lourd des voiliers) : accélération 0,18 bloc/s², freinage 0,35, virage 5°/s au plus, longue
  erre (`waterDrag` 0,045), roulis 0,55 ; vitesses 1,3 / 3,2 / 5,4 ; pilote automatique : rayon 15, anticipation 30,
  sondes 80.

## 6. Passerelle d'embarquement

Système existant (`docs/PASSERELLES.md`, `core/Gangplank.java`) : spec `gangplanks/fortress_ship.json` et modèle
`gangplank_fortress_ship.bbmodel` écrits par `tools/fortress_gangplank.py` (ajoute la spec à `ships_g2.py` à l'exécution,
sans le modifier). Tribord, au milieu du passavant (z 1,6, 3 blocs de large, 9 de long, style bois sombre), charnière
en haut du pavois (6,0) sur la face extérieure, escalier du pont (4,5) à la charnière, levier sur le pont à l'arrière ;
aucun merlon ni lisse dessiné au-dessus de la planche. Paquet rangé posé à plat sur l'assise de pierre
sous la lisse (`stow_drop` 0,6, `stow_offset` 0,39, `stow_tilt` 4, mesurés par `fortress_gangplank.py compact` après
l'amincissement de l'assise en phase 4), peau de pierre grise (assombrie en phase 4) et liseré de fer (case
`fortress_ship` de l'atlas `gangplank.png`, ajoutée dans `gangplanklib.py` à une place fixe, 13).

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
  `interiors/fortress_ship.grid`, mobilier `interiors/fortress_ship_decor.json` (`tools/fortress_decor.py`, meubles
  modélisés `tools/fortress_furniture.py`). Aperçu : [preview_fortress_ship.png](preview_fortress_ship.png) ; pièces
  meublées : [interieur_fortress_ship.png](interieur_fortress_ship.png).
* Java : `FortressLayout`, `FortressShipEntity` ; tests `FortressShipTest` (forme, dimensions, pièces, escaliers, portes,
  sièges, coque fermée, embarquement, pièces meublées, modèle, animations), `FortressShipGameTest` (en jeu : mise à
  l'eau près d'un quai, vues des trois références, tous les niveaux, marche, portes, pièces meublées photographiées,
  assis puis relevé sur trois sièges, marche entre les meubles, passerelle déployée puis repliée, barre).
* Fichiers partagés modifiés (une entrée chacun) : `Ships.java`, `MedievalShips.java`, `ShipModels.java`, `en_us.json`,
  `fr_fr.json`, `NoZFightingTest`, `NewShipModelsTest` (+ `fortress_ship_reference_quads.json`), `GangplankSpecsTest`,
  `GangplankFoldTest` (taille nominale de l'ancien paquet en accordéon, que ce navire n'a jamais eu),
  `ShipClientGameTest` (un appel), `tools/gangplank/gangplanklib.py` + `textures/entity/gangplank.png` (case de
  camouflage). À la fusion des trois navires de la 1.27.0 : garder les lignes de chacun et régénérer l'atlas
  (`python3 tools/fortress_gangplank.py` réécrit l'atlas avec toutes les cases déclarées).
* Limites : les fenêtres du château ne laissent pas voir dehors (murs de la grille pleins : leur face intérieure est
  dessinée) ; pas de canons (rien de tel sur les images) ; la grue et sa caisse sont décoratives ; sans les mods de
  décoration, les meubles des mods sont remplacés par des boîtes ; armures, râteliers, écus, carte de guerre et brasero
  sont des décors (pas d'objets à prendre) ; le château de 151 (plus massif, à trois étages) n'est pas reproduit tel quel.

## 9. Passe de fidélité (phase 3)

Planche : [comparaison_fortress_ship.png](comparaison_fortress_ship.png) (référence | modèle vu de la même caméra pour 112,
151 et 149, puis la vue 112 avant / après). La caméra de 112 est recalée par moindres carrés sur des points sûrs (bec,
pommes des trois mâts, flottaison et lisse au grand mât : 13 px d'écart au plus) ; les hauteurs des voiles et des bandes
du bordé ci-dessus en sont tirées. 151 et 149 sont des variantes (château plus massif, voiles plus hautes) : leurs vues
sont cadrées à l'œil.

Corrigé, par ordre de visibilité :
* **Voilure** : les basses voiles pendaient 2 à 4 blocs trop bas et les huniers étaient presque aussi grands qu'elles. Les
  hunes montent (misaine 17,3, grand mât 20,3), les basses voiles pendent juste dessous (grande voile 19,7 → 9,4, 18,4 de
  large ; misaine 16,7 → 9,9) et de petits huniers les surmontent (≈ 2,5 × 6–8). Vergues brassées de 45° au lieu de 38°.
* **Foc** : il débordait loin devant l'étrave (amure au bout du beaupré, ≈ 40 blocs²) ; c'est maintenant une petite trinquette
  sur l'étai de misaine, en grande partie cachée par la misaine comme sur 112.
* **Tour** sur la grande voile seulement (aucune image n'en montre sur la misaine) ; chutes blanches larges, têtière rouge.
* **Bordé** : préceinte remontée sous les panneaux rouges (plus de bande brune entre eux), panneaux plus hauts, bandeau de
  pierre plus mince ; contreforts de pierre en gradins sous chaque nervure ; bordé sombre sous le gaillard d'avant.
* **Pierre** biseautée et un peu chaude (joints profonds, arêtes claires) : la coque et le château sont moins gris et plats.
* **Château** : toit de la tourelle abaissé (faîte 17,0 au lieu de 18,6) ; plus de pilastre au milieu de l'étage de la
  cabine (les trois fenêtres éclairées sur le bois sombre), encadrements de fenêtres en bois sombre, cordon sous la
  dunette dans l'ombre (pierre sombre).

Restent (par ordre de visibilité) : le tableau arrière vertical (112 montre une voûte qui rentre sous le château en
encorbellement) ; la coque et le château encore un peu plus clairs que sur 112, dont l'éclairage creuse les joints et les
dessous ; la tourelle un peu plus en arrière (z −17 au lieu de ≈ −16) ; le château massif à trois étages et les voiles
sombres déchirées de 151, les fenêtres en arc de 149 ; sur 151 / 149 les voiles sont plus hautes que sur 112 (variantes).

## 10. Passe de structure (phase 4)

Planche : [comparaison_fortress_ship.png](comparaison_fortress_ship.png) (référence | modèle vu de la même caméra pour 112,
151 et 149 ; puis phase 3 / phase 4 depuis la caméra de 112 et depuis la poupe). Caméras : celle de 112 recalée en phase 3 ;
151 et 149 recadrées à l'œil (variantes). Chaque itération mesurée aussi par la part de pixels gris / rouges / bois
sombre sur la coque (112 : 23 % de gris ; phase 3 : 60 % ; phase 4 : 47 %, le reste de l'écart venant surtout de
l'éclairage chaud et des ombres de l'image).

Changé :
* **Matériaux et couleurs** (voir § 5) : coque en bois sombre, pierre en bandes étroites, plus sombre et en blocs réguliers
  à joints sombres, nervures à plaque de fer, panneaux rouges en planches encadrées de montants cloutés (plus de
  « rideaux »), château en bois sombre (la pierre en quoins, cordons, parapets et merlons), voiles cramoisi.
* **Poupe** : la coque rentre sous le château en voûte à gradins (quoins de pierre en escalier aux angles), consoles
  sous le plancher de la cabine, l'étage de la cabine sur le tableau avec trois fenêtres en arc, le **donjon en
  encorbellement** d'un bloc (z −20,5) sur une table de consoles, deux fenêtres en arc, la grande bannière, parapet sur
  consoles ; le safran pend à la voûte. La grille suit : le toit du donjon (et ses créneaux) s'étend sur
  l'encorbellement (`fortress_interior.py` : origine z −21,5, ligne de poupe `fortress_shape.stern_z`), rien n'existe
  derrière l'étage de la cabine, la voûte est hors de l'eau du bord (l'eau y est dessinée). `FortressLayout` :
  `KNUCKLE_Y`, `KEEP_OVERHANG_Y`, `KEEP_STERN_Z`, sondes de poupe (safran z −19,3, donjon z −21,3).
* **Tourelle** avancée d'un demi-bloc (z −18,5 … −14,5, centre −16,5), grandes fenêtres éclairées ; son mobilier suit,
  le tonneau de flèches passe derrière elle ; un bloc libre devant sa porte (le test en jeu s'y tient à z −13,95).
* **Voilure** : vergues des basses voiles relevées d'un bloc sous des hunes relevées, basses voiles plus hautes (grande
  voile 20,65 → 9,0), chutes blanc-gris plus larges (≈ 1/7 chacune), grande tour centrée (≈ 1/3 de la largeur), foc
  réduit (≈ 60 %).
* **Fenêtres en arc éclairées** (149) sur le château (flancs, poupe, cloisons avant), leur intérieur dessiné sur les murs
  des pièces ; **hunes rondes en bois crénelées** (149).
* Avant : bordé clouté sous le gaillard, planches rouges contre l'étrave, grands écus à tour ; bannière du gaillard
  reculée comme sur 112.
* Gardés : grue et caisse suspendue, bannières, merlons du passavant (151 / 149), lanternes.

Restent (par ordre de visibilité) : le château massif à trois étages et les voiles sombres déchirées de 151 ; l'éclairage
chaud et les ombres profondes des images (la pierre y paraît plus contrastée) ; les voiles de 149 vues de face depuis
tribord (brassées dans l'autre sens) et plus hautes ; le passavant de 112 à balustrade de bois (merlons de 151 / 149
gardés) ; les fenêtres du donjon sombres sur 112 (éclairées ici, comme 149) ; les contreforts sous les nervures en
blocs séparés sur le bouchain (continus sur 112).

## 11. Passe visuelle (phase 5, 1.27.1)

Planche : [comparaison_fortress_ship.png](comparaison_fortress_ship.png) (référence 112 | après ; puis avant / après depuis
la caméra de 112, le flanc de près, le château, la grande voile et la poupe, rendus avec l'éclairage des entités de
Minecraft : deux lumières fixes, chaque face éclairée à plat, les flancs à environ la moitié ; enfin la même vue en jeu
avant / après, variante decor). Silhouette, pièces, sièges, passerelle, collisions et physique inchangés ; grille et mobilier identiques.

Minecraft éclaire le modèle face par face, sans ombre ni occlusion : l'ombre et la lumière des images sont donc
**peintes dans les textures** (`fortress_texture.py`, phase 5) :
* **Pierre** plus claire (les flancs ne reçoivent qu'environ la moitié de la lumière), chaque bloc biseauté (arêtes haute
  et gauche claires, basse et droite sombres sur un joint noir), marbré, piqueté, écorné, parfois fêlé, d'une teinte un
  peu chaude ou froide ; deux fois plus de blocs différents (12 normaux, 5 cloutés, 6 sombres, 4 clairs) ; une pierre
  encrassée et moussue pour les contreforts qui descendent dans l'eau.
* **Bois** : chaque planche sa teinte, arête haute claire, joint sombre, abouts cloués, nœuds ; le bordé plus sombre et
  plus vert rang par rang vers la quille (`hull_low`, `hull_deep`), mouillé à la flottaison, dans l'ombre sous la
  préceinte de pierre ; la bande cloutée haute dans l'ombre du bandeau (`studs_top`) ; bois un peu plus chaud et clair.
* **Fer** : clous bombés à reflet et ombre portée (bande cloutée, montants, pierres cloutées), plaques des nervures
  martelées et biseautées à gros bouton et rivets d'angle, coulures de rouille.
* **Panneaux rouges** plus vifs : quatre planches par bloc, clous aux abouts, usure, ombrés en haut et au pied.
* **Voiles** à 32 px par bloc (atlas des voiles 1024²) : chaque bloc de toile biseauté comme les voiles en voxels de 112,
  coutures doubles entre les laizes, bandes de ris et garcettes, ralingue torsadée tout autour, plis, pied plus sombre,
  têtière dans l'ombre de la vergue ; la tour cernée de sombre, ses assises et son biseau dessinés.
* Bannières et écus à 32 px par bloc (plis, tour cernée et appareillée, bord d'or à reflet et rivets) ; tuiles du toit
  bombées ; fenêtres à vitraux sous plomb ; dorures en bandes claire / sombre.
* Les faces alignées (pierre, panneaux, bandes cloutées) commencent à un bloc entier pris au hasard dans leur région, les
  plaques et montants sont étirés en travers : les blocs voisins ne se répètent plus et les boutons sont centrés.

**Relief** (69 cubes, 5 792 → 5 861, + 1,2 %) : un bouton de fer en saillie sur chaque plaque de nervure, un appui de
pierre en saillie sous chaque fenêtre en arc ; haubans, galhaubans, étais et bras plus épais (0,07–0,08) pour rester
lisibles de loin. Passerelle : la case de camouflage `fortress_ship` suit la pierre plus claire.

Vu en jeu (dernière ligne de la planche, variante decor du premier passage) : les bannières et écus se lisent enfin
(la tour était presque invisible), les étais sont moins pointillés (encore discontinus de loin : voir § 12), la coque et les voiles ont du grain. Les garcettes
claires et les points de couture des voiles scintillaient au loin (pas de mipmaps sur les entités) : garcettes sombres,
coutures en lignes, plus de trame fine ; l'usure claire des panneaux rouges est atténuée.

Restent : l'éclairage chaud et les ombres portées des images (impossibles sans ombres dans le jeu) ; le reste du § 10.

## 12. Passe visuelle, suite (phase 6, 1.27.1)

Planche : la même [comparaison_fortress_ship.png](comparaison_fortress_ship.png), l'« avant » étant désormais main (1.27.0)
et l'« après » les phases 5 et 6 ; dernière ligne : la vue en jeu de main et de la branche (variante decor).
Aperçu mis à jour : [preview_fortress_ship.png](preview_fortress_ship.png). Silhouette, pièces, sièges, collisions,
physique inchangés ; grille et mobilier identiques ; 5 861 cubes (aucun ajouté).

Revue des captures en jeu de la phase 5 : de loin la coque se lisait encore comme un navire de bois brun à minces
bandes grises (112 : une forteresse de pierre claire aux larges ceintures et piliers encadrant des panneaux rouges vifs),
les panneaux rouges étaient devenus des planches striées sans plus d'éclat, le bordé grésillait de points clairs et
noirs, les clous du bandeau ressemblaient à des cailloux, les clous noirs perçaient le bois à l'intérieur et les étais
restaient pointillés. Corrigé :
* **Pierre** encore plus claire (≈ + 17 %) et plus chaude (`STONE_TONES` autour de `#a89a8c`), biseau haut de 2 px
  presque blanc (≈ `#d6ccc0`), pied et flanc droit moins sombres, joint un peu moins noir ; pierre sombre et claire
  relevées d'autant. **Nervures** : la plaque de fer plus étroite (0,56 → 0,42, `RIB_PLATE_W`), la pierre claire en
  montre un quart de bloc de chaque côté : de loin la nervure se lit comme un pilier de pierre ; boutons et rivets
  dessinés pour la vraie largeur de la plaque (ronds).
* **Panneaux rouges** redessinés comme sur 112 : des blocs carrés biseautés, un par bloc, rouge vif chaud (`#c2302a`,
  ± 8 % par bloc), arête claire en haut et à gauche, sombre en bas et à droite, sans clous ; un liseré de fer en haut
  et au pied, les rangs du haut dans l'ombre du bandeau.
* **Bordé** : l'écart de teinte entre planches divisé par deux, clous brun sombre (plus de pixel presque noir ni de
  reflet), un about sur deux seulement, moins de nœuds : plus de grésillement de loin. Le bordé des fonds aussi clair
  qu'avant la phase 5 (seuls les derniers rangs vers la quille un peu plus sombres), la bande mouillée réduite à 3 px
  au pied de la virure de flottaison.
* **Clous du bandeau** : fer sombre (`#3a3a3e`) à un seul reflet, un par bloc, en quinconce d'un rang à l'autre
  (deux fois moins) ; montants des panneaux : une seule colonne de clous (deux par bloc au lieu de quatre).
* **Intérieur** : plus de têtes de clous sur les bois des ferrures, poutres et meubles (`wood_dark`, `wood_mid`,
  `wood_light`, `rail`, `dark_wood`) : étirées sur une grande face elles faisaient des trous noirs (cale, poutre de la
  cabine).
* **Étais et bras** assez épais pour rester des lignes continues en jeu de loin : étai de misaine et grand étai 0,26,
  étais de hune et d'artimon 0,20–0,22, sous-barbe 0,18, bras 0,20, écoutes, drisse et haubans de beaupré 0,12 (au lieu
  de 0,08) ; même nombre de cubes.
* Passerelle : la case de camouflage `fortress_ship` suit la pierre (`#aea091`, seule la case 13 de `gangplank.png`).

Vu en jeu (dernière ligne de la planche, variante decor, 1029a8f) : étais continus de la proue aux hunes, pierre plus
claire sur le château et les ceintures, panneaux rouges en blocs vifs, bordé sans points clairs, plus de clous noirs dans
la cale ni sur la poutre de la cabine. Les bras d'artimon (0,12) y restaient pointillés : portés à 0,20.

Restent : l'éclairage chaud et les ombres portées des images (le jeu éclaire les flancs à environ la moitié : la pierre
reste moins lumineuse que sur 112) ; le reste du § 10.

## 13. Refonte visuelle en profondeur (phase 7, 1.28.0)

Planche : [comparaison_fortress_ship.png](comparaison_fortress_ship.png) (référence 112 | en jeu avant, main 1.27.2 | rendu
après avec l'éclairage des entités de Minecraft depuis la caméra de 112 ; puis le flanc de près, le château, la grande
voile et la poupe, avant / après). Aperçu : [preview_fortress_ship.png](preview_fortress_ship.png). Caméra de 112 recalée
par moindres carrés sur les trois pommes de mât, le bec, la lisse au grand mât et les bannières (écart ≤ 50 px : 112
n'est pas une vraie perspective du modèle, sa tourelle et sa poupe diffèrent un peu). Silhouette, pièces, sièges,
portes, passerelle, collisions et physique inchangés ; grille et mobilier identiques (octets identiques) ; flottaison
inchangée. 5 769 cubes (5 861 avant : les plaques de fer et leurs boutons en moins, les lisses de fer et la seconde
assise de la ceinture en plus) ; génération déterministe.

Revue des captures en jeu de 1.27.2 : depuis le quai la coque se lisait encore comme un navire de bois brun à minces
bandes grises, le château en bois sombre manquait de contraste, les voiles étaient plates. Sur 112 la coque est une
**forteresse de pierre claire** : deux larges ceintures de pierre (à la flottaison et sous la lisse), des piliers de
pierre encadrant de grands panneaux rouges biseautés dans des cadres de fer noir à gros rivets, le bois sombre seulement
dans les fonds et sous le gaillard d'avant ; le château est en pierre claire à panneaux rouges, seul l'étage de la
cabine (trois fenêtres en arc éclairées) reste en bois sombre. Fait :
* **Bordé** (`hull_rows`, `cladding`) : la préceinte de pierre descend jusqu'à la flottaison (`WALE` 0,3–1,45, 1,15 de
  haut, en pierre cloutée), les panneaux rouges 1,45–3,45 (`RED_TOP`), la bande sombre cloutée 3,45–4,15, la ceinture
  haute 4,15–5,5 (`BELT_H` 1,12 + la lisse) en **deux assises** décalées d'un demi-bloc (`BELT_UP`, `stone_course(phase)`),
  la haute cloutée. Les **nervures** sont des piliers de pierre claire d'un bloc de large, en saillie d'un tiers de bloc,
  à clous d'argent (plus de plaque de fer noire ni de bouton). Les panneaux rouges sont **encadrés de fer** : un montant
  de fer sombre à rivets clairs de chaque côté du pilier (`POST_W` 0,42, `stud_post` redessiné) et une lisse de fer à
  rivets en haut et au pied de chaque panneau (`panel_rail`, région `iron_rail`). La ceinture de la poupe suit (la
  préceinte sur la voûte en pierre claire).
* **Château** : flancs du donjon, parapet de la dunette, cloison avant du château, front et mur de poupe du donjon en
  pierre claire (appareil aligné un bloc par face), quoins du donjon en pierre plus claire ; la cloison du gaillard
  d'avant et le garde-corps avant de la dunette en pierre aussi. L'étage de la cabine, la tourelle (bois sombre, toit
  rouge) et les fenêtres en arc restent.
* **Pierre** (`fortress_texture.py`) : base autour de `#bcae9e`, biseau haut presque blanc, joints `#2a2420` ; faces
  plus lisses (moins de marbrure, d'éclats et de fêlures) ; les **clous** sur la pierre en dômes d'argent brillants
  (`STUD`). Rouge des panneaux `#c43826`. Bande cloutée en brun moyen plus chaud.
* **Voiles** : cramoisi un ton plus profond (`RED`), chaque bloc de toile à sa propre valeur (± 7 %), biseaux plus
  marqués (haut et gauche clairs, bas et droite sombres), la têtière dans l'ombre de la vergue sur un rang et demi
  (− 38 %), le ventre qui prend la lumière (+ 12 %), blancs des chutes plus chauds ; la tour cernée inchangée.
* **Bannières** : frange d'or (ligne claire dans un bord plus sombre) ; **flammes** : la tour blanche cernée à la
  drisse. Lanternes des angles du château inchangées.
* Passerelle : la case de camouflage `fortress_ship` suit la pierre (`#bcae9e`, seule la case 13 de `gangplank.png`) ;
  le paquet rangé passe toujours au ras de la ceinture (`fortress_gangplank.py compact` : 0,43 au plus, inclinaison 4°).

Quatre itérations comparées à 112 depuis sa caméra (rendu avec les deux lumières fixes du jeu, flancs à ≈ 0,5) :
1 : bandes, piliers, cadres, château en pierre ; 2 : ceinture en deux assises, pierre plus nette, clous d'argent, voiles
ombrées ; 3 : pierre + 8 %, bande cloutée plus chaude, blancs des voiles ; 4 : voûte de poupe en pierre claire, tour sur
les flammes, frange d'or des bannières. Jugement « un joueur le trouverait-il beau ? » : matières lisibles de loin
(pierre claire, rouge vif, bois sombre), contrastes nets, plus de grésillement, pas de z-fighting (`NoZFightingTest`),
pas de trou vu de la proue, du flanc, de la poupe ni de dessus.

Restent : l'éclairage chaud et les ombres portées de 112 (le jeu éclaire les flancs à environ la moitié) ; la lisse de bois
du passavant de 112 (merlons de 151 / 149 gardés) ; la préceinte de 112 est à moitié sous l'eau (ici elle s'arrête
0,3 au-dessus de la flottaison, que la branche `water-hull` déplace) ; le reste du § 10.

## 14. Seconde passe après relecture (phase 8, 1.28.0)

Relecture des rendus de la phase 7 (éclairage des entités de Minecraft, dix caméras, recalés sur les captures en jeu de
main) : depuis le quai, le **tiers avant** de la coque (bordé sombre clouté sous le gaillard, un seul écu) et tout le
**bas de la coque** restaient une masse presque noire ; la **pierre**, crème et aux biseaux mous, se lisait en calcaire
bouffi plutôt qu'en pierre taillée gris moyen de 112 ; la **grille de fer noir** des panneaux rouges les faisait lire en
caisses ; sous la préceinte chaque pilier finissait par un **cube isolé** ; les **lanternes** étaient trop petites et
ternes. Fait (textures et constantes du générateur, silhouette inchangée) :
* **Coque** : les panneaux rouges courent sur tout le flanc (`hull_rows` : plus de bande cloutée sous le gaillard), un
  montant de chaque côté de chaque nervure (celles de 10,2 et 15,0 comprises : 28 montants) ; **quoins de pierre en
  escalier** le long de l'étrave (`stem_quoin_*`, 8 par bord, 0,78 de haut, alternativement 0,92 et 0,64 de large,
  chacun avancé avec la quête, un sur trois clouté) ; bordé des fonds en **chêne sombre lisible** (base `#5a4030`,
  arête haute des planches + 20 % (`_boards(edge)`), joints `#20160e`) ; la virure sous la préceinte à 0,72 au lieu de
  0,56 en haut, celle de la flottaison dans le même chêne.
* **Pierre** (`fortress_texture.py`) : base `#a9a39c` (gris moyen neutre-chaud), biseau haut-gauche + 21 % (`#cdc7bf`),
  bas-droite − 35 % (`#6e6862`), **joint de 2 px** (mortier `#2a2420` puis un pixel de biseau sombre), ± 8 % par bloc et
  **un bloc sur six plus sombre** (`#8e8880`, `STONE_DARKER`, aussi dans les tuiles `sb_*`), un éclat sur deux blocs ;
  pierre claire des chaperons `#c9c3bb` ; pierre sombre neutre ; clous d'argent gardés.
* **Cadres des panneaux** : montants en **noyer sombre** `#3a2c20` à clous d'argent (`stud_post`), **lisses de fer
  supprimées** (`panel_rail`, région `iron_rail` inutilisée), bord haut et bas des cellules rouges en noyer : la pierre
  et le rouge dominent le flanc.
* **Contreforts** : sous la préceinte, piles de deux ou trois blocs (`FOOT_W` 1,0 / 0,84 / 0,68, chacun posé sur la
  coque sur toute sa hauteur) jusqu'où le bouchain rentre, jamais un bloc seul (ici trois partout : 12 piles).
* **Lanternes** : corps de 0,45 à 0,6 bloc (`s` : passavant 1,5, gaillard 1,7, proue 2,0, dunette 1,7, donjon 1,8,
  poupe 1,8, fleuron de la tourelle 1,8 dans une cage élargie), verre **ambre plein feu** `#ffb640` à liseré clair de
  2 px et cœur pâle (`_lamp_glass`, propre au navire), une lanterne de plus **sous la pointe du bec** (`lantern_stem`,
  bras de fer).
* Passerelle : la case de camouflage `fortress_ship` suit la pierre (`#a9a39c`, seule la case 13 de `gangplank.png`).

5 785 cubes (5 769 : les 16 quoins et 12 blocs de contrefort en plus, les lisses de fer en moins) ; quads de référence
régénérés ; grille, mobilier, collisions, flottaison inchangés (`WATERLINE_Y` intact). Planche
[comparaison_fortress_ship.png](comparaison_fortress_ship.png) refaite : référence 112 | en jeu avant (main 1.27.2) | rendu
phase 8 depuis la caméra de 112, puis le flanc, la proue, le château et la vue de loin à l'échelle du jeu (phase 7 /
phase 8) ; aperçu [preview_fortress_ship.png](preview_fortress_ship.png) refait.

Restent : l'éclairage chaud et les ombres portées de 112 (le jeu éclaire les flancs à environ la moitié : la pierre y
paraît plus sombre que sur l'image) ; la préceinte de 112 à moitié sous l'eau (branche `water-hull`) ; le reste du § 10.
