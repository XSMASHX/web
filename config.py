class Config:
    SECRET_KEY = 'Contraseña super secreta'


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'hotel_gestor'



config = {
    'development': DevelopmentConfig
}
