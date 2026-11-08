# Passerelles d'embarquement (1.23.0, pliage en accordéon 1.23.1)

Chaque navire et chaque grand dirigeable porte une **passerelle d'embarquement** médiévale : une planche de bois
renforcée (planches, taquets antidérapants, longerons, ferrures latérales, charnières visibles, petites rambardes,
bout biseauté qui se pose sur le quai), **pliée en accordéon** contre le flanc quand elle est rangée, et un
**levier** sur le pont qui la déploie et la replie. Les chaînes (ou cordages) de soutien suivent le bout de la
planche.

## Pliage en accordéon (1.23.1)

* La planche est faite de **segments** d'au plus 1,6 bloc (`ceil(longueur / 1,6)` segments, au moins 2 ; champ `segments`
  pour en imposer un autre nombre), reliés par des **charnières** visibles sur les côtés (plaques et nœuds de fer
  autour de l'axe de pliage). Chaque segment porte ses propres petits poteaux et sa rambarde.
* **Rangée**, elle est pliée en zigzag en un **paquet compact suspendu contre l'extérieur du flanc**, juste sous la
  charnière (le haut du bastingage) : le segment 0 pend de la charnière, le segment 1 remonte contre lui, etc. Le
  paquet fait la hauteur d'un segment et `n` épaisseurs de planche (0,4 bloc chacune : 1,2 bloc pour 3 segments, 2,8
  pour les 7 de la frégate bleue) ; rien ne dépasse au-dessus du bastingage. Les joints impairs plient les faces de
  marche l'une contre l'autre (axe 0,135 au-dessus de la face de marche), les joints pairs les dessous (axe 0,27
  dessous) : les couches s'empilent sans se croiser. Les poteaux des rambardes se rabattent à plat, vers l'intérieur,
  sur leur segment.
* Le paquet ne touche jamais la coque : sa face intérieure est à 0,06 bloc au-delà de la face extérieure de la coque
  (forme de coque du navire, `HullShape`) ou des ferrures du modèle sous la charnière (préceintes, sabords, porte-
  haubans : `stow_offset`, mesuré sur le modèle par `tools/gangplank/ships_g2.py stow`), selon ce qui dépasse le plus.
* **Déploiement** (mêmes 3 secondes, même levier, mêmes sons, mêmes règles) : petit déverrouillage, le paquet se
  soulève et pivote vers l'extérieur et le haut (20° au-dessus de l'horizontale, ou de la pente visée si elle monte),
  se déplie segment par segment (le joint le plus proche du bord d'abord), puis la planche droite descend sur le quai
  (petit rebond) ; les rambardes se redressent à la fin. Déployée, c'est exactement la planche d'une seule pièce de
  1.23.0 (mêmes points, mêmes boîtes de collision, même angle). **Repli** : l'inverse.
* Le balayage vérifié au clic (« Un bloc gêne le déploiement ») reste celui de 1.23.0 (de la verticale à la pente
  visée) : les règles ne changent pas.
* Rendu : un os par segment (`seg_<k>`, origine à son bout intérieur) et deux par rambarde (`rail_<k>_0`, `rail_<k>_1`)
  dans `gangplank_<id>.bbmodel` ; chaque segment est placé par sa pose de pliage (angles cumulés des charnières), sans
  allocation par image ; la pose rangée est calculée une fois par navire.

## Utilisation

* **Clic droit sur le levier** (sur le pont, près de la passerelle ; la bulle d'aide indique « Clic droit : déployer
  la passerelle ») : la passerelle se déverrouille, pivote sur ses charnières, descend progressivement et vient se
  poser sur le quai ou le ponton (3 secondes, mouvement amorti, petit rebond à l'arrivée). Le levier bascule ; bruit
  de levier, de bois et de chaîne au départ, choc du bois à l'arrivée.
* **Deuxième clic** : elle remonte et se verrouille contre la coque (bruit de verrou à la fin).
* **On marche dessus** : depuis le quai on monte la pente jusqu'au pont, puis on descend l'escalier intérieur — et
  l'inverse — sans sauter ni être téléporté. La pente est découpée en petites marches invisibles (au plus 0,25 bloc
  chacune), l'escalier intérieur en marches de 0,45 bloc au plus.
* Rangée, la passerelle pliée suit le navire normalement (elle ne gêne rien et ne heurte rien).

## Règles de sécurité (côté serveur)

Déploiement refusé (message rouge dans la barre d'action) si :

| Situation | Message |
| --- | --- |
| le navire avance encore (plus de ~1 bloc/s) | « Le navire doit être à l'arrêt pour déployer la passerelle. » |
| le Nautilus est en plongée | « Faites d'abord surface pour déployer la passerelle. » |
| le pilote automatique fait route | « Le pilote automatique fait route : impossible de déployer la passerelle. » |
| rien de solide au bout (eau, vide sous un dirigeable) | « Aucun quai ni ponton à portée : la passerelle ne peut pas être déployée dans le vide. » |
| le quai est trop bas (pente > maximum, ou chute > `max_drop`) | « Le quai est trop bas pour la passerelle (pente trop forte). » |
| le quai est trop haut | « Le quai est trop haut pour la passerelle. » |
| l'appui trouvé ne tient pas au bout de la planche | « Pas d'appui stable au bout de la passerelle. » |
| un bloc dans l'arc que balaie la planche | « Un bloc gêne le déploiement de la passerelle. » |
| un bloc au-dessus du passage (on s'y cognerait) | « Un bloc encombre la passerelle : le passage serait bouché. » |
| une créature, un joueur ou un véhicule sur le chemin | « Quelqu'un (ou quelque chose) se trouve sur le chemin de la passerelle. » |

Repli refusé tant que quelqu'un (joueur, créature, véhicule) se tient sur la planche ou sur l'escalier :
« Impossible de replier la passerelle : quelqu'un est dessus. » Pendant un mouvement : « La passerelle est en
mouvement. »

**Passerelle sortie = navire amarré** : le navire est tenu exactement sur place (ni poussée, ni dérive, ni
descente pour un dirigeable). Les commandes du pilote sont ignorées avec le message **« Repliez d'abord la
passerelle »**. Le roulis et le flottement dessinés s'arrêtent (la planche reste posée sur le quai).

**Pilote automatique** : à une escale, il compte son temps d'arrêt normalement, passerelle sortie. Quand il doit
repartir, il replie lui-même la passerelle si personne n'est dessus, sinon il attend (« Départ retardé : quelqu'un est
sur la passerelle. ») et repart une fois la passerelle rangée. Une route lancée passerelle sortie fait de même.

**Recherche d'appui** : au clic seulement (jamais à chaque tick) : colonnes au bout de la planche (centre et deux
coins), surface supérieure solide la plus haute dans la plage autorisée, angle calculé pour que le bout se pose
dessus, puis nouvelle recherche à la nouvelle portée jusqu'à stabilisation. Aucun chargement de tronçon : une colonne
non chargée n'a pas d'appui (et compte comme pleine pour le balayage).

## Multijoueur, sauvegarde

* Le serveur décide de tout. Seuls les **changements** sont synchronisés (données suivies de l'entité : état
  RANGÉE/DÉPLOIEMENT/DÉPLOYÉE/REPLI, tick de départ du mouvement, angle final) ; chaque client calcule l'animation à
  partir de ces trois valeurs et de l'heure du monde.
* Les **collisions** (marches de la pente, escalier, ouverture du bastingage) sont calculées une fois par
  déploiement, en coordonnées du monde (le navire est tenu sur place), à l'identique sur le serveur (créatures) et
  sur chaque client (le joueur local, simulé par son client). Aucune collision pendant le mouvement ni passerelle
  rangée. Le contrôle anti-vol du serveur ne compte pas un joueur debout sur une passerelle déployée.
* **Sauvegarde** : l'état et l'angle sont enregistrés avec le navire. Au rechargement, une passerelle en cours de
  déploiement est considérée déployée, une passerelle en cours de repli rangée ; une passerelle déployée est
  re-vérifiée au premier tick (dès que le tronçon du bout est chargé) : si son quai a disparu, elle se replie.
* Rien ne tourne quand la passerelle est rangée ; pendant un mouvement, seule la minuterie ; déployée, le maintien
  sur place.

## Navires équipés

Fichier par navire : `assets/medievalships/gangplanks/<id>.json` (repère local du navire : +x bâbord, y vers le
haut, +z vers la proue, voir l'en-tête de `core/Gangplank.java`), modèle pliant `models/entity/gangplank_<id>.bbmodel`,
levier `models/entity/gangplank_lever_<style>.bbmodel`, atlas commun `textures/entity/gangplank.png`, tous générés
par `tools/gangplank/gangplanklib.py`.

| Navire | Côté | Largeur × longueur | Style | Remarques |
| --- | --- | --- | --- | --- |
| `galley` (galère) | tribord | 2,0 × 3,5 | bois clair | charnière à 1,63, angles -25.0°…25.0°, chute 1,47 max |
| `galleon` (galion) | tribord | 2,0 × 5,5 | bois sombre ferré | charnière à 2,22, angles -20.0°…38.0°, chute 3,38 max |
| `warship` (navire de guerre) | tribord | 2,4 × 9,0 | bois sombre ferré | charnière à 5,83, angles -15.0°…42.0°, chute 6,02 max |
| `medieval_galley` (galère médiévale) | tribord | 2,0 × 4,0 | bois clair | charnière à 2,15, angles -25.0°…30.0°, chute 1,99 max |
| `steam_paddleboat` (bateau à vapeur) | tribord | 2,0 × 5,5 | acier | charnière à 3,37, angles -20.0°…40.0°, chute 3,53 max |
| `elven_sailboat` (voilier elfique) | tribord | 2,2 × 4,0 | bois elfique | charnière à 1,94, angles -25.0°…35.0°, chute 2,29 max |
| `old_corsair` (corsaire) | tribord | 3,0 × 8,0 | bois usé | charnière à 6,0, angles -15.0°…42.0°, chute 5,35 max |
| `blue_frigate` (frégate bleue) | tribord | 3,0 × 10,0 | bois sombre ferré | charnière à 7,55, angles -15.0°…42.0°, chute 6,69 max |
| `steampunk_airship` (dirigeable steampunk) | tribord | 3,0 × 4,5 | cuivre, chaînes | charnière à 1,35, angles -20°…30°, chute 2,0 max |
| `crystal_airship` (dirigeable de cristal) | tribord | 3,5 × 5,5 | cristal | charnière à 1,13, angles -25.0°…45.0°, chute 3,88 max |
| `sky_leviathan` (Léviathan des cieux) | tribord | 3,0 × 5,5 | bois sombre ferré | charnière à 1,14, angles -25.0°…45.0°, chute 3,88 max |
| `dragon_junk` (jonque du dragon) | tribord | 3,0 × 5,5 | jade | charnière à 1,14, angles -25.0°…45.0°, chute 3,88 max |

**Non équipés** (volontairement) :

* `rowboat` (barque) et `trade_sloop` (petit sloop marchand) : petits bateaux, pas de passerelle (demande du joueur) ;
* `nautilus` : pas de passerelle (demande du joueur) ;
* `hot_air_balloon` (montgolfière) : une nacelle, on y monte d'un clic ;
* `rustic_skiff` : petit volant qui a déjà son propre escalier d'embarquement le long du bordé.

## Format d'un fichier de passerelle

```json
{
 "side": "starboard",              // côté de la coque ("port" = bâbord, "starboard" = tribord)
 "hinge": [-2.07, 2.38, 2.85],     // milieu de la ligne de charnière, à la hauteur où l'on marche
 "width": 1.8, "length": 4.0,      // blocs
 "style": "wood",                  // wood, dark_wood, worn, elven, copper, crystal, jade, steel
 "lever": [-1.0, 0.6, 1.45],       // pied du levier, sur le pont
 "lever_yaw": 0,                   // facultatif (défaut : tourné vers l'intérieur)
 "step": [-1.85, 0.6, 1.95, -0.65, 2.38, 3.75],  // boîte d'escalier intérieure (solide passerelle déployée)
 "rail_gap": [1.9, 3.8],           // portion du bastingage sans collision au-dessus de la charnière (déployée)
 "angles": [-15, 35],              // pentes permises, positif vers le bas
 "max_drop": 2.6,                  // plus grande hauteur charnière -> appui
 "chain_anchor": null,             // point fixe des chaînes (null : deux petits poteaux à la charnière)
 "segments": 4,                    // facultatif : nombre de segments pliants (défaut ceil(longueur / 1,6), au moins 2)
 "stow_offset": 0.2                // facultatif : écart mini charnière -> face intérieure du paquet rangé (ferrures)
}
```

La boîte `step` devient un escalier qui monte vers le bordé : n marches de 0,45 au plus, du bas de la boîte (le pont)
jusqu'à son haut (la hauteur de la charnière). `stowed_angle` (facultatif, défaut −90) n'est plus la position
rangée (la planche est pliée) : c'est le début du balayage vérifié au déploiement (règles de 1.23.0).

## Limites

* Le paquet rangé fait `n` × 0,4 bloc d'épaisseur (2,8 blocs sur la frégate bleue, 7 segments) : bien moins visible
  qu'une planche de 10 blocs dressée, mais c'est un vrai paquet de planches.
* Galère : deux de ses avirons passent dans la largeur de la passerelle ; ils traversent le paquet rangé (ils passent
  déjà sous la planche déployée et dans son escalier). Galère médiévale : 4 segments au lieu de 3 pour que le paquet
  reste au-dessus des sabords de nage.
* Pendant le mouvement (3 s), le paquet qui se déplie peut traverser un bloc voisin (un quai très haut collé à la
  coque) : seul le balayage de 1.23.0 est vérifié, et aucune collision n'existe pendant le mouvement.

* Les collisions ne suivent pas le roulis dessiné (il est coupé quand la passerelle est sortie).
* Les rambardes de la planche sont décoratives (on peut tomber par le côté).
* Si le quai est détruit pendant que la passerelle est déployée, elle reste en place jusqu'au prochain clic ou au
  prochain chargement (pas de surveillance à chaque tick, par choix).
* L'horloge du client peut avoir quelques ticks d'écart avec celle du serveur : l'animation peut commencer un
  instant plus tôt ou plus tard ; l'état final et les collisions viennent toujours du serveur.

## Tests

* JUnit `GangplankFoldTest` (1.23.1) : nombre de segments et os du modèle ; pour chaque navire équipé, chaque
  segment et chaque rambarde rabattue du paquet rangé (sommets du vrai modèle) sous la charnière, hors de la forme de
  coque, hors des solides du navire et au-delà des ferrures mesurées ; couches empilées sans se croiser ; charnières
  jamais disjointes et mouvement continu du paquet à la planche droite ; déployée = planche de 1.23.0 (mêmes sommets,
  mêmes boîtes de collision) ; champs `segments` et `stow_offset`.
* JUnit `GangplankTest` : repère et formule de rotation (identique à la transformation du rendu), animation
  (début, fin, sens du pivot, levier), marches de la pente franchissables dans les deux sens (montée ≤ 0,25, sans
  trou, sur la pente), escalier (marches ≤ 0,45 jusqu'à la charnière), recherche d'appui sur un monde factice (quai
  à plusieurs hauteurs, vide, trop bas, trop haut, trop loin, `max_drop` d'un dirigeable), balayage et passage
  obstrués, levier, chargement de tous les fichiers `gangplanks/*.json` et de leurs modèles, navires de référence
  (charnière sur le bordé, escalier depuis le pont, levier sur le pont, rien de solide sur le chemin).
* Jeu réel `GangplankGameTest` (appelé par `ShipClientGameTest`, en solo **et** sur serveur dédié) : quai de pierre
  et bassin construits par commandes ; levier visé et cliqué pour de vrai → DÉPLOIEMENT → DÉPLOYÉE ~3 s plus tard,
  boîtes enregistrées sur le client ; un joueur en survie marche du quai jusqu'au pont (touche avancer seulement) et
  revient ; repli refusé tant qu'il est dessus, accepté ensuite ; commandes du pilote ignorées (la galère ne bouge
  pas) ; déploiement refusé avec un bloc dans l'arc ; aller-retour NBT cohérent ; rechargement après la disparition
  du quai → repli ; dirigeable : refus en plein ciel, déploiement à côté d'un ponton, marche du ponton au pont ;
  (1.23.1) point le plus haut du paquet rangé (modèle chargé par le client) sous la charnière. Captures :
  `passerelle_*` (dont `passerelle_0b_paquet_replie`).
