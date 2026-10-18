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

## 2. Inventaire des mods de décoration : **bloquant**

Le cahier des charges demande d'inspecter tes mods de décoration et de réutiliser leurs meubles.
**Dans mon environnement de travail (un conteneur cloud), il n'y a aucun mod de décoration** :
pas de dossier `mods/`, pas de `.jar` tiers. Seuls sont présents le code de Medieval Ships, Minecraft,
Fabric, Fabric API et Lithium (pour les tests).
Je ne peux donc ni lister ni réutiliser tes meubles tant que tu ne me les fournis pas.

Remarques techniques, valables quels que soient ces mods :

* un bloc de mod ne peut pas être posé dans une entité en mouvement ; il faudrait **dessiner son
  modèle de bloc** dans le rendu du Nautilus (possible côté client, sans copier les fichiers, en
  le lisant depuis le mod installé), avec dépendance **optionnelle** ;
* leurs interactions (s'asseoir, ouvrir) sont codées pour des blocs dans le monde : elles ne
  fonctionnent pas dans une entité, il faudrait les refaire de notre côté ;
* si le mod n'est pas installé sur un client, le meuble serait invisible : il faut un modèle de
  secours dans Medieval Ships.

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
* Meubles : tu m'envoies les `.jar` de tes mods de décoration ; je les inspecte avant la phase de décoration.

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
