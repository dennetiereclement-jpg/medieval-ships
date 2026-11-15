# La Forge divine steampunk (1.34.0)

Un grand atelier de fabrication **posé d'un seul objet** comme les [ateliers](ATELIERS.md) et les [tentes](TENTES.md) :
fourneau central en pierre sculptée au feu très lumineux, croix dorée, grande enclume noire, deux colonnes de chaleur
lumineuses, engrenages dorés sur la façade, tuyaux de cuivre, statue divine ailée au sommet, bannières bleues et or,
chaînes et lanternes, établis à tiroirs, cristal doré, presse mécanique, plateforme de pierre décorée. Environ
**13 x 10 x 6 blocs**.

Contrairement aux huit ateliers classiques, la forge est **animée** et a **sa propre interface de fabrication** :
engrenages qui tournent, feu et colonnes qui ondulent, étincelles, vapeur, lueur sacrée, coups d'enclume pendant une
fabrication ; recettes lues depuis les **datapacks**, compatibles avec les objets et monnaies du serveur, et des
exigences facultatives pour se brancher sur les **métiers du serveur** (sans en créer un second).

Aucune génération naturelle, aucune entité pour l'animation, aucun vrai feu (rien ne brûle, aucun bloc n'est détruit),
compatible serveur dédié. Le mod doit être installé sur le serveur **et** les clients.

## Pose et retrait

- **Objet** : `medievalships:forge_divine`, onglet créatif **Ateliers** (après les huit ateliers), piles de 16 ;
  `/workshop give forge_divine [joueurs]` (ou `/tent give`, `/ship give`), `/give @p medievalships:forge_divine`.
- **Pose** : clic droit au sol avec l'objet. La **façade fait face au joueur** qui la pose. Comme les tentes, la place
  est vérifiée d'abord : toute l'emprise (tournée selon l'orientation, 13 x 7 blocs au sol, 10 de haut) doit être libre
  (air, herbes, fleurs, neige…) et le sol plein sous au moins 60 % de l'emprise ; sinon un message en rouge
  (« Pas assez de place pour la forge divine (13 x 7 blocs, 10 de haut) : Pierre en x y z. ») et rien n'est posé.
  Admin : `/workshop place forge_divine [x y z] [south|west|north|east]`.
- **Lumière** : le bloc d'ancrage éclaire comme une balise (niveau 15) ; le feu, les colonnes, les lanternes, le
  cristal, l'auréole et la grille de lave sont dessinés en pleine lumière.
- **Collisions** : les boîtes du descripteur (`workshops/forge_divine.json`) : la plateforme se monte à pied (marche
  de 0,5 bloc au plus), on est arrêté par la masse du fourneau, les colonnes, les établis, l'enclume et la presse ;
  rien sous les éléments suspendus (bannières, lanternes, chaînes).
- **Retrait** : casser le bloc d'ancrage (en créatif : rien ne tombe ; en survie : l'objet est rendu),
  `/tent remove [x y z]`, `/workshop remove [x y z]` (alias `/atelier`). Il ne reste **aucun bloc, aucune collision,
  aucun bloc-entité, aucune entité**. Si une fabrication était en cours, elle se termine sur-le-champ : son résultat est
  remis à son joueur s'il est connecté, sinon posé au sol devant la forge, ainsi que les résultats gardés pour des
  joueurs absents (rien n'est perdu).

## Animation et effets

Le rendu est fait par le client à partir du bloc d'ancrage (un bloc-entité, aucune entité) :

- la partie fixe est un maillage « cuit » une fois (comme les tentes), découpé hors de la vue ; rien n'est dessiné
  au-delà de `tentRenderDistance` (64 blocs par défaut), les petits détails (os `detail`) au-delà de
  `tentDecorDistance` (32) ;
- les **engrenages** tournent lentement au repos et plus vite pendant une fabrication (`gear_a_*` dans le sens horaire
  vu de face, `gear_b_*` dans l'autre sens), avec un changement d'allure progressif ;
- le **feu** et les **colonnes de chaleur** sont des animations image par image (4 images), plus rapides pendant une
  fabrication ; des éléments ne s'allument **qu'en fabrication** (fourneau plus vif, colonnes plus brillantes, lumière
  dorée autour de la statue : os `craft_*`) ou seulement au repos (`idle_*`) ;
- **effets**, seulement si un joueur est à moins de **24 blocs** : étincelles et braises de temps en temps (enclume,
  fourneau), bouffée de vapeur des tuyaux de temps à autre, lueur sacrée autour de la statue ; tout est plus fréquent
  en fabrication. **Sons** espacés : crépitement du feu, léger bruit de machinerie, souffle de vapeur ; en fabrication,
  coups de marteau sur l'enclume avec une gerbe d'étincelles ; au début, un bruit d'outil ; à la fin, un son
  « magique » (balise + carillon d'améthyste) et une gerbe de lumière. Particules et sons vanilla uniquement.

## Clic droit : le même circuit que les autres ateliers

Le clic se fait sur le **bloc d'ancrage** (comme pour tous les objets posés) : au pied du fourneau, au centre de la
façade, là où le contour de visée apparaît. Côté serveur, un clic droit sur ce bloc (avec ou sans objet en main) :

1. remet d'abord au joueur les **résultats que la forge gardait pour lui** (fabrications terminées pendant qu'il était
   déconnecté) ;
2. déclenche l'événement Fabric **`WorkshopUseCallback`** avec le métier **`forge_divine`** (un autre mod peut prendre
   la main et annuler la suite) — au plus un usage toutes les 10 ticks par joueur, rien pour un spectateur ;
3. sinon exécute la commande configurée **`workshopCommands.forge_divine`** (dans `config/medievalships.json`, section
   `server`), comme le joueur, niveau de permission 2 : pour ouvrir à la place le menu d'un système de métiers existant ;
4. **sinon ouvre l'interface intégrée de la Forge divine** (au lieu du court message des autres ateliers).

## L'interface de la Forge divine

- À gauche, les recettes d'une catégorie (« Toutes les recettes », puis **Armes légendaires, Armures divines,
  Steampunk, Objets rares, Améliorations**, avec les flèches `<` `>`), chacune avec l'objet produit ; une recette qu'on
  ne peut pas forger maintenant est grisée. Molette pour faire défiler.
- À droite, la recette choisie : l'objet (survol = son infobulle complète : nom, description, enchantements…), la
  catégorie, la durée, la description, chaque **ingrédient possédé / requis** (vert s'il y en a assez, rouge sinon ;
  pour un tag, « N'importe quel objet du tag … »), les **exigences non remplies avec leur raison** (en rouge :
  « Métier « forgeron » niveau 10 requis (vous : 4) », « Recette à débloquer (tag « … » requis) », « Réservée au
  niveau d'opérateur 2 »), et le bouton **« Forger »** (actif seulement si tout est là et la forge libre).
- En haut, l'état de la forge : « Au repos » ou « En fabrication : … — 7 s » (« Votre commande : … » si c'est la vôtre)
  avec une barre de progression, et le nombre d'objets gardés pour vous.
- La liste vient du serveur (en 1.21.11 les recettes ne sont pas envoyées aux clients) : elle est envoyée à l'ouverture,
  après chaque clic, et de nouveau quand l'inventaire change (au plus une fois par seconde).

Au clic sur « Forger », **le serveur revérifie tout** : forge libre (sinon « La forge est occupée (encore 12 s). »),
recette toujours chargée, exigences, ingrédients. Il **retire exactement les ingrédients** (inventaire principal,
puis barre d'action, puis main secondaire ; un même tas peut servir à deux ingrédients, le partage est calculé pour
ne jamais échouer à tort), lance la fabrication (**une seule à la fois par forge**), anime la forge pendant `duree`,
puis **donne le résultat** au joueur : dans son inventaire, **au sol à ses pieds** si l'inventaire est plein ; **s'il
est déconnecté**, le résultat (et sa commande de récompense) est **gardé dans la forge** et lui est rendu à son
prochain clic. La fabrication en cours est **sauvegardée** : elle continue après un redémarrage du serveur (son temps
est celui du jeu, arrêté pendant que le serveur est éteint).

## Format des recettes (datapacks)

Type de recette **`medievalships:forge_divine`**, fichiers `data/<namespace>/recipe/<nom>.json` d'un datapack (ou d'un
mod), rechargés par `/reload`. `/forge recettes` liste ce qui est chargé ; une recette invalide est refusée et le
journal du serveur dit pourquoi (« Couldn't parse data file … forge divine : … »).

| champ | obligatoire | contenu |
|---|---|---|
| `type` | oui | `"medievalships:forge_divine"` |
| `ingredients` | oui | 1 à 12 ingrédients : `{"item": "minecraft:gold_ingot", "count": 4}` ou `{"tag": "c:ingots/gold", "count": 4}` (le `#` est facultatif) ; `count` 1 par défaut ; facultatif : `"components"` (composants **exacts** que le tas doit avoir) et `"predicates"` (correspondance **partielle**, ex. une partie de `minecraft:custom_data`), aux formats des prédicats d'objets vanilla. Raccourci : `"minecraft:diamond"` ou `"#minecraft:planks"` (quantité 1). |
| `result` | oui | une pile d'objet au format vanilla : `{"id": ..., "count": ..., "components": {...}}` (nom `minecraft:custom_name`, lore `minecraft:lore`, enchantements `minecraft:enchantments`, `minecraft:custom_data`…), ou juste un id |
| `duree` | non | durée en ticks (20 = 1 s), 200 par défaut, de 1 à 72000 (1 h) |
| `categorie` | non | `armes_legendaires`, `armures_divines`, `steampunk`, `objets_rares`, `ameliorations` (inconnue ou absente : `objets_rares`) |
| `metier` | non | objectif de scoreboard du métier du serveur |
| `niveau` | non | score minimal dans `metier` (1 si seul `metier` est donné) |
| `tag` | non | tag de commande que le joueur doit avoir (`/tag … add …`), ex. recette débloquée par une quête |
| `permission` | non | niveau d'opérateur minimal (0 à 4) |
| `commande` | non | une commande ou une liste (8 au plus), exécutée(s) **comme le joueur** (niveau 2, silencieusement) quand le résultat lui est remis : XP du métier, message, fonction… |
| `nom` | non | nom affiché dans l'interface (sinon le nom de l'objet produit) |
| `description` | non | une ligne de texte sous la recette |
| `ordre` | non | tri à l'intérieur de la catégorie (puis le nom) |
| `essai` | non | `true` : recette d'essai, masquée quand `forgeTestRecipe` vaut `false` |

Les accents sont acceptés dans les noms de champs (`durée`, `catégorie`, `métier`) et dans les catégories
(« Armes légendaires »).

**Exemple simple** — `data/monserveur/recipe/forge/lame_aube.json` :

```json
{
  "type": "medievalships:forge_divine",
  "categorie": "armes_legendaires",
  "duree": 600,
  "ingredients": [
    {"item": "minecraft:netherite_ingot", "count": 2},
    {"item": "minecraft:nether_star"},
    {"tag": "minecraft:logs", "count": 4}
  ],
  "result": {
    "id": "minecraft:netherite_sword",
    "components": {
      "minecraft:custom_name": {"text": "Lame de l'Aube", "italic": false, "color": "gold"},
      "minecraft:lore": [{"text": "Forgée dans le feu sacré", "italic": true, "color": "gray"}],
      "minecraft:enchantments": {"minecraft:sharpness": 5, "minecraft:unbreaking": 3}
    }
  },
  "description": "Une lame qui brille au lever du soleil."
}
```

**Avec la monnaie du serveur et un métier** (la monnaie est un objet avec des composants : une émeraude avec un
`custom_data`, par exemple) :

```json
{
  "type": "medievalships:forge_divine",
  "categorie": "armures_divines",
  "duree": 1200,
  "ingredients": [
    {"item": "minecraft:emerald", "count": 30, "predicates": {"minecraft:custom_data": {"monnaie": "couronne"}}},
    {"item": "minecraft:diamond_chestplate"},
    {"item": "minecraft:paper", "components": {"minecraft:custom_model_data": {"floats": [12]}}}
  ],
  "result": {"id": "minecraft:diamond_chestplate", "components": {"minecraft:custom_name": "Cuirasse bénie"}},
  "metier": "forgeron",
  "niveau": 25,
  "tag": "quete_cuirasse_finie",
  "commande": ["scoreboard players add @s forgeron_xp 120", "tellraw @s {\"text\":\"+120 XP de forgeron\",\"color\":\"gold\"}"],
  "nom": "Cuirasse bénie",
  "ordre": 1
}
```

Ici une émeraude ordinaire ne compte pas : seule celle qui a `{"monnaie": "couronne"}` dans son `custom_data` paie
(`predicates` = correspondance partielle ; `components` = valeur exacte du composant).

### La recette d'essai

Le mod fournit **une seule recette, d'essai** : `data/medievalships/recipe/forge_divine_essai.json` — 4 lingots d'or
\+ 1 diamant → une épée en or nommée **« Lame divine (essai) »** (lore, Solidité I), 10 s, catégorie Armes
légendaires, marquée `"essai": true`. Pour la **désactiver** : `"forgeTestRecipe": false` dans la section `server` de
`config/medievalships.json` (puis redémarrage ou `/ship reload`), ou un datapack qui remplace ce fichier par une autre
recette. Toutes les autres recettes sont celles de vos datapacks.

## Se brancher sur les métiers, l'XP, les commandes, les PNJ

La forge **ne crée pas de second système de métiers** : elle lit et nourrit celui du serveur.

- **Niveau de métier** : `metier` + `niveau` lisent un **objectif de scoreboard** (la plupart des datapacks et
  systèmes de métiers en tiennent un ; sinon il suffit qu'ils recopient le niveau dans un score :
  `execute store result score @s forgeron run …`). Un objectif inexistant rend la recette inaccessible avec la raison
  « métier inconnu du serveur ».
- **XP du métier** : `commande` est exécutée comme le joueur à la remise du résultat (comme les commandes d'ateliers) :
  `scoreboard players add @s forgeron_xp 25`, `xp add @s 10 points`, `function monserveur:metiers/xp_forge`…
  Si le joueur était déconnecté, elle s'exécute quand il récupère l'objet.
- **Recettes débloquées par une quête** : `tag` ; la récompense de la quête fait `tag <joueur> add recette_lame`.
- **Réservé aux administrateurs** : `permission` (niveau d'opérateur).
- **Remplacer l'interface** par le menu d'un système existant : `"workshopCommands": {"forge_divine": "…"}` ; ou un
  mod Java qui écoute `WorkshopUseCallback` (métier `forge_divine`).
- **Système de métiers qui a ses propres recettes** : il peut seulement **faire jouer l'animation** à la forge pendant
  sa propre fabrication : `/forge animer x y z 10` (10 secondes), `/forge arreter x y z`, ou l'API Java ci-dessous.
- **PNJ (Easy NPC ou autre)** : un PNJ capable d'exécuter une commande peut débloquer une recette (`tag @p add …`),
  ouvrir l'interface de la forge à un joueur qui se tient près d'elle (`/forge ouvrir <joueur> [x y z]`), ou lancer
  l'animation (`/forge animer x y z <secondes>`). Non testé avec Easy NPC lui-même : seules les commandes le sont.

## Commandes (administrateurs)

Sans position, la forge la plus proche à moins de 48 blocs ; une position peut être n'importe quel bloc de la forge.

| commande | effet |
|---|---|
| `/forge animer [x y z] <secondes>` | joue l'animation de fabrication (1 à 3600 s) ; rien n'est remis à la fin ; refusé si la forge est occupée |
| `/forge arreter [x y z]` | termine la fabrication en cours **maintenant** : une animation s'arrête, une fabrication de joueur se termine en avance (le résultat lui est remis) |
| `/forge etat [x y z]` | au repos ou en fabrication (quoi, pour qui, temps restant, %), résultats gardés pour des absents |
| `/forge recettes` | les recettes de forge chargées (catégorie, durée, essai, exigences) |
| `/forge ouvrir <joueurs> [x y z]` | ouvre l'interface aux joueurs qui sont à moins de 6 blocs de la forge (action d'un PNJ) |

Et les commandes des ateliers : `/workshop give|place|remove|list|types` (alias `/atelier`), `/tent remove`.

## API Java (`fr.medievalships.api.DivineForgeApi`)

Côté serveur ; chaque méthode prend le bloc d'ancrage ou n'importe quel bloc de la forge.

```java
// 30 s d'animation, rien n'est remis (votre mod donne lui-même son objet)
DivineForgeApi.startCrafting(world, pos, 600);
// 10 s, puis la forge remet la pile au joueur (gardée pour lui s'il est absent)
DivineForgeApi.startCrafting(world, pos, 200, player, maPile);
DivineForgeApi.stopCrafting(world, pos);          // termine maintenant
DivineForgeApi.isCrafting(world, pos);            // aussi côté client (copie synchronisée)
DivineForgeApi.remainingTicks(world, pos);
DivineForgeApi.openInterface(player, pos);        // l'interface intégrée, quoi que dise workshopCommands
DivineForgeApi.recipes(world);                    // ids des recettes chargées

DivineForgeApi.CRAFT_STARTED.register((world, pos, player, recipe, ticks) -> { /* ... */ });
DivineForgeApi.CRAFT_FINISHED.register((world, pos, player, playerId, recipe, result, animationOnly) -> {
    if (player != null && recipe != null) MesMetiers.ajouterXp(player, "forge", 25);
});
```

`CRAFT_FINISHED` : `player` est null si le joueur est déconnecté (le résultat est alors gardé dans la forge),
`recipe` est null pour une animation, `medievalships:api` pour `startCrafting(…, player, pile)`, `result` est une copie
de ce qui a été remis. Le bloc-entité est `fr.medievalships.forge.DivineForgeBlockEntity` (type
`medievalships:forge_divine`), l'état pur `fr.medievalships.core.ForgeCraft`.

## Réglages (`config/medievalships.json`, section `server`)

- `forgeTestRecipe` (`true`) : affiche la recette d'essai (et toute recette `"essai": true`) ;
- `workshopCommands.forge_divine` : une commande à la place de l'interface (voir plus haut) ;
- `tentRenderDistance` (64) / `tentDecorDistance` (32) : distances de dessin, communes avec les tentes et ateliers.

## Fichiers et contrat des modèles

- Descripteur `assets/medievalships/workshops/forge_divine.json` (format des ateliers) : `model`, `texture`, `extent`,
  `colliders`, `light` (forcée à 15 par le code), `profession` (`forge_divine`) et **`extra_models`** :
  `[{"model": "models/entity/forge_divine_deco.bbmodel", "texture": "textures/entity/forge_divine_deco.png"}]` —
  modèles dessinés avec la même transformation que le modèle principal, chacun avec son atlas (le champ est général :
  tout objet posé peut en avoir).
- Deux modèles : la **structure** (`models/entity/forge_divine.bbmodel` + `textures/entity/forge_divine.png`) et le
  **décor** (`forge_divine_deco.bbmodel` + `forge_divine_deco.png`), générés par `tools/forge/`.
- Os reconnus par le rendu (dans l'un ou l'autre modèle) : `gear_a_<n>` / `gear_b_<n>` (tournent autour de leur axe z
  local par leur pivot), `<nom>_f<n>` (animation image par image : `fire_f0..3`, `flow_l_f0..3`, `flow_r_f0..3`),
  `craft_*` (visibles en fabrication), `idle_*` (visibles au repos), `detail` (cachés au loin), cubes `glow*` (pleine
  lumière), os vides `fx_spark_*`, `fx_steam_*`, `fx_ember_*`, `fx_holy_*` (leur pivot = point d'émission des effets).
  Sans ces os, la forge est simplement dessinée immobile ; sans les points `fx_*`, les effets partent de points fixes
  (enclume, fourneau, tuyaux, statue). Un modèle absent n'est pas dessiné (journalisé), le jeu ne plante pas ; un
  descripteur absent est remplacé par l'enveloppe convenue (13 x 10 x 6).

## Tests

- **JUnit** (`DivineForgeTest`) : l'objet (famille des ateliers, métier `forge_divine`, avant l'artillerie dans
  `PROPS`, lumière 15, « posée »), le descripteur (enveloppe 13 x 10 x 6, colliders dans l'emprise, bord avant
  franchissable, rien sous les bannières, `extra_models`), le champ `extra_models` pour tout objet, le repli si le
  descripteur manque, les os du contrat dans les deux modèles, l'axe d'un engrenage selon la rotation de son os ; la
  recette d'essai du jar ; la lecture de tous les champs, alias et valeurs par défaut, 19 recettes invalides refusées ;
  les exigences (métier inconnu, niveau insuffisant, sans score, tag, permission) ; le paiement **exact** sur un
  inventaire simulé (plusieurs tas, ingrédients manquants, tas partagé entre un tag et un de ses objets, monnaie à
  composants distinguée des émeraudes ordinaires, 300 planches sur 41 cases) ; la machine d'état (occupée, échéance,
  progression, arrêt, animation, restauration après redémarrage) ; les flipbooks et engrenages en fonction du temps
  (images dans l'ordre, vitesses, changement d'allure sans saut, pause, retour en arrière).
- **En jeu** (`ForgeGameTest`, appelé par `ShipClientGameTest` en solo, après redémarrage et en serveur dédié ;
  `-PgametestOnly=forge` pour lui seul) : les deux modèles chargés avec leurs os, le refus faute de place, la pose
  orientée, le bloc-entité, la lumière 15, l'emprise, les collisions (masse du fourneau, rien sous les bannières, un
  joueur qui marche monte sur la plateforme et est arrêté), le clic avec une commande configurée puis sans (ouverture
  de l'interface, recette d'essai listée 0/4 0/1), la fabrication par le bouton (4 lingots et 1 diamant retirés
  exactement, « La forge est occupée », état vu par le client, épée nommée reçue après la durée, événements de l'API),
  `forgeTestRecipe`, `/forge animer|etat|arreter`, l'API, le retrait par `/tent remove` et par un joueur en créatif
  (aucun bloc, collision, bloc-entité ni objet restant, côté serveur et client), une fabrication conservée après le
  redémarrage du monde ; captures de face, de 3/4, de près, en fabrication, de nuit.

## Limites (honnêtes)

- Une seule fabrication à la fois par forge (voulu) ; pas de file d'attente.
- Les recettes n'apparaissent pas dans le livre de recettes vanilla ni dans JEI/REI/EMI.
- Le paiement prend l'inventaire principal, la barre d'action et la main secondaire, pas l'armure portée ni le contenu
  des sacs ou boîtes de Shulker ; un joueur en créatif paie aussi ses ingrédients.
- `permission` est un niveau d'opérateur (pas de nœuds de permission : aucun mod de permissions n'est requis).
- Une recette rechargée (`/reload`) pendant une fabrication ne change pas celle-ci : le résultat est fixé au lancement.
- Si la forge est retirée alors qu'elle garde des résultats pour des joueurs absents, ces objets sont posés au sol
  devant elle et leurs commandes de récompense ne sont pas exécutées.
- L'interface montre au plus 512 recettes. Les commandes de récompense sont exécutées comme le joueur avec le niveau 2 :
  seuls les datapacks du serveur les choisissent.
- Les effets (particules, sons) sont côté client et seulement à moins de 24 blocs ; pas de son personnalisé (sons
  vanilla).
- Non testé : le branchement réel avec Easy NPC ou un plugin de métiers précis (seules les commandes et l'API le sont),
  de très nombreuses forges actives à la fois, des centaines de recettes.
