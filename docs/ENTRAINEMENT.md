# Aires d'entraînement (un bloc = une aire)

Trois aires d'entraînement médiévales pour une cour de caserne, une place de ville ou une guilde (1.18.0). **Chaque
aire est UN seul bloc**, exactement comme les [tentes](TENTES.md), les [charrettes](CHARRETTES.md) et les
[ateliers](ATELIERS.md) : on pose le bloc, l'aire entière (sol, clôture, mannequins, sac de frappe, râteliers,
auvent, bannières, lanternes) est dessinée à partir de lui, comme un seul modèle statique. Depuis la 1.19.0, les
**mannequins et le sac de frappe réagissent aux coups** (voir « Cibles interactives ») et les aires sont
**indestructibles en survie** (voir « Indestructibles, retrait par un admin »). Aucun vrai bloc de terrain n'est posé
ni remplacé : rien à nettoyer quand on retire l'aire.

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
- **Retirer** (admin) : en mode créatif, casser le bloc d'ancrage (la fine dalle au centre de l'aire), ou
  `/tent remove [nearest|x y z]`, ou `/training remove [nearest|x y z]`. En survie et en aventure, on ne peut pas la
  casser (voir plus bas).
- `/tent list` liste les aires posées avec les tentes et les autres objets en un bloc ; `/training list` les aires
  seules (`/training` est l'arbre de `/tent` limité aux trois aires : `give`, `place`, `remove`, `list`, `types`).

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

## Cibles interactives (1.19.0)

On peut **frapper** les mannequins et le sac de frappe : ils réagissent, sans jamais être abîmés.

- **Mannequin de paille** (aire aux frappes, trois mannequins) : le corps bascule en arrière, à l'opposé du coup,
  autour du pied du poteau (avec un petit balancement de côté, et une légère torsion si le coup est donné sur le côté),
  la tête hoche, les bras se balancent, puis tout revient doucement au repos en 3 à 4 secondes. Bruit de bois et de
  paille, quelques brins de paille qui volent.
- **Sac de frappe** (aire aux frappes) : il part en balancier à l'opposé du coup, autour du haut de sa chaîne (un
  pendule à deux axes : il oscille, se balance un peu de côté et s'amortit en une dizaine de secondes) ; un nouveau
  coup **s'ajoute** au mouvement en cours (frapper en rythme le fait balancer de plus en plus). Bruit sourd de cuir
  rembourré et cliquetis de la chaîne.
- **Mannequin à l'épée et au bouclier** (aire épée et bouclier, trois mannequins) : un coup **sur le bouclier** fait
  reculer le bouclier et le bras qui le tient (le bouclier vibre sur sa poignée), avec le bruit d'un bouclier (bois et
  fer) et des étincelles ; un coup **sur le corps** fait basculer le mannequin (moins qu'un mannequin de paille : il
  est plus lourd) et **vibrer l'épée** dans son poing. L'épée et le bouclier restent toujours dans les mains.
- La force de la réaction suit les dégâts du coup : un coup de poing fait à peine bouger un mannequin, une épée de fer
  ou une flèche bien tirée le fait basculer franchement ; un coup chargé (barre d'attaque pleine) compte plus.
- Tout ce qui passe par le chemin normal des dégâts de Minecraft marche : poing, épées, haches, masses, lances,
  tridents (tenus ou lancés), flèches, carreaux d'arbalète, et les dégâts des autres mods qui appellent `damage` sur
  l'entité avec un attaquant ou un projectile.
- **Pas de farm** : un coup n'inflige aucun dégât et compte comme « raté » pour Minecraft : pas de recul, pas d'effet
  de coup réussi (aura de feu, enchantements, balayage), pas d'usure de l'arme, pas d'expérience, pas de butin, pas de
  statistiques de dégâts ; les flèches **rebondissent** (elles ne restent pas plantées). Les mannequins ne meurent
  jamais (leurs points de vie ne baissent pas), ne brûlent pas, ne subissent ni potions, ni effets, ni explosions, ni
  foudre, ni chutes, ni noyade ; rien ne peut les pousser, les déplacer ou les faire monter dans un bateau ; les
  monstres les ignorent.
- **Multijoueur** : tout est décidé par le serveur (direction du coup, partie touchée, force) et envoyé aux joueurs
  proches ; chaque client anime ensuite la réaction lui-même. Tous les joueurs voient la même chose.
- Les sons d'une même cible sont limités (au plus un toutes les 3 ticks), les particules sont discrètes (3 ou 4).

### Comment ça marche

- Chaque mannequin et le sac sont une petite entité (`medievalships:training_target`, « Cible d'entraînement »)
  posée par l'aire elle-même : **une par cible**, à sa place, avec la boîte de la partie qui peut être frappée (le
  bouclier compris). Elle n'est **jamais sauvegardée** : quand le tronçon (chunk) de l'aire se charge, l'aire la
  recrée (une seule fois : si elle existe déjà, rien n'est ajouté) ; quand il se décharge, elle disparaît avec lui ;
  quand on retire l'aire, ses cibles partent avec elle ; une cible dont l'aire a disparu (bloc remplacé par un outil de
  construction, par exemple) se retire d'elle-même en moins de 2 secondes. Elle ne s'invoque pas (`/summon` refusé) :
  ni mannequin orphelin, ni doublon.
- `/kill` ne les tue pas (c'est voulu) : pour retirer les mannequins, on retire l'aire (`/tent remove` ou
  `/training remove`).
- Le modèle de l'aire reste un seul modèle Blockbench : chaque mannequin / sac y est rangé sous son propre os
  (`target_<i>`, avec `target_<i>_head`, `_arm_l`, `_arm_r`, `_shield`, `_sword`) ; le rendu statique de l'aire
  laisse ces os à l'entité de la cible, qui les dessine au même endroit, avec la même lumière, tournés par la
  réaction. Au repos l'image est exactement la même qu'avant. Si un client n'a pas (encore) l'entité d'une cible
  (trop loin pour le serveur, pas encore apparue), le rendu statique dessine la cible au repos : jamais de trou.
- Le champ `"targets"` du JSON de l'aire (écrit par le générateur) décrit chaque cible : genre (`dummy`,
  `shield_dummy`, `bag`), os, pivot (pied du poteau / haut de la chaîne), boîte frappable, boîte du bouclier.

### Performances

- **Serveur** : une cible ne fait presque rien à chaque tick (pas d'IA, pas de mouvement, pas de physique : elle
  vérifie seulement qu'elle est à sa place, et toutes les 2 secondes que son aire existe encore) ; ses données ne
  partent vers les clients qu'au moment d'un coup. Une aire posée ne coûte rien d'autre.
- **Client** : rien n'est calculé au repos ; après un coup, quelques oscillateurs amortis (six au plus par cible)
  sont calculés à chaque tick jusqu'au retour au repos, puis tout s'arrête.

## Indestructibles, retrait par un admin

- Les trois aires **ne se cassent pas** en survie ni en aventure (dureté de la bedrock), ne sautent pas aux
  explosions (TNT, creepers, charges de vent), ne sont pas poussées par les pistons, et ni le Wither ni le dragon ne
  les détruisent (tags `minecraft:wither_immune` et `minecraft:dragon_immune`).
- Un **admin** les retire : en **mode créatif** (casser la dalle d'ancrage au centre ; pas d'objet rendu), ou par
  commande (`/tent remove`, `/training remove` : permission d'admin, comme `/ship`).
- Le bloc d'ancrage d'une aire n'a plus qu'une fine dalle de visée (au lieu d'un bloc entier) : les mannequins debout
  au-dessus se frappent sans que le bloc les cache.
- Les autres objets en un bloc (tentes, charrettes, ateliers, canon) ne changent pas.

## Compatibilité

- **Better Combat**, **Spell Engine** (et les autres mods de combat ou de sorts) : **non testés** (ils ne sont pas
  dans la construction de test). La conception n'utilise que le chemin vanilla des dégâts (`damage` de l'entité avec
  la source du coup) : tout mod qui frappe ou blesse par ce chemin devrait faire réagir les cibles ; un mod qui le
  contournerait ne les ferait pas réagir (et ne pourrait pas les abîmer non plus : elles ne perdent jamais de vie).
  Un sort de zone sans direction pousse la cible à l'opposé du lanceur.
- Mods d'optimisation du rendu des entités (Entity Culling…) : ils peuvent ne pas dessiner une cible cachée derrière
  un mur, ce qui ne se voit pas.

## Ce qui est testé

- JUnit `TrainingTargetTest` : lecture du champ `"targets"` (genres, os par défaut, boîtes triées, bouclier réservé
  aux mannequins à bouclier, entrées invalides ignorées), rotation avec l'orientation, rayon contre une boîte (bouclier
  ou corps), force selon les dégâts ; la réaction : rien au repos, un mannequin bascule à l'opposé du coup et revient
  exactement au repos (puis ne calcule plus rien), un coup faible bouge moins qu'un fort, le sac oscille avec la
  période d'un pendule et deux coups s'ajoutent, un coup sur le bouclier fait reculer le bras du bouclier (et bouge
  moins le corps), un coup sur le corps fait vibrer l'épée ; avec les vraies aires : chaque os de cible existe, son
  origine est le pivot, la boîte est dans l'emprise, l'os dessiné seul donne exactement ce que le modèle entier
  dessine pour lui. `BbModelSubtreeTest` : le dessin d'un sous-arbre d'os, identique au repos, tourné autour des
  pivots. `TrainingTargetsModelTest` (modèles) : les os, pivots et boîtes des modèles.
- En jeu, `TrainingTargetGameTest` (solo et serveur dédié, à chaque construction CI) : les trois aires posées ; leurs
  cibles apparues une fois chacune à leur place (l'aire épée et bouclier tournée vers l'ouest), avec la bonne boîte,
  connues du client (même boîte), qui laisse leurs os aux entités ; chaque cible frappée au poing, à l'épée de fer et
  par une flèche : compteur de coups qui monte sur le serveur et sur le client, réaction animée sur le client, vie
  intacte, toujours là, rien de lâché, flèche non plantée ; coup sur le bouclier / sur le corps distingués ; `/kill`
  sans effet ; pas de doublon quand l'aire redemande ses cibles, ni après `/tent remove` et une nouvelle pose, ni
  après déchargement et rechargement des tronçons ; un joueur en survie qui mine l'ancrage ne le casse pas ; une
  explosion ne casse ni l'aire ni les cibles ; un joueur en créatif la casse (cibles retirées) ; `/training remove` ;
  captures d'un mannequin et du sac en plein mouvement et d'un coup sur le bouclier.

## Limites

- L'aire ne se tourne que par quarts de tour (la direction du joueur à la pose).
- Les cibles réagissent mais ne comptent rien (pas de score ni de statistiques d'entraînement) pour l'instant.
- L'aire aux tatamis n'a pas de cible (ses bâtons et épées sont des décors) ; son banc a deux places assises (champ
  `"seats"`).
- Au-delà de la distance de suivi des entités du serveur (en général la distance de vue), les mannequins restent
  dessinés au repos par le modèle statique et ne bougent pas.

## Pour les développeurs

- Bibliothèque partagée : `tools/training/traininglib.py` (sur `merchantlib` / `tentlib`) — atlas par aire (paille,
  sac, pierre, boucliers ronds, bannières à épées croisées / lotus / écu, auvents unis ou rayés, sols terre + pierres
  ou tatamis à bordure rouge), `fence_ring` (entrée, socles ou piliers de pierre), `dummy` (casque, épée, bouclier),
  `punching_bag`, `sword_rack`, `shield_rack`, `awning`, `lantern_post`, `post_banner`, `bench`, `flower_pot`,
  `export` (écrit `training/<id>.json`, le modèle, l'atlas, l'icône et le décor).
- Générateurs : `tools/training/generate_<id>.py` (`TRAINING_OUT=<fichier.bbmodel>` : aperçu seul).
- Java : groupe `training` (`TentType.TRAINING`, `TentTypes.TRAINING`, dans `TentTypes.PROPS` avant le canon) ; tests
  JUnit `TrainingTest` (chargement, taille 6 à 11 blocs, clôture qui bloque, entrée libre, cour praticable).
- Cibles (1.19.0) : `core/TrainingTarget` (champ `"targets"`, rotation, rayon contre une boîte, force),
  `core/TargetMotion` (oscillateurs amortis, sans classe Minecraft, testés en JUnit), `training/TrainingTargetEntity`
  (l'entité, `damage`, données suivies : compteur de coups, direction × force, point, partie),
  `training/TrainingTargets` (type d'entité, file d'attente par monde servie en fin de tick, `ensure` : une par cible,
  retrait), `tent/TrainingAreaBlock` (ancrage indestructible, dalle de visée), `client/render/TrainingTargetRenderer`
  (sous-arbre d'os par `BbModel.renderSubtree`, masque des cibles dessinées pour `TentBlockEntityRenderer`).
