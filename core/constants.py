'''

Imports

'''

from pathlib import Path
from decouple import config, Csv


'''

Constants

'''

BASE_DIR = Path(__file__).parent.parent
GAME_DIR = fr'{BASE_DIR}\{Path(__file__).parent.name}'
COGS_DIR = fr'{BASE_DIR}\cogs'
DATA_DIR = fr'{BASE_DIR}\data'
SERV_DIR = fr'{DATA_DIR}\games'
LOGS_DIR = fr'{DATA_DIR}\logs'


TOKEN = config('TOKEN', default = None)
INVITE = config('INVITE', cast = str, default = 'http://google.com/')
PREFIXES = config('PREFIXES', cast = Csv(), default = []) 
