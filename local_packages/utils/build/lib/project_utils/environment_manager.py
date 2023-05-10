
from dotenv import load_dotenv
import os

from project_utils.general import General

class Manager():

    def __init__(self) -> None:
        load_dotenv(General().configure_relative_file_path('.env', 10))


    def get_env_varaibles(self, *args):
        env_variables = {arg : os.getenv(arg) for arg in args}
        return env_variables


    def get_database_credentials(self, authenticator:str):
        '''
        authenticator : str - ('settings' OR 'postgres')
        '''
        development = os.getenv('DEVELOPMENT') 
        if development == 'True':
            credentials = {
                'host':os.getenv('DEVELOPMENT_HOST'),
                'dbname':os.getenv('DEVELOPMENT_DBNAME'),
                'user':os.getenv('DEVELOPMENT_USER'),
                'port':os.getenv('DEVELOPMENT_PORT'),
                'password':os.getenv('DEVELOPMENT_PASSWORD'),
            }
        else:
            credentials =  {
                'host':os.getenv('HEROKU_HOST'),
                'dbname':os.getenv('HEROKU_DBNAME'),
                'user':os.getenv('HEROKU_USER'),
                'port':os.getenv('HEROKU_PORT'),
                'password':os.getenv('HEROKU_PASSWORD'),
            }

        if authenticator == 'settings':
            db_name = credentials['dbname']
            del credentials['dbname']
            credentials['name'] = db_name

        return credentials
