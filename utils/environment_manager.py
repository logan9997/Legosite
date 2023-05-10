
from dotenv import load_dotenv
import os

class Manager():

    load_dotenv('.env')

    def get_env_varaibles(self, *args):
        env_variables = {arg : os.getenv(arg) for arg in args}
        return env_variables
    
    def get_database_credentials(self):
        development = os.getenv('DEVELOPMENT') 
        if development == 'True':
            return {
                'HOST':os.getenv('DEVELOPMENT_HOST'),
                'DBNAME':os.getenv('DEVELOPMENT_DBNAME'),
                'USER':os.getenv('DEVELOPMENT_USER'),
                'PORT':os.getenv('DEVELOPMENT_PORT'),
                'PASSWORD':os.getenv('DEVELOPMENT_PASSWORD'),
            }
        return {
            'HOST':os.getenv('HEROKU_HOST'),
            'DBNAME':os.getenv('HEROKU_DBNAME'),
            'USER':os.getenv('HEROKU_USER'),
            'PORT':os.getenv('HEROKU_PORT'),
            'PASSWORD':os.getenv('HEROKU_PASSWORD'),
        }
    
