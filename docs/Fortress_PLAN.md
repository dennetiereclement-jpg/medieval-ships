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
| Bordé (relevé avec la caméra recalée de la phase 3) | lisse de pierre 730–755, bande sombre cloutée 755–785, panneaux rouges 785–850, préceinte de pierre 850–872, bois sombre jusqu'à la quille (970), nervures descendant en gradins dessous | bandeau de pierre clouté (4,5–5,3) et sa lisse, bande sombre cloutée (3,55–4,5), panneaux rouges entre les nervures (1,45–3,55), préceinte de pierre juste dessous (0,75–1,45), bois sombre dessous avec les contreforts de pierre des nervures en gradins ; bordé sombre sans panneaux rouges sous le gaillard d'avant |
| Nervures de pierre | colonnes verticales tous les ≈ 180 px, flanquées de plaques de fer cloutées | 8 nervures par bord (z −19 … 15, tous les ≈ 5 blocs), plaques de fer de chaque côté |
| Château arrière | parapet crénelé y 500–540 (x 1180–1460), étage bas à fenêtres éclairées y 650–720, tourelle x 1230–1400 y 380–500, toit rouge pyramidal 300–400, épi + lanterne y 260–330 | dunette 8,0 sur la cabine du capitaine (4,5), donjon jusqu'au toit-terrasse 11,0 (parapet 12,0 + merlons), tourelle 11,0–14,5, toit rouge bas en gradins jusqu'à 17,0 (relevé : avant-toit 15,2, faîte 16,9), épi et lanterne jusqu'à ≈ 19,4 |
| Mâts | misaine x ≈ 500, grand mât x ≈ 800, artimon x ≈ 1140 ; pommes y ≈ 150 / 95 / 95 | misaine z = 8 (sur le gaillard), grand mât z = −1, artimon z = −11,5 (sur la dunette, devant le donjon) ; têtes 24 / 27,5 / 24,5 ; hunes 17,3 / 20,3 / 20,4 (sous les huniers, au-dessus des basses voiles) |
| Voiles (caméra recalée) | misaine : basse voile (vergue 16,9 → bordure 9,9) + petit hunier (18,0–20,5) ; grand mât : grande basse voile à la tour (20,3 → 9,3) + petit hunier (20,8–24,1) ; artimon : une voile (19,3 → 13,0) ; la tour de la grande voile réduite aux 3/4 de sa largeur (vergues brassées ≈ 45°) | basses voiles rouges à larges chutes blanches, têtière rouge aux coins blancs ; tour crénelée beige à porte sur la grande basse voile seulement (comme sur les trois images) ; petits huniers encadrés de blanc ; voile d'artimon rayée ; bas des voiles en escalier, usé |
| Foc | petit triangle blanc à bande rouge devant la misaine, amure au-dessus de l'étrave (≈ z 18, y 10,3) | un foc (trinquette) blanc à bande rouge sur l'étai de misaine, amure au-dessus de l'étrave, point d'écoute au-dessus du gaillard |
| Flammes | rouges, longues, à queue d'aronde en escalier, en tête de chaque mât | trois flammes rouges (4,0 / 5,2 / 4,4 de long) |
| Hunes | caisses grises crénelées | hunes carrées à parapet de pierre et merlons |
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
  hauteur), arrière large à tableau (9 blocs) ; murs du château et pavois verticaux au-dessus de la lisse.
* Beaupré de (0, 8,4, 19,5) à (0, 11,6, 28,0) ; vergues brassées de 45° (côté bâbord vers l'arrière) : les voiles
  montrent leur face sur les vues de flanc comme sur les images (la tour de la grande voile y paraît aux 3/4 de sa largeur).

## 3. Niveaux et pièces

| Niveau | y | Contenu |
|---|---|---|
| Tourelle | 11,0 | sur le toit du donjon (z −19 … −15), porte vers l'avant, fenêtres éclairées ; poste de vigie (table, longue-vue, coffre à pavillons) |
| Toit du donjon | 11,0 | terrasse crénelée autour de la tourelle ; trappe de l'escalier du donjon (bâbord) ; râtelier de lances, tonneau de flèches, brasero |
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

* **Matériaux** : bordé de bois brun sombre ; pierre grise un peu chaude en blocs biseautés (16 px par bloc, arête haute
  claire, bas et côté droit dans l'ombre, joints profonds, clous de fer) pour
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
  du beaupré, au bec, au safran, au parapet arrière et aux bouts de vergues ; ≈ 4 300 cubes.
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
