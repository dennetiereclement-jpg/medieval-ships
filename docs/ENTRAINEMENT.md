# Aires d'entraînement (un bloc = une aire)

Trois aires d'entraînement médiévales pour une cour de caserne, une place de ville ou une guilde (1.18.0). **Chaque
aire est UN seul bloc**, exactement comme les [tentes](TENTES.md), les [charrettes](CHARRETTES.md) et les
[ateliers](ATELIERS.md) : on pose le bloc, l'aire entière (sol, clôture, mannequins, sac de frappe, râteliers,
auvent, bannières, lanternes) est dessinée à partir de lui, comme un seul modèle statique. Pas d'entité, pas
d'animation, rien ne « tick » : on peut en poser une cinquantaine sur une carte sans coût de calcul. Aucun vrai bloc
de terrain n'est posé ni remplacé : rien à nettoyer quand on retire l'aire.

| id | nom | contenu |
|----|-----|-----|
| `training_area_dummy` | Aire d'entraînement aux frappes (Strike Training Area) | cour carrée d'environ 7 x 7 blocs en terre battue et pierres, clôture de poteaux cerclés de fer et de lisses en planches sur les quatre côtés, socles de pierre aux quatre coins, une entrée à l'avant ; trois mannequins de paille et de bois de tailles différentes (poteau, corps de paille lié de corde, bras en croix, tête) ; un lourd sac de frappe pendu à une chaîne sous une potence (au fond à droite, rouleau de corde sur le poteau) ; un petit auvent de toile rouge (au fond à gauche) sur un râtelier d'épées d'entraînement, tonneaux et caisses ; quatre petites bannières rouges aux épées croisées (deux sur les grands poteaux du fond, deux sur les poteaux d'angle avant) ; deux lanternes |
| `training_area_tatami` | Aire d'entraînement aux tatamis (Tatami Training Area) | sol de tatamis beiges bordé de rouge avec un motif au centre, clôture et entrée, petit étal à l'auvent rayé rouge et beige (banc, étagères, jarres, linges pliés), bâtons et épées de bois contre la clôture, bannières rouges au lotus doré, lanternes sur de hauts poteaux, pot de fleurs roses sur un socle de pierre (modèle de l'agent L) |
| `training_area_shield` | Aire d'entraînement épée et bouclier (Sword & Shield Training Area) | sol de terre et de pierres, clôture à piliers de pierre et entrée, trois mannequins de bois casqués tenant une épée et un bouclier rond (anneaux rouges et blancs, bord et umbo de fer), étal à l'auvent rayé bleu et beige avec râtelier de boucliers et d'épées, râtelier d'épées contre la clôture, tonneaux, bannières bleues à l'écu doré, lanternes sur de hauts poteaux (modèle de l'agent L) |

Objets : `medievalships:training_area_dummy`, `medievalships:training_area_tatami`,
`medievalships:training_area_shield` — dans l'onglet créatif **Entraînement** (séparé des tentes, des charrettes, des
ateliers et de l'artillerie). Piles de 16.

## Obtenir, poser, orienter, retirer

- **Obtenir** : onglet créatif « Entraînement », ou `/give @p medievalships:training_area_dummy`, ou
  `/tent give <id> [joueurs]` (aussi `/ship give <id>`). Noms courts acceptés par les commandes : `dummy`, `tatami`,
  `shield`.
- **Poser** : clic droit sur le sol avec l'objet. L'aire est posée **l'entrée tournée vers le joueur**. Il faut une
  place libre sur toute l'emprise (environ 8 x 8 blocs, 4 de haut ; herbes, fleurs et neige sont simplement couvertes)
  et un sol plein et à peu près plat ; sinon un message en français explique le refus (« Pas assez de place pour l'aire
  d'entraînement… », « Le sol n'est pas assez plein sous l'aire d'entraînement… »). Rien n'est jamais écrasé.
- Ou par commande : `/tent place <id> [x y z] [south|west|north|east]`.
- **Retirer** : casser le bloc d'ancrage (au centre de l'aire ; il rend l'objet), ou `/tent remove [nearest|x y z]`.
- `/tent list` liste les aires posées avec les tentes et les autres objets en un bloc.

## Collisions et circulation

- La **clôture bloque** (environ 1,5 bloc de haut, comme une clôture vanilla) : on entre par l'**entrée** (au moins
  1,5 bloc de large), on ne saute pas par-dessus.
- Mannequins, sac de frappe et sa potence, râteliers, banc, tonneaux, caisses, poteaux de l'auvent et des bannières
  sont solides.
- Le **sol** de l'aire est une fine plaque posée sur le terrain, sans collision : on marche sur le vrai sol en dessous.
  Pas de mur invisible : chaque boîte de collision correspond à un objet dessiné.

## Blocs des mods (dessinés en place si le mod est installé)

`training_area_dummy` : `landsoficaria:cypress_barrel` (tonneau, sinon `minecraft:barrel`), `furnish:spruce_crate`
(petite caisse sur la caisse de gauche, sinon une caisse dessinée), `farmersdelight:straw_bale` (botte de paille près de
l'auvent, sinon une botte dessinée). Le reste (épées, sac de frappe, mannequins, bannières) est modélisé : les objets
des mods (armes, armures) ne peuvent pas être intégrés comme blocs.

## Limites

- Ce sont des **décors** : frapper un mannequin ou le sac ne fait rien de particulier (pas de statistiques, pas de
  dégâts, pas d'animation) pour l'instant.
- L'aire ne se tourne que par quarts de tour (la direction du joueur à la pose).
- Pas encore vérifié en jeu au moment de l'écriture : les trois aires sont posées une fois chacune par le test en jeu
  (TentGameTest) à la prochaine construction CI ; `training_area_tatami` et `training_area_shield` sont, sur la
  branche `training-core`, des ébauches copiées de l'aire aux frappes, remplacées par les modèles de l'agent L à la
  fusion.

## Pour les développeurs

- Bibliothèque partagée : `tools/training/traininglib.py` (sur `merchantlib` / `tentlib`) — atlas par aire (paille,
  sac, pierre, boucliers ronds, bannières à épées croisées / lotus / écu, auvents unis ou rayés, sols terre + pierres
  ou tatamis à bordure rouge), `fence_ring` (entrée, socles ou piliers de pierre), `dummy` (casque, épée, bouclier),
  `punching_bag`, `sword_rack`, `shield_rack`, `awning`, `lantern_post`, `post_banner`, `bench`, `flower_pot`,
  `export` (écrit `training/<id>.json`, le modèle, l'atlas, l'icône et le décor).
- Générateurs : `tools/training/generate_<id>.py` (`TRAINING_OUT=<fichier.bbmodel>` : aperçu seul).
- Java : groupe `training` (`TentType.TRAINING`, `TentTypes.TRAINING`, dans `TentTypes.PROPS` avant le canon) ; tests
  JUnit `TrainingTest` (chargement, taille 6 à 11 blocs, clôture qui bloque, entrée libre, cour praticable).
