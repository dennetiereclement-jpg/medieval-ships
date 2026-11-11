# Performances — mesures et optimisations (1.29.0)

Le mod dessine de très gros modèles (un navire de ville fait 6 000 à 7 500 cubes, soit 30 000 à 37 000 faces ; le
Nautilus 134 000 faces avant élagage des plaques fines) et ajoute ses coques aux collisions de chaque entité qui
bouge. Sur un serveur MMO avec des dizaines d'accessoires en ville et plusieurs gros navires à quai, c'est le temps de
trame des clients et le temps de tick du serveur qui comptent. Ce document garde, version par version, ce qui a été
mesuré par le banc en jeu et ce qui a été optimisé.

## Le banc de mesure (`PerfGameTest`, joué par la CI en solo et sur serveur dédié)

Sur un terrain à part (x 6000) :

- une **place de 40 accessoires** (6 tentes de camp, 6 tentes de marchands, 8 tentes de marché, 6 charrettes,
  4 ateliers, la taverne, 6 décorations, 3 pieux) sur 8 colonnes espacées de 16 blocs et 5 rangs de 14 blocs ;
- un **port** à l'est avec les six gros navires (navire au lion, forteresse, vapeur à engrenages, galion, grand
  vaisseau, frégate bleue) à quai côte à côte à 25 blocs d'intervalle, et le Nautilus ;
- **24 mobs avec leur IA** (villageois et zombies casqués) dans les rues et sur le pont du navire au lion : chacun de
  leurs mouvements passe par le crochet de collision du mod.

Trois caméras (le marché, le quai, le pont du navire au lion), et pour chacune jusqu'à 200 trames (ou 6 s) **avec**
les rendus du mod puis **sans** (bascule de débogage `RenderStats.skip`) : temps de trame moyen, temps passé par le
mod à émettre ses sommets (`RenderStats.emitNanos`, mesuré dans ses propres commandes de rendu), quads et meubles
soumis par trame, cellules de maillage regardées et coupées, mémoire allouée par trame par le fil de rendu
(`ThreadMXBean.getThreadAllocatedBytes`). Côté serveur, 100 ticks à l'arrêt puis 100 ticks avec le navire au lion en
route : MSPT moyen (`MinecraftServer.getTickTimes`), appels du crochet de collision, coques interrogées, boîtes
ajoutées et temps passé par tick (`ShipCollisions.CALLS/SHIPS/BOXES/NANOS`), requêtes de pièces sèches
(`ShipInteriors.DRY_CALLS`), mémoire allouée par tick par le fil serveur, collectes du ramasse-miettes de tout le
banc. Tout est imprimé en lignes PASS avec les chiffres, sans seuil : la CI dessine avec llvmpipe (rendu logiciel), où
chaque trame est lente ; ce qui compte est le **avec / sans** d'un même passage et les compteurs du mod, pas la
valeur absolue. Localement : `./gradlew runProductionClientGameTest -PgametestOnly=perf`.

Modèles chargés (faces) : royal_lion_ship 37 227, fortress_ship 29 489, gear_steamship 34 742, galleon 35 388,
warship 52 702, blue_frigate 26 482, nautilus 121 819 (133 723 avant l'élagage des chants de ses plaques fines).

## Avant / après (CI, llvmpipe, solo)

_Chiffres relevés par la CI (variante vanilla, solo) : avant = branche `perf-baseline` (92e896ca), après = main 1.29.0
(4a842d80) ; voir les lignes `perf client` et `perf server` de `medievalships-test.txt`. Le rendu y est logiciel
(llvmpipe) : seuls les écarts relatifs comptent. Sous Sodium, le pont coûte 18,5 ms par trame au mod en 1.29.0._

| Mesure | 1.28.0 (avant) | 1.29.0 (après) |
|---|---|---|
| Quai : temps de trame avec / sans le mod | 25,5 / 20,6 ms (4,9 ms dus au mod) | 23,6 / 20,8 ms (2,9 ms dus au mod) |
| Quai : émission de sommets du mod par trame | 1,42 ms | 0,24 ms |
| Quai : quads soumis par trame | 11 218 | 2 535 |
| Pont : temps de trame avec / sans le mod | 113,9 / 24,6 ms (89,2 ms dus au mod) | 58,1 / 24,0 ms (34,2 ms dus au mod) |
| Pont : émission de sommets du mod par trame | 14,89 ms | 4,27 ms |
| Pont : quads soumis par trame | 144 734 | 40 948 |
| Marché : temps de trame avec / sans le mod | 42,1 / 18,2 ms (24,0 ms dus au mod) | 30,5 / 18,5 ms (12,0 ms dus au mod) |
| Mémoire allouée par trame (fil de rendu, quai) | 1,18 Mo | 0,12 Mo |
| MSPT à l'arrêt / navire en route | 3,44 / 4,38 ms | 3,86 / 3,83 ms (bruit de la machine partagée) |
| Crochet de collision : appels, temps, coques interrogées par tick | 52 appels, 0,141 ms, 365 coques | 44 appels, 0,124 ms, 16 coques |
| Mémoire allouée par tick (fil serveur) | 495 Ko | 430 Ko |

## Ce qui a été optimisé en 1.29.0

### Client

- **Maillage statique cuit** (`BbModel`) : les os qu'aucune animation ne bouge — la coque, les ponts, les mâts, les
  pièces, le mobilier de secours, soit les neuf dixièmes d'un navire — étaient déjà transformés une seule fois, mais
  recopiés quad par quad à chaque trame à travers un rappel, puis émis sommet par sommet par la chaîne
  `vertex(entry, …).color().texture().overlay().light().normal(entry, …)` de vanilla, qui alloue deux `Vector3f` par
  sommet (huit par face : plusieurs millions d'objets par trame pour six navires). Ils sont maintenant cuits une fois
  en un tableau plat (23 flottants par face : quatre coins avec leurs uv, la normale), groupés par os en **cellules de
  8 blocs**, chaque cellule découpée par texture, par classe de lumière (monde, lampes du vaisseau, faces lumineuses)
  et par face à un ou deux côtés, et le rendu reçoit ces plages entières (`BbModel.MeshSink`). Seuls les os animés
  (voiles, drapeaux, portes, rames, hélices…) sont transformés à chaque trame, par des tableaux de travail de la pose
  (plus aucune allocation par os ni par quad).
- **Émission des sommets** (`MeshEmitter`) : un seul appel `VertexConsumer.vertex(x, y, z, couleur, u, v, overlay,
  lumière, nx, ny, nz)` par sommet — celui que le `BufferBuilder` de vanilla (et celui de Sodium) écrit directement
  en mémoire — avec les positions et la normale de face transformées sur place depuis les matrices de la commande,
  la normale une fois par face.
- **Cellules hors champ** (`RenderCulling`, `WorldRendererMixin`) : vanilla ne coupe qu'une entité entière (sa boîte
  de rendu) ; les cellules du maillage dont la boîte est hors du frustum de la trame (en espace vue, à partir de la
  matrice de projection de chaque rendu du monde) ne sont pas émises — sur le pont d'un navire, la moitié arrière
  est derrière la caméra. Les accessoires dessinés hors de leur bloc (`rendersOutsideBoundingBox`), que vanilla ne
  coupe jamais, sont testés de même par leur emprise : un accessoire hors champ ne soumet rien. Désactivé sous
  Iris/Oculus (leur passe d'ombre redessine les entités du point de vue du soleil) ; sans la mixin (un autre mod qui
  remanie la méthode), tout est dessiné.
- **Faces arrière** : une face vue de dos dont le cube possède la face opposée est cachée par celle-ci ; elle n'est
  pas émise (test `normale · position` en espace vue, une multiplication par face). Les faces dont le cube n'a pas de
  face opposée (le dessus seul d'un pont, une vitre intérieure) sont marquées « deux côtés » et jamais sautées : la
  même image, avec moins de sommets. Les effets translucides (faisceau du projecteur, eau du sas) gardent leurs deux
  faces.
- **Niveaux de détail** : au-delà de 48 blocs les pièces et leur mobilier, au-delà de 80 les petits détails (déjà
  en 1.27), et désormais au-delà de 160 les cordages et les canons (des choses de moins d'un pixel à cette distance).
- **Poses réutilisées** (`BbModel.scratchPose`) par les rendus des navires, accessoires, cibles d'entraînement,
  leviers et aperçu de placement (plus de pose allouée par trame et par texture).
- **Visée** : `ShipPicker` ignore les navires hors de portée du rayon (plus de lancer de rayon par trame contre chaque
  navire du monde) ; `SeatPicker` ne regarde que les accessoires des chunks à portée (plus de copie de la liste de
  tous les accessoires à chaque trame).

### Serveur

- **Crochet de collision** (`ShipCollisions.withHulls`, appelé pour chaque mouvement de chaque entité) : la liste
  vanilla n'est plus copiée que si une boîte est réellement ajoutée (`Lazy`) ; chaque coque passe d'abord une **phase
  large** par cercle englobant (élargi de la portée d'une passerelle déployée) avant tout calcul de pose, d'état de
  portes, d'ouverture de bastingage ou de cellules ; `HullContact` n'alloue plus de tableau d'axes par boîte.
- **Transport des entités du pont** (`ShipEntity.carryEntities`) : un navire à l'arrêt ne balaye plus les entités
  de sa zone à chaque tick (une fois sur dix, pour garder le filet de secours d'une entité enfoncée dans le pont).

### Mesuré et laissé tel quel

- `DryWater.tick` (quelques objets par navire et par tick, redessin borné), le ticker du pieu (tous les 5 ticks, une
  petite boîte), les autres accessoires (aucun ticker), les données synchronisées de `ShipEntity` (déjà envoyées
  seulement quand elles changent), le NBT des navires (quelques dizaines de champs), les charges réseau (`SitPayload`,
  `DrawbridgeSyncPayload`, configuration : rien de périodique).
- Le mobilier des mods de décoration (`submitBlock` par meuble et par trame dans les 48 blocs) : des blocs vanilla,
  déjà coupés par distance ; un cache par vaisseau serait la suite.
- Les modèles sont chargés une fois et partagés par tous les rendus (`ShipModels`, `TentModels`) ; le maillage cuit
  s'ajoute à la mémoire des quads (environ 90 octets par face, cuit à la première trame de chaque modèle dessiné).
