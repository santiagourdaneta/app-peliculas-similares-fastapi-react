# La dirección secreta para ir a tu almacén MySQL
# config.py
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/recomendacion_db"

# Hash de la contraseña "admin". ESTE DEBE SER EL HASH REAL GENERADO.
ADMIN_PASSWORD_HASH = "$2a$12$IWRM.y/cWqOiKZiN5BKzse4urT3S55jyMeLQJTNXAfg2pZhya4XFu"

# Clave secreta para firmar los tokens de acceso (JWT).
# ¡Cámbiala por una cadena de texto larga y aleatoria!
SECRET_KEY = "$2a$12$qViZVikxOktKRXgTUha8QOHnhpDZZNN81MxcjUMypkxFwXkgfp9u."