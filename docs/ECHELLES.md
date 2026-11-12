# Échelles de coupée (1.30.0)

Chaque navire qui flotte avec un pont au-dessus de l'eau porte des échelles sur ses deux flancs, pour qu'un joueur
tombé à l'eau puisse remonter à bord : galère, galion, vaisseau de guerre, galère médiévale, bateau à roue, voilier
elfique, Nautilus (en surface, jusqu'au pont du kiosque), Vieux Corsaire, frégate aux voiles bleues, sloop marchand,
navire royal au lion, navire forteresse, navire à vapeur à engrenages. Une par flanc sur les coques courtes, deux sur
les longues (demi-longueur ≥ 15 blocs). Pas d'échelle sur la chaloupe (on y monte depuis l'eau) ni sur les aéronefs :
aucun ne flotte sur l'eau (la jonque dragon s'arrête à 0,8 bloc au-dessus de la surface).

## Emplacements

Choisis sur les modèles (vues de côté texturées, mesure de la peau du modèle par bandes) à l'écart des sabords, des
avirons (entre deux avirons au milieu de la galère, là où le genou de l'aviron ne bouge pas), des tambours de roues,
des cadènes et caps de mouton, des boucliers et bannières du navire royal, des contreforts d'acier de la forteresse, de
la passerelle et de son paquet rangé, et des canots portés sur le pont (galion, vaisseau, Corsaire, sloop, Nautilus) :
voir la table `SideLadder.TABLE` et les emplacements dans `SideLadderTest.SPOTS`.

## Géométrie

* Repère du navire. Le profil de chaque échelle (distance de sa face intérieure à l'axe, en fonction de la hauteur) est
  le maximum courant, depuis le haut du pavois, de la coque de collision et de la peau du modèle (lisses, préceintes,
  chapeau de pavois) : l'échelle repose sur le pavois et les préceintes et pend droit là où la coque rentre sous elle,
  comme une vraie échelle de coupée. Elle ne rentre jamais vers l'intérieur en descendant : un grimpeur plaqué contre
  elle ne bute jamais sous un surplomb. En plan elle suit la ligne de la coque (pente dX/dz).
* Le bas est calculé à l'exécution : 1,6 bloc sous la ligne de flottaison du type (`WATERLINE_Y`), donc il suit un
  changement de flottaison.
* `SideLadderTest#main` mesure les profils sur les modèles et les coques de collision et imprime la table ; le test
  vérifie que la table correspond toujours aux modèles.

## Grimper

* `LivingEntity#isClimbing` (mixin, client et serveur) : la même zone pure (`SideLadder.climbing`) des deux côtés, donc la
  prédiction du client et le serveur s'accordent. Comme une échelle vanilla : avancer ou sauter pour monter, s'accroupir
  pour rester, chute lente, pas de dégâts de chute ; dans l'eau, avancer contre l'échelle suffit.
* Une dalle de collision (`SideLadder.collectBoxes`, ajoutée par `ShipCollisions` après la phase large de la coque) donne
  au grimpeur une face contre laquelle s'appuyer ; sous l'eau elle comble aussi l'espace sous les préceintes.
* En haut, la zone dépasse le pavois de 0,3 bloc et s'étend 0,6 bloc vers l'intérieur : le joueur enjambe le pavois et
  descend sur le pont.
* Navire en marche : le grimpeur est emporté avec la coque (client pour le joueur, serveur pour les mobs), et le serveur
  élargit la zone d'un joueur selon la vitesse et la rotation du navire (le client voit la coque quelques ticks en retard),
  ce qui remet aussi à zéro le compteur anti-vol.
* Les mobs grimpent aussi (inoffensif).

## Rendu

Maillage cuit une fois par type (`SideLadder.mesh`, atlas des passerelles, matériau assorti à la coque : bois, bois
sombre, bois usé, elfique, cuivre, acier), écrit par `MeshEmitter` comme le maillage statique des modèles ; montants,
barreaux tous les 0,3 bloc, deux crochets de fer sur le pavois. Non dessiné au-delà de 160 blocs.
