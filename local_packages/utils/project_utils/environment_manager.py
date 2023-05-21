
import os

from dotenv import load_dotenv
from project_utils.general import General
from config.config import ROOT_DIR


class Manager():

    def __init__(self) -> None:
        print(ROOT_DIR)
        load_dotenv(General().configure_relative_file_path('.env', 10))

    def get_env_varaibles(self, *args):
        env_variables = {arg: os.getenv(arg) for arg in args}
        return env_variables

    def get_database_credentials(self, authenticator: str):
        '''
        authenticator : str - ('settings' OR 'postgres')
        '''
        development = os.getenv('DEVELOPMENT')
        if development == 'True':
            credentials = {
                'host': os.getenv('DEVELOPMENT_HOST'),
                'dbname': os.getenv('DEVELOPMENT_DBNAME'),
                'user': os.getenv('DEVELOPMENT_USER'),
                'port': os.getenv('DEVELOPMENT_PORT'),
                'password': os.getenv('DEVELOPMENT_PASSWORD'),
            }
        else:
            credentials = {
                'host': os.getenv('HEROKU_HOST'),
                'dbname': os.getenv('HEROKU_DBNAME'),
                'user': os.getenv('HEROKU_USER'),
                'port': os.getenv('HEROKU_PORT'),
                'password': os.getenv('HEROKU_PASSWORD'),
            }

        if authenticator == 'settings':
            db_name = credentials['dbname']
            del credentials['dbname']
            credentials['name'] = db_name
            credentials = {k.upper(): v for k, v in credentials.items()}
        return credentials
