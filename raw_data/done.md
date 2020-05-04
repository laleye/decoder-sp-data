# Data collection from stackoverflow

**du mardi 28 Avril au jeudi 30 avril**

J'ai utilisé l'API Stack exchange pour récupérer des posts sur le site.
La difficulté est que le nombre de requêtes vers le site est limité par jour.
L'objectif est de recupérer des données java pour construire le dataset.

Les étapes d'extraction et de traitement des posts est le suivant:

## extraction des posts

J'ai récupérer les posts ayant plus de votes du 01/10/2010 au 29/04/2020 avec comme *java* comme
tag. Actuellement, seulement **55 pages** sont extraites. Les données sont enregistrées sous format json.

## traitement des posts

Un post est utilisé si son titre respecte les critères suvants:

> le titre doit commencer par *how* ou *what* ou terminer par *?*

> *java* doit être le premier élément de la liste des tags (ou un élément de la liste des tags, à tester)

> la question posée doit avoir eu des réponses

> une des réponses doit être une réponse acceptée

> la réponse acceptée doit contenir du code source

> le code source doit être du code java (using java parser)
    
## Données obtenues après traitement

> nombre total de posts parcourus (A): 11396

> nombre total de questions obtenues (B): 5239

> nombre de questions ayant une réponse acceptée et java comme premier tag (C): 4482

> nombre de questions ayant du code source dans la réponse acceptée (D): 2284

> nombre de questions ayant du code source java dans la réponse acceptée (E): 1058

> nombre d'exemples (text/snippet) après traitement dans le dataset (F): **1058**

## Recap

From stackoverflow: **1058 text/snippet**

From conala dataset: **330 text/snippet**
