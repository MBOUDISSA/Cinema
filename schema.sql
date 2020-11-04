DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id_user INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE film (
  id_film INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  realisateur TEXT NOT NULL,
  date_sortie DATE NOT NULL,
  synopsis TEXT NOT NULL,

  FOREIGN KEY (author_id) REFERENCES user (id_user)
);

INSERT INTO film(id_film,author_id,created,title,realisateur,date_sortie,synopsis)
VALUES(1,1,CURRENT_TIMESTAMP,"Le seigneur des anneaux","Stephen King",2001-12-19,"Un jeune et timide `Hobbit', Frodon Sacquet, hérite d'un anneau magique. Bien loin d'être une simple babiole, il s'agit d'un instrument de pouvoir absolu qui permettrait à Sauron, le `Seigneur des ténèbres', de régner sur la `Terre du Milieu' et de réduire en esclavage ses peuples. Frodon doit parvenir jusqu'à la `Crevasse du Destin' pour détruire l'anneau.");

INSERT INTO film(id_film,author_id,created,title,realisateur,date_sortie,synopsis)
VALUES(1,1,CURRENT_TIMESTAMP,"Harry Potter","Chris Columbus",2001-12-5,"Orphelin, le jeune Harry Potter peut enfin quitter ses tyranniques oncle et tante Dursley lorsqu'un curieux messager lui révèle qu'il est un sorcier. À 11 ans, Harry va enfin pouvoir intégrer la légendaire école de sorcellerie de Poudlard, y trouver une famille digne de ce nom et des amis, développer ses dons, et préparer son glorieux avenir.");

INSERT INTO user(id,username,password)
VALUES(1,Colin,bonjour)