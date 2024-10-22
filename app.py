from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, inspect
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base, joinedload
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, constr
from typing import Dict, List
import logging

# Configuration du logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration de la base de données
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:AApOdMZVPlhqIrcSjDRGrKGkGCwOhCWn@junction.proxy.rlwy.net:57289/railway"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Déclaration de base pour SQLAlchemy
Base = declarative_base()

# Modèles SQLAlchemy
class Categorie(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, index=True)
    url = Column(String)
    
    sous_categories = relationship("SousCategorie", back_populates="categorie")
    

class SousCategorie(Base):
    __tablename__ = "sous_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    url = Column(String)
    categorie_id = Column(Integer, ForeignKey("categories.id"))
    
    categorie = relationship("Categorie", back_populates="sous_categories")


class Langue(Base):
    __tablename__ = "langues"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, index=True)

# Dépendances pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialisation de l'application FastAPI
app = FastAPI()

# Monter le dossier static pour servir les fichiers
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route pour servir la page index.html
@app.get("/", response_class=HTMLResponse)
async def get_home():
    return FileResponse("static/index.html")

# Fonction pour créer dynamiquement une table en fonction de la catégorie
def create_category_table_if_not_exists(category_name: str):
    # Normalisation du nom de la table
    table_name = f"depo_{category_name.lower().replace(' ', '_')}"
    
    # Vérifie si la table existe, sinon la crée
    with engine.connect() as connection:
        if not inspect(connection).has_table(table_name):
            table = Table(
                table_name,
                Base.metadata,  # Utiliser Base.metadata
                Column("id", Integer, primary_key=True, autoincrement=True),  # Utiliser Integer pour l'ID
                Column("nom", String, nullable=False),
                Column("traduction", String, nullable=False),
                Column("langue", String, nullable=False)
            )
            # Crée la table
            Base.metadata.create_all(engine)
            return table
        else:
            return Table(table_name, Base.metadata, autoload_with=engine)

# Modèle de données reçu dans la requête
class TranslationData(BaseModel):
    categorie: str
    sous_categorie: str
    langue: str
    traduction: str

# Modèles Pydantic pour les entrées
class CategorieCreate(BaseModel):
    nom: constr(min_length=1, max_length=100)  # type: ignore
    url: constr(min_length=1, max_length=255)  # type: ignore

class SousCategorieCreate(BaseModel):
    nom: constr(min_length=1, max_length=100)  # type: ignore
    url: constr(min_length=1, max_length=255)  # type: ignore
    categorie_id: int

class LangueCreate(BaseModel):
    nom: constr(min_length=1, max_length=100)  # type: ignore

# Modèles Pydantic pour les réponses
class SousCategorieResponse(BaseModel):
    id: int
    nom: str
    url: str

class CategorieResponse(BaseModel):
    id: int
    nom: str
    url: str
    sous_categories: List[SousCategorieResponse]  # Ajout de ce champ

class LangueResponse(BaseModel):
    nom: str

class CategorieListResponse(BaseModel):
    categories: List[CategorieResponse]

class SousCategorieListResponse(BaseModel):
    sous_categories: Dict[str, List[SousCategorieResponse]]

class LangueListResponse(BaseModel):
    languages: List[LangueResponse]

# Route pour ajouter une catégorie
@app.post("/categorie/", response_model=CategorieResponse)
async def create_categorie(categorie: CategorieCreate, db: Session = Depends(get_db)):
    db_categorie = Categorie(nom=categorie.nom, url=categorie.url)
    db.add(db_categorie)
    db.commit()
    db.refresh(db_categorie)
    return CategorieResponse(id=db_categorie.id, nom=db_categorie.nom, url=db_categorie.url)

# Route pour ajouter une sous-catégorie
@app.post("/sous_categorie/", response_model=SousCategorieResponse)
async def create_sous_categorie(sous_categorie: SousCategorieCreate, db: Session = Depends(get_db)):
    if not db.query(Categorie).filter(Categorie.id == sous_categorie.categorie_id).first():
        raise HTTPException(status_code=400, detail="La catégorie associée n'existe pas.")
    
    db_sous_categorie = SousCategorie(nom=sous_categorie.nom, url=sous_categorie.url, categorie_id=sous_categorie.categorie_id)
    db.add(db_sous_categorie)
    db.commit()
    db.refresh(db_sous_categorie)
    return SousCategorieResponse(id=db_sous_categorie.id, nom=db_sous_categorie.nom, url=db_sous_categorie.url)

# Route pour ajouter une langue
@app.post("/langue/", response_model=LangueResponse)
async def create_langue(langue: LangueCreate, db: Session = Depends(get_db)):
    if db.query(Langue).filter(Langue.nom == langue.nom).first():
        raise HTTPException(status_code=400, detail="La langue existe déjà.")
    
    db_langue = Langue(nom=langue.nom)
    db.add(db_langue)
    db.commit()
    db.refresh(db_langue)
    return LangueResponse(nom=db_langue.nom)

# Route pour obtenir toutes les catégories avec leurs sous-catégories
@app.get("/categorie/", response_model=CategorieListResponse)
async def read_categories(db: Session = Depends(get_db)):
    categories = db.query(Categorie).options(joinedload(Categorie.sous_categories)).all()
    return CategorieListResponse(categories=[
        CategorieResponse(
            id=c.id,
            nom=c.nom,
            url=c.url,
            sous_categories=[SousCategorieResponse(id=sc.id, nom=sc.nom, url=sc.url) for sc in c.sous_categories]
        ) for c in categories
    ])

# Route pour obtenir toutes les langues
@app.get("/langue/", response_model=LangueListResponse)
async def read_languages(db: Session = Depends(get_db)):
    languages = db.query(Langue).all()
    return LangueListResponse(languages=[LangueResponse(nom=l.nom) for l in languages])

# Endpoint pour recevoir les données et les insérer dans la base de données
@app.post("/api/traduction/")
async def receive_translation(data: TranslationData, db: Session = Depends(get_db)):
    try:
        # Crée la table si elle n'existe pas encore
        table = create_category_table_if_not_exists(data.categorie)
        
        # Insertion des données dans la table correspondante
        insert_statement = table.insert().values(
            nom=data.sous_categorie,
            traduction=data.traduction,
            langue=data.langue
        )
        db.execute(insert_statement)
        db.commit()

        return {"message": "Données insérées avec succès."}
    except IntegrityError:
        db.rollback()
        logger.error("Erreur d'intégrité des données", exc_info=True)
        raise HTTPException(status_code=400, detail="Erreur d'intégrité des données.")
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur serveur: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
