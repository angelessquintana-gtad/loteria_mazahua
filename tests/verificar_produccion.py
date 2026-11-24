"""Seguridad JWT en configuración de producción, con SQLite temporal y HTTPS simulado."""
from .verificar_acceso_jwt import main


if __name__ == '__main__':
    main(produccion=True)
