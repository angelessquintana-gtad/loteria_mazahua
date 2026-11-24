import os
import ssl
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv(Path(__file__).resolve().parent / ".env")

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "loteria_mazahua")

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query={"charset": "utf8mb4"},
)
opciones_conexion = {'connect_timeout': 10}
if os.getenv('DB_SSL', 'false').lower() == 'true':
    opciones_conexion['ssl'] = ssl.create_default_context()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800,
                       hide_parameters=True,
                       pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
                       max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '5')),
                       pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '15')), connect_args=opciones_conexion)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
