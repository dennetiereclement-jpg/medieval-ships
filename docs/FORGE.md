# La Forge divine steampunk (1.34.0)

Un grand atelier **posé d'un seul objet** comme les [ateliers](ATELIERS.md) et les [tentes](TENTES.md) : fourneau
central en pierre sculptée au feu très lumineux, croix dorée, grande enclume noire, deux colonnes de chaleur
lumineuses, engrenages dorés sur la façade, tuyaux de cuivre, statue divine ailée au sommet, bannières bleues et or,
chaînes et lanternes, établis à tiroirs, cristal doré, presse mécanique, plateforme de pierre décorée. Environ
**13 x 10 x 6 blocs**.

La forge est **animée** (engrenages qui tournent, feu et colonnes qui ondulent, étincelles, vapeur, lueur sacrée) et
peut passer « **en activité** » (tout plus vif, coups d'enclume, son magique à la fin). Elle **ne fabrique rien et
n'est reliée à rien** : pas de recettes, pas d'interface, pas de progression. Un clic droit fait exactement ce que fait
un clic sur les autres ateliers (le point d'accroche générique, rien par défaut) ; l'activité se déclenche par
commande (`/forge animer`) ou par l'API Java, pour l'usage que le serveur veut en faire avec son propre système.

Aucune génération naturelle, aucune entité pour l'animation, aucun vrai feu (rien ne brûle, aucun bloc n'est détruit),
compatible serveur dédié. Le mod doit être installé sur le serveur **et** les clients.

## Pose et retrait

- **Objet** : `medievalships:forge_divine`, onglet créatif **Ateliers** (après les huit ateliers), piles de 16 ;
  `/workshop give forge_divine [joueurs]` (ou `/tent give`, `/ship give`), `/give @p medievalships:forge_divine`.
- **Pose** : clic droit au sol avec l'objet. La **façade fait face au joueur** qui la pose. Comme les tentes, la place
  est vérifiée d'abord : toute l'emprise (tournée selon l'orientation, 13 x 7 blocs au sol, 10 de haut) doit être libre
  (air, herbes, fleurs, neige…) et le sol plein sous au moins 60 % de l'emprise ; sinon un message en rouge
  (« Pas assez de place pour la forge divine (13 x 7 blocs, 10 de haut) : Pierre en x y z. ») et rien n'est posé.
  Admin : `/workshop place forge_divine [x y z] [south|west|north|east]` (alias `/atelier`).
- **Lumière** : le bloc d'ancrage éclaire comme une balise (niveau 15) ; le feu, les colonnes, les lanternes, le
  cristal, l'auréole et la grille de lave sont dessinés en pleine lumière.
- **Collisions** : les boîtes du descripteur (`workshops/forge_divine.json`) : la plateforme se monte à pied (deux
  marches de 0,25 bloc), on est arrêté par le corps du fourneau, les colonnes, les établis, l'enclume, la presse ; rien
  sous les éléments suspendus (bannières, lanternes, chaînes).
- **Retrait** : casser le bloc d'ancrage (en créatif : rien ne tombe ; en survie : l'objet est rendu),
  `/tent remove [x y z]`, `/workshop remove [x y z]`. Il ne reste **aucun bloc, aucune collision, aucun bloc-entité,
  aucune entité** ; une activité en cours s'arrête avec la forge.

## Clic droit : le même circuit que les autres ateliers

Le clic se fait sur le **bloc d'ancrage** (comme pour tous les objets posés) : au pied du fourneau, au centre de la
façade, là où le contour de visée apparaît. Côté serveur, exactement comme pour les huit ateliers :

1. spectateur : rien ; au plus un usage toutes les 10 ticks par joueur ;
2. l'événement Fabric **`WorkshopUseCallback`** avec le métier **`forge_divine`** (un autre mod peut prendre la main) ;
3. sinon la commande configurée **`workshopCommands.forge_divine`** (dans `config/medievalships.json`, section
   `server`), exécutée comme le joueur, niveau de permission 2 ;
4. sinon le court message des ateliers : « Forge divine — aucune interface de fabrication n'est reliée ».

**Rien n'est configuré par défaut.** Exemple pour ouvrir votre propre menu :

```json
"server": {
  "workshopCommands": {
    "forge_divine": "function monserveur:forge/ouvrir"
  }
}
```

Voir aussi [ATELIERS.md](ATELIERS.md#relier-un-atelier-à-un-système-de-métiers).

## Animation, activité et effets

Le rendu est fait par le client à partir du bloc d'ancrage (un bloc-entité, aucune entité) :

- la partie fixe est un maillage « cuit » une fois (comme les tentes), découpé hors de la vue ; rien n'est dessiné
  au-delà de `tentRenderDistance` (64 blocs par défaut), les petits détails (os `detail`) au-delà de
  `tentDecorDistance` (32) ;
- les **engrenages** tournent lentement au repos et plus vite en activité (`gear_a_*` dans le sens horaire vu de face,
  `gear_b_*` dans l'autre sens), avec un changement d'allure progressif ;
- le **feu** et les **colonnes de chaleur** sont des animations image par image (4 images), plus rapides en activité ;
  des éléments ne s'allument **qu'en activité** (fourneau plus vif, colonnes plus brillantes, lumière dorée autour de
  la statue : os `craft_*`) ou seulement au repos (`idle_*`) ;
- **effets**, seulement si un joueur est à moins de **24 blocs** : étincelles et braises de temps en temps (enclume,
  fourneau), bouffée de vapeur des tuyaux de temps à autre, lueur sacrée autour de la statue ; tout est plus fréquent
  en activité. **Sons** espacés : crépitement du feu, léger bruit de machinerie, souffle de vapeur ; en activité, coups
  de marteau sur l'enclume avec une gerbe d'étincelles ; au début, un bruit d'outil ; à la fin, un son « magique »
  (balise + carillon d'améthyste) et une gerbe de lumière. Particules et sons vanilla uniquement.

**L'activité** est un simple état du bloc-entité : « au repos » ou « en activité jusqu'au tick N » (temps de jeu). Il est
**sauvegardé** (une activité en cours continue après un redémarrage du serveur, le temps de jeu étant arrêté pendant
que le serveur est éteint) et **synchronisé** aux clients, qui animent la forge. Une seule activité à la fois.

## Commandes (administrateurs)

Sans position, la forge la plus proche à moins de 48 blocs de la position de la commande ; une position peut être
n'importe quel bloc de la forge.

| commande | effet |
|---|---|
| `/forge animer [x y z] <secondes>` | met la forge en activité pendant 1 à 3600 s ; refusé si elle l'est déjà |
| `/forge arreter [x y z]` | termine l'activité maintenant |
| `/forge etat [x y z]` | au repos, ou en activité (temps restant, %) |

Exemples d'usage avec un système du serveur : une fonction de datapack qui fabrique un objet peut lancer
`execute positioned 100 64 200 run forge animer 10` pendant sa propre fabrication ; un PNJ capable d'exécuter une
commande peut faire de même (non testé avec un mod de PNJ précis : seules les commandes le sont).

## API Java (`fr.medievalships.api.DivineForgeApi`)

Côté serveur ; chaque méthode prend le bloc d'ancrage ou n'importe quel bloc de la forge.

```java
DivineForgeApi.startActivity(world, pos, 200);   // 10 s d'activité (false : pas de forge, ou déjà active)
DivineForgeApi.stopActivity(world, pos);         // termine maintenant
DivineForgeApi.isActive(world, pos);             // aussi côté client (copie synchronisée)
DivineForgeApi.remainingTicks(world, pos);
DivineForgeApi.find(world, pos);                 // le bloc-entité DivineForgeBlockEntity, ou null

DivineForgeApi.ACTIVITY_STARTED.register((world, pos, ticks) -> { /* ... */ });
DivineForgeApi.ACTIVITY_FINISHED.register((world, pos, stopped) -> {
    if (!stopped) MonSysteme.forgeTerminee(world, pos);   // false : son temps est écoulé
});
```

`startCrafting(world, pos, ticks)` est un synonyme de `startActivity`. `stopped` vaut `true` quand l'activité a été
arrêtée avant son terme (`/forge arreter`, `stopActivity`, forge retirée). Le bloc-entité est
`fr.medievalships.forge.DivineForgeBlockEntity` (type `medievalships:forge_divine`), l'état pur
`fr.medievalships.core.ForgeActivity`.

## Fichiers et contrat des modèles

- Descripteur `assets/medievalships/workshops/forge_divine.json` (format des ateliers) : `model`, `texture`, `extent`,
  `colliders`, `light` (forcée à 15 par le code), et **`extra_models`** :
  `[{"model": "models/entity/forge_divine_deco.bbmodel", "texture": "textures/entity/forge_divine_deco.png"}]` —
  modèles dessinés avec la même transformation que le modèle principal, chacun avec son atlas (le champ est général :
  tout objet posé peut en avoir). Le métier vaut `forge_divine` (l'id, faute de champ `profession`).
- Deux modèles, générés par `tools/forge/` : la **structure** (`models/entity/forge_divine.bbmodel` +
  `textures/entity/forge_divine.png`) et le **décor** (`forge_divine_deco.bbmodel` + `forge_divine_deco.png`).
- Os reconnus par le rendu (dans l'un ou l'autre modèle) : `gear_a_<n>` / `gear_b_<n>` (tournent autour de leur axe z
  local par leur pivot), `<nom>_f<n>` (animation image par image : `fire_f0..3`, `flow_l_f0..3`, `flow_r_f0..3`),
  `craft_*` (visibles en activité), `idle_*` (visibles au repos), `detail` (cachés au loin), cubes `glow*` (pleine
  lumière), os vides `fx_spark_*`, `fx_steam_*`, `fx_ember_*`, `fx_holy_*` (leur pivot = point d'émission des effets).
  Sans ces os, la forge est simplement dessinée immobile ; sans les points `fx_*`, les effets partent de points fixes
  (enclume, fourneau, tuyaux, statue). Un modèle absent n'est pas dessiné (journalisé), le jeu ne plante pas ; un
  descripteur absent est remplacé par l'enveloppe convenue (13 x 10 x 6).

## Tests

- **JUnit** (`DivineForgeTest`) : l'objet (famille des ateliers, métier `forge_divine`, avant l'artillerie dans
  `PROPS`, lumière 15, « posée »), le descripteur (enveloppe 13 x 10 x 6, colliders dans l'emprise, bord avant
  franchissable, rien sous les bannières, `extra_models`), le champ `extra_models` pour tout objet, le repli si le
  descripteur manque, les os du contrat dans les deux modèles (points `fx_*` dans la forge), l'axe d'un engrenage selon
  la rotation de son os ; la machine d'état (une activité à la fois, échéance, progression, arrêt, bornes, restauration
  après redémarrage) ; les flipbooks et engrenages en fonction du temps (images dans l'ordre, vitesses, changement
  d'allure sans saut, pause, retour en arrière) ; le rythme des effets.
- **En jeu** (`ForgeGameTest`, appelé par `ShipClientGameTest` en solo, après redémarrage et en serveur dédié ;
  `-PgametestOnly=forge` pour lui seul) : les deux modèles chargés avec leurs os, le refus faute de place, la pose
  orientée, le bloc-entité, la lumière 15, l'emprise, les collisions (corps du fourneau solide, rien sous les bannières,
  un joueur qui marche monte sur la plateforme et est arrêté), le clic avec une commande configurée puis sans (le
  message des ateliers, aucun écran), `/forge animer` (état vu par le client, fin toute seule après la durée, une
  activité à la fois), `/forge arreter` depuis n'importe quel bloc, la forge la plus proche, l'API et ses événements, le
  retrait par `/tent remove` pendant une activité et par un joueur en créatif (aucun bloc, collision, bloc-entité ni
  objet restant, côté serveur et client), une activité conservée après le redémarrage du monde (même tick de fin) ;
  captures au repos (face, 3/4, de près), en activité, de nuit, après redémarrage.

## Limites (honnêtes)

- La forge ne fabrique rien : c'est un décor animé et un point d'accroche (clic, commandes, API) pour le système du
  serveur.
- Une seule activité à la fois par forge ; pas de file d'attente.
- Le clic droit ne marche que sur le bloc d'ancrage (comme tous les objets posés du mod), pas sur le reste du modèle.
- Les effets (particules, sons) sont côté client et seulement à moins de 24 blocs ; sons vanilla, pas de son
  personnalisé.
- Non testé : de très nombreuses forges actives à la fois, l'usage depuis un mod de PNJ ou de métiers précis (seules les
  commandes et l'API le sont).
