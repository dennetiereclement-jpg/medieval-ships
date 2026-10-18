# Nautilus — analyse et plan technique (phases 1 et 2)

Ce document répond aux phases 1 (analyse) et 2 (architecture) du cahier des charges « Projet
Nautilus ». La modélisation ne commence qu'après validation des points de la section 6.

## 1. Ce que le mod sait déjà faire (réutilisé tel quel)

| Besoin du Nautilus | Déjà dans Medieval Ships | Adaptation nécessaire |
|---|---|---|
| Item, placement au clic droit, `/ship give`, `/ship spawn`, `/ship remove` | `ShipItem`, `ShipPlacement`, `ShipCommands` (7 véhicules) | contrôle de profondeur, de longueur et de largeur d'eau |
| Marche libre sur un véhicule en mouvement | `EntityCollisionMixin` : le pont et les cloisons sont des boîtes solides qui suivent le navire ; le joueur est transporté (client et serveur), compatible Lithium, filet de sécurité | beaucoup plus de boîtes (2 niveaux, cloisons, plafonds) : regroupement par salle, seules les boîtes proches du joueur sont calculées |
| Pièces intérieures avec cloisons et portes | grande cabine du galion et du vaisseau, dunette, escaliers en marches de 0,5 bloc | portes **mobiles** (boîte retirée quand la porte est ouverte), escalier en colimaçon, échelles |
| Sièges, passagers, pilote | sièges indexés, siège 0 = pilote, `Seat.dismount` | ~24 sièges (salon, salle à manger, bibliothèque, timonerie) |
| Physique, inertie, virages larges | `ShipPhysics` (accélération, freinage, traînée, rayon de giration) | réglages « grand bâtiment » |
| Mouvement vertical, altitude tenue, plafond | `Flight` du dirigeable (vitesse verticale avec inertie, maintien, collisions verticales) | devient une **plongée** : plafond = surface, plancher = fond marin + marge |
| Pilote automatique 3D (x, y, z, cap, vitesse, attente) | `Autopilot` + `Flight.autopilot`, itinéraires `air` | itinéraires `submarine` : surface / plongée / profondeur de croisière, évitement du relief |
| Sauvegarde, rechargement, tickets de chunks | `PersistentState` + NBT de l'entité | état des portes, volets, sas, projecteurs, canot |
| Animations (hélice signée, gouvernail) | lecteur `.bbmodel` maison (os, rotations, boucles) | moteur, pistons, engrenages, portes, volets |
| Éclairage « plein feu » des lanternes | éléments `glow*` dessinés en pleine luminosité | lumières intérieures et projecteurs |

## 2. Inventaire des mods de décoration (reçus le 18/10)

| Mod | Version | Licence | Blocs | Utile pour le Nautilus |
|---|---|---|---|---|
| Farmhouse Decorations (`farmhouse_decorations`) | 26.4.0 | tous droits réservés | 68 | **le plus proche du style victorien** : piano, gramophone, canapé capitonné rouge (gauche/milieu/droite), fauteuil à bascule, chaise de salle à manger, table de salle à manger, table basse ronde, grand bureau à sous-main vert, machine à écrire, grande bibliothèque, pile de livres, lit double et lit simple en bois sculpté, commode, table de nuit, armoire, cabinet à liqueurs, lampadaire, lanterne à pétrole (suspendue ou posée), lampe, tapis rond 3×3 et 1×3, horloge à coucou, radiateur, cuisine (four ancien, plan de travail, évier, placards, étagère à épices), vasque de salle de bain, miroirs, verres et bouteilles de vin |
| Furnish (`furnish`) | 31 | tous droits réservés | 341 | **vitrines** (16 couleurs, pour les coquillages, coraux et perles du salon), rideaux (rouge), assiettes anglaises et chinoises, cadres, piles de livres, échiquier, casiers métalliques, étagères ; tables, chaises et armoires plus cubiques (moins adaptées) |
| Farmer's Delight (`farmersdelight`) | 1.21.11-3.6.16 | MIT | 133 | cuisine : fourneau en briques, marmite, poêle, planche à découper, placards |
| Lands of Icaria (`landsoficaria`) | 1.0.2 | GPL-3.0 / CC-BY-NC-SA | 657 | jarres, tonneaux, barreaux et chaînes en acier (salle des machines, réserves) |
| Mebahel Dwarven (`mebahelcreaturesdwarven`) | 1.3.3 | tous droits réservés | 5 | tuyaux et engrenages en métal doré (salle des machines) ; ce mod dépend de GeckoLib (déjà sur ton serveur), le Nautilus n'en dépend pas |

Aperçus rendus depuis les fichiers des mods : `docs/nautilus_meubles_mods.png`.

### Comment ces meubles seront utilisés

* Un bloc ne peut pas être posé dans une entité qui bouge. Le Nautilus **dessine le modèle du bloc**
  (celui du mod installé, lu à l'exécution) à sa place dans la pièce, avec le Nautilus : rien n'est
  copié ni redistribué, les licences sont respectées.
* Dépendances **optionnelles** : si un mod manque sur un client, le meuble est remplacé par un modèle
  de secours du Nautilus (le jeu ne plante pas, le sous-marin reste utilisable).
* Les collisions et les interactions (s'asseoir sur une chaise ou un canapé, allumer une lampe)
  sont gérées par le Nautilus lui-même : celles des mods sont prévues pour des blocs posés dans le
  monde et ne fonctionnent pas dans un véhicule.
* Ce qui n'existe dans aucun mod sera modélisé : **orgue monumental**, lustres, globe terrestre,
  baies vitrées et leurs volets, machines (batteries, moteur, pistons), scaphandres, instruments
  de Nemo, timonerie, projecteur, portes étanches.

## 3. Contradiction entre les dimensions demandées et l'image

Mesures sur la planche Minecraft (vue de côté et vue du dessus) :

| Rapport | Image | Tableau du cahier des charges (110 × 13 × 13) |
|---|---|---|
| longueur / hauteur de coque | ≈ 5,5 | 8,5 |
| longueur / hauteur avec timonerie | ≈ 4 | 6,5 |
| longueur / largeur | ≈ 7 | 8,5 |

Avec 110 × 13 × 13, le Nautilus serait **beaucoup plus effilé** que sur l'image (une aiguille).
Pour respecter la silhouette, il faut changer l'un des deux :

* **A — garder 110 blocs de long** : coque 16 de large, 20 de haut, ~27 avec la timonerie.
  Place pour 2 grands niveaux et un double fond, salon de 6–7 de haut ; véhicule très lourd.
* **B — garder 13 de haut** : ~72 de long, 10–11 de large. Les pièces deviennent étroites
  (salon ≈ 5 de large) : difficile à aménager comme demandé.
* **C (ma recommandation) — 96 × 14 × 17**, timonerie à 23 : proportions de l'image, toutes les
  pièces aux dimensions demandées ou plus, deux niveaux de 4,5 blocs sous plafond, double fond.

## 4. Le problème de l'eau à l'intérieur (le plus important techniquement)

Un véhicule est une **entité** : il ne déplace pas l'eau du monde. Sous la surface, l'intérieur
du Nautilus est rempli par les blocs d'eau du monde, donc un joueur à l'intérieur nagerait et se
noierait. On ne peut pas y poser de blocs d'air : ils détruiraient l'océan sur le passage.

Solution prévue, sans toucher aux blocs du monde :

* chaque compartiment étanche est une **zone sèche** connue du serveur et du client (boîtes en
  coordonnées du Nautilus) ;
* un joueur dans une zone sèche est traité comme hors de l'eau : il marche, ne nage pas, ne
  perd pas d'air, ni écran bleu, ni brouillard aquatique, ni son sous-marin ;
* le sas est une zone dont l'état (vide / plein) est sauvegardé : plein, il redevient de l'eau
  normale pour le joueur ; les portes ne s'ouvrent que dans le bon état ;
* depuis l'intérieur, les hublots et les baies montrent le vrai monde (le vrai fond marin) ;
* l'eau du monde qui « traverse » visuellement la coque n'est pas dessinée dans les zones sèches.

Ce sont des mixins sur le contact avec les fluides (`Entity`) et sur le rendu (caméra, brouillard).
C'est faisable mais c'est le point le plus risqué. Il sera développé et testé en jeu **en premier**,
sur un prototype de coque, avant toute la décoration : si une partie ne marche pas, je te le dirai.

## 5. Architecture proposée (option C : 96 × 14 × 17)

Coordonnées du Nautilus : z vers l'avant, y = 0 au plancher du niveau principal.

* **Double fond** (y −3 à 0) : ballasts, conduites, câbles, coursive technique de 2 blocs de haut
  sur toute la longueur, trappes cachées.
* **Niveau inférieur** (y −3 à 0 au centre, plus bas sous le salon) : sas des scaphandres (avant),
  réserves, accès techniques, salles des batteries (arrière).
* **Niveau principal** (y 0 à 4,5), de l'avant vers l'arrière :
  chambre de Nemo · cabine d'Aronnax · coursive · salle à manger (8 × 6) · bibliothèque (8 × 6) ·
  **grand salon (14 × 7, 6,5 de haut, orgue au fond, baies vitrées des deux côtés)** · escalier central
  en colimaçon · cuisine · batteries (section A) · moteur (section B), 20 blocs au total.
* **Dessus** : timonerie blindée à l'avant (4 hublots, roue, compas, leviers, cadrans) par échelle et
  trappe étanche, cage du projecteur derrière, logement du canot avec trappe vers l'intérieur,
  plate-forme.
* **Accès extérieur** (planche, image 10) : puits avec échelle vers une trappe sur le dessus.

## 6. Décisions

* Dimensions retenues : **option C, 96 × 14 × 17** (timonerie à 23).
* Meubles : tes 5 mods ont été reçus et inspectés (section 2).

## 6 bis. Points qui demandaient ta décision (pour mémoire)

1. **Mods de décoration** : envoie-moi tes `.jar` (ou la liste exacte avec leurs versions et leurs
   liens). Sinon, je modélise tous les meubles moi-même, d'après les images.
2. **Dimensions** : A, B ou C (voir section 3).
3. **Images** : je n'ai reçu qu'une image, la planche Minecraft. Le cahier des charges parle aussi de
   photographies historiques, d'un plan en coupe et d'une description détaillée de l'intérieur.
   Envoie-les si tu les as, de préférence **en fichiers** (pour que je puisse les découper et faire
   les planches de comparaison).

## 7. Découpage et livraisons intermédiaires

Le projet est trop gros pour une seule livraison : chaque étape sera testée en jeu (solo + serveur
dédié, avec et sans Lithium) et livrée sous forme de jar.

1. Prototype : coque simplifiée, zones sèches, marche à l'intérieur sous l'eau, plongée et remontée,
   collisions. **Valide la faisabilité.**
2. Extérieur fidèle : coque, éperon, ailerons, hélice, hublots, timonerie, projecteurs.
3. Structure intérieure : niveaux, cloisons, coursives, portes animées, escaliers, échelles, trappes.
4. Décoration des salles, une par une, avec une comparaison à l'image pour chacune.
5. Interactions : sièges, lampes, volets des baies, projecteurs, sas, canot détachable.
6. Navigation sous-marine et pilote automatique 3D (itinéraires `submarine`).
7. Tests complets, captures comparatives, documentation.
