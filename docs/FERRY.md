# Créer un ferry automatique

Exemple : un ferry fait l'aller-retour entre **Port A** et **Port B**, attend 5 minutes à chaque
port, et contourne une île en passant par deux points intermédiaires.

```
Port A ──► Point 1 ──► Point 2 ──► Port B
   ▲                                  │
   └──────────── (retour) ◄───────────┘
```

## 1. Préparer les ports

* Le navire mesure environ **22 × 5,5 blocs** et a un tirant d'eau de **2 blocs** : l'eau doit
  avoir au moins 2 blocs de profondeur sur tout le trajet et aux escales.
* Une escale est le point où se placera le **centre** du navire. Placez-la au milieu d'un
  bassin dégagé, **le long** du quai (à ~3,5 blocs du bord du quai), pas face à lui : le navire
  arrive dans l'axe de la route.
* Pour un aller-retour, le navire fait demi-tour sur place à l'escale (il pivote à la rame) :
  prévoyez un cercle d'eau libre d'environ **24 blocs de diamètre** autour de chaque port.
* Les quais hauts d'un bloc au-dessus de l'eau permettent d'enjamber le bastingage
  directement depuis le quai.

## 2. Enregistrer l'itinéraire

Placez-vous successivement à chaque point (en bateau vanilla, à la nage ou en vol) :

```
/ship route create ferry_ab pingpong
# au Port A, à l'endroit où le centre du navire doit s'arrêter :
/ship route addstop ferry_ab 300 Port A
# en mer, pour contourner l'île :
/ship route addpoint ferry_ab
/ship route addpoint ferry_ab
# au Port B :
/ship route addstop ferry_ab 300 Port B
/ship route show ferry_ab
```

`show` trace le chemin en particules : vérifiez qu'aucun segment ne coupe une côte.
Conseils :

* une ligne droite entre deux points doit rester en eau libre sur toute la largeur du navire ;
* dans les virages serrés, ajoutez un point au milieu de la courbe ;
* un point de passage n'a pas besoin d'être précis : le navire le contourne dans un rayon de
  7 blocs (`aiWaypointRadius`) et anticipe le virage suivant.

## 3. Mettre le navire en service

```
/ship spawn                   # au Port A, ou placez la galère avec l'objet
/ship name La Sirène
/ship captain add             # facultatif : un PNJ visible à la barre
/ship route start ferry_ab
```

Comme le navire est à moins de 16 blocs de l'escale « Port A », il commence **à quai** et attend
ses 300 secondes. Utilisez `/ship route depart` pour le faire partir tout de suite.

## 4. Ce qui se passe ensuite

1. Le navire attend au Port A. Les joueurs montent à bord (clic droit sur la coque ou en
   enjambant le bastingage depuis le quai) et s'assoient sur les bancs ou restent debout.
2. Annonces aux joueurs à bord et à moins de 40 blocs : départ dans 60 s, 30 s, 10 s, 5…1 s.
3. Le navire lève l'ancre, accélère progressivement et suit les points.
4. Il anticipe les virages, ralentit dans les virages serrés, évite les obstacles détectés
   devant lui (îlots, autres navires), et ne fonce jamais volontairement sur une côte.
5. À l'approche du Port B, il réduit sa vitesse pour s'arrêter au point exact.
6. « *La Sirène est arrivée à Port B. Départ dans 300 s.* » — les joueurs descendent.
7. Après 5 minutes, il repart dans l'autre sens.

## Chunks et redémarrages

* Un navire en pilote automatique **garde chargés les chunks** autour de lui et devant lui
  (`chunkLoadAutopilotShips`, rayon `chunkLoadRadius`) : le ferry continue de naviguer sans
  aucun joueur à proximité.
* Sa position est mémorisée toutes les 5 secondes. Au redémarrage du serveur, ses chunks sont
  rechargés et il **reprend là où il était** (même phase : en mer, à quai avec le temps
  d'attente restant…). Le navire n'est jamais recréé : il ne peut pas être dupliqué.
* Un joueur qui se déconnecte à bord est débarqué sur le pont avant la sauvegarde ; à sa
  reconnexion il est replacé sur le pont du navire, où que celui-ci soit.

## En cas de blocage

Si le navire n'avance plus vers son objectif pendant ~50 secondes :

* sur un **point de passage** : il l'abandonne et vise le point suivant ;
* sur une **escale** : il s'arrête, prévient les administrateurs en ligne (message rouge avec
  ses coordonnées) et réessaie toutes les 30 secondes.

Corrigez alors l'itinéraire (`removepoint` / `addpoint`) ou utilisez `/ship unstuck`.
La détection d'obstacles est **locale** (environ 36 blocs devant la proue) : elle contourne
îlots, rochers et navires, mais ne cherche pas de chemin à travers tout un archipel ; ce sont
vos points de passage qui définissent la route.

## Plusieurs ferries

Plusieurs navires peuvent suivre le même itinéraire (par exemple deux ferries partant de
chaque port). Les navires se détectent mutuellement comme obstacles et ne se traversent pas.
