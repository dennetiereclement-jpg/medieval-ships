# Montgolfière steampunk (`hot_air_balloon`) — analyse, plan et guide du joueur

Image de référence : `scratchpad/ref/hot_air_balloon_ref.png` (une seule vue, trois-quarts avant bâbord, légèrement
en contre-plongée). Un gros ballon rond à fuseaux vert olive et beige, une nacelle-barque de bois sombre suspendue
par des chaînes dorées, un brûleur central, une petite machinerie de cuivre, une grande roue dentée de bois sur le
flanc, des lanternes suspendues. Vieux look steampunk fait main.

Comparaison image / rendu du modèle (même point de vue, côté, avant, nacelle) :
[`preview_hot_air_balloon.png`](preview_hot_air_balloon.png).

## 1. Mesures sur l'image (768 × 512 px)

Segmentation ciel / objet par couleur. Échelle retenue : **largeur du ballon = 13,4 blocs** (23,9 px par bloc).

| Élément | Pixels | Blocs (modèle) |
|---|---|---|
| Ballon, largeur maximale (x 196 → 518, lignes 110–150) | 322 | **13,4** (R = 6,7) |
| Ballon, sommet → bouche (y 12 → 300) | 288 | hauteur de l'enveloppe **14,4** (bouche y +5,0 → sommet +19,4), soit 1,07 × la largeur : « légèrement plus haut que large » |
| Bande de charge en laiton (y ≈ 175) | 0,43 de la hauteur depuis la bouche | f = **0,40** (y +10,8) |
| Bouche (largeur à y 300) | ≈ 150 | rayon **2,35** (0,35 R), collier de laiton |
| Fuseaux visibles sur la moitié avant | 7–8 bandes | **20 fuseaux** alternés (18° chacun) |
| Bouche → lisse de la nacelle (y 300 → 400) | 100 | **4,0** (colonne du brûleur, anneau de charge) |
| Nacelle, longueur (x 240 → 495) | 255 | **10,2** hors tout (coque 9,2), 0,76 × le ballon |
| Nacelle, hauteur (y 400 → 490) | 90 | lisse à +1,0 (+1,4 aux extrémités), quille à −1,3 |
| Roue dentée (diamètre ≈ 75 px) | 3,1 | rayon **1,4** (dents comprises 1,6), centre à y +2,3, à bâbord de l'arrière |
| Cheminée (sommet y ≈ 300) | | **+3,9** au-dessus du pont, chaudière ronde noire |
| Lanternes sous les extrémités | | 4, pendues sous les bras de la lisse, fond à y ≈ −0,8 |

Proportions : 13,4 de large, **21 de haut** (quille → fleuron de la couronne), nacelle 10,2 × 3,7. Beaucoup plus
petit que le dirigeable steampunk (22 × 18), c'est le plus léger des aéronefs du mod.

## 2. Structure, matériaux, éléments mobiles

* **Enveloppe** : corps de révolution autour de l'axe vertical (profil Catmull-Rom dans `balloon_shape.py` /
  `BalloonLayout`), **20 fuseaux** de toile cousue, vert olive et beige alternés, en panneaux inclinés entre 16 anneaux
  (serrés à la bouche et à la couronne : pas d'escalier). Couronne : plaque et dôme de laiton, anneau d'or, fleuron
  (la soupape). Bouche : collier de laiton, perle d'or. **Bande de charge** riveté de laiton à 40 % de la hauteur,
  bossages d'or entre les fuseaux, huit manilles d'or ornées.
* **Suspension** : huit **chaînes d'or** descendent la jupe depuis les manilles jusqu'à l'anneau de charge (laiton,
  sous la bouche), puis de l'anneau aux cabillots de la lisse (proue, flancs, poupe). L'anneau est porté par quatre
  jambes de laiton depuis la tête du brûleur.
* **Nacelle** : petite coque de barque, bordé de planches **teintées vert sombre**, fond de bois sombre, **lisses
  (rims)** de bois verni sombre : préceinte à la ligne du pont, cap de plat-bord plat et main courante ronde, lisse de
  laiton, perle d'or ; **six fenêtres éclairées** à cadre de laiton par bord ; étrave et étambot à boule d'or ; pont de
  planches ; deux bancs de cuir capitonné le long des bords et un banc de proue ; sacs de lest et glène de corde.
* **Colonne du brûleur** (cuivre et laiton) au milieu : quatre poteaux, croix de fer, **plate-forme** carrée à
  mi-hauteur avec sa balustrade, lanterne en applique, tête du brûleur (tambour de laiton, quatre gicleurs, bouche
  ardente) et sa **flamme** (deux langues croisées en texture lumineuse) qui monte dans la bouche.
* **Machinerie** : chaudière noire rivetée sur sa selle, dôme de fer, porte de foyer rougeoyante, cadran, sifflet,
  soupape à volant, **cheminée** à collier de laiton, bouche évasée et chapeau de pluie ; tuyau de cuivre jusqu'au
  brûleur avec son robinet ; serpentin de cuivre.
* **Roue dentée** de bois (jante de chêne cerclée de fer, 16 dents, huit rayons, moyeu de laiton) sur son essieu et sa
  chape de fer au flanc bâbord de l'arrière, un pignon de laiton au-dessus, carter d'engrenage et bielle à bord.
* **Lanternes** suspendues à des bras de fer sous les quatre coins de la lisse.

Animations (os du modèle) : `helm_wheel` (`steer`, le volant des vannes), `burner_flame` + `burner_core`
(`elevator` : la flamme **grossit en montée**, rapetisse en descente ; `flag_wave` : son vacillement permanent),
`side_wheel` + `pinion` (`engine` : tournent avec la vitesse), `lantern_*` (`lantern_sway`). Le modèle entier
ondule doucement (`sway` 1,6) et flotte de haut en bas (`hover` 0,1).

Taille du modèle : **2 536 cubes** (enveloppe 300 panneaux, chaînes ≈ 300 maillons), une texture 256 × 256.

## 3. Places et commandes

* **Pilote** debout aux vannes du brûleur, derrière la colonne (z −2,1), face à la proue ; prise des commandes en
  cliquant le poste de laiton (volant) devant lui.
* **Trois passagers** : deux bancs latéraux (z +1,9), un banc de proue (z +3,5). Un cinquième joueur est refusé.
* Vol : avancer / reculer / tourner comme les autres navires ; **saut = monter**, **sprint = descendre** ; l'altitude se
  tient seule (pas de gravité). Config `hot_air_balloon` dans `config/medievalships.json` : vitesses 1,2 / 2,6 / 4,0,
  accélération 0,3, virage 9°/s ; `flight` : montée 1,2, descente 1,0, accélération verticale 0,35 (décollage
  progressif, atterrissage en douceur : la simulation unitaire vérifie qu'il se pose sans s'enfoncer), dégagement
  autopilote 6, `sway` 1,6, inclinaison 3°.
* Pose : avec l'objet, en l'air au-dessus du point visé (la place est vérifiée pour le ballon entier : collines, arbres,
  bâtiments, autres coques) ; `/ship give hot_air_balloon`, `/ship spawn hot_air_balloon`.
* Autopilote : les routes aériennes du dirigeable (`/ship route ...` avec des points d'altitude, voir
  `COMMANDES.md`) ; il monte par-dessus les obstacles avec son dégagement et redescend aux arrêts.
* Ambiance (client, sons vanilla uniquement) : veilleuse du brûleur (crépitement), **rugissement du brûleur et
  flammes** en montée, fumée de la cheminée en route, vent dans le gréement à vitesse, cliquetis des chaînes et
  craquements de la nacelle dans le balancement.

## 4. Contraintes et limites

* Le ballon est solide (tranches de collision d'un bloc) : on ne le traverse pas, le clic dessus ramasse / monte.
* Pas d'intérieur ni de grille : la nacelle est un pont ouvert (volume de transport comme les autres barques).
* La roue dentée dépasse de 2 blocs à bâbord : sondes de terrain dédiées, elle compte dans la vérification de place.
* Une seule vue de référence : les faces non visibles (tribord, dessus, dessous) sont extrapolées symétriques.
