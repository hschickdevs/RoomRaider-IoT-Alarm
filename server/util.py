from os import getcwd, mkdir, getenv
import ssl
from os.path import isdir, join, dirname, abspath
from dotenv import find_dotenv, load_dotenv


def get_logfile() -> str:
    """
    Get logfile path & create logs dir if it doesn't exist in the bot directory
    """
    # Create the logs directory and log file in the server/logs directory
    log_dir = join(dirname(abspath(__file__)), 'logs')
    if not isdir(log_dir):
        mkdir(log_dir)
    return join(log_dir, 'log.txt')


def handle_env():
    """
    Checks if the .env file exists in the repo root, and imports the variables if so.
    """
    try:
        # Adjust the search path to check the repo root for the .env file
        # .env file should be placed in the repo root
        envpath = find_dotenv(raise_error_if_not_found=True, usecwd=True, filename='.env')
        load_dotenv(dotenv_path=envpath)
    except:
        pass
    finally:
        mandatory_vars = ['TG_USERS', 'TG_BOT_TOKEN',
                        #   'WEBHOOK_HOST', 'WEBHOOK_PORT', 'WEBHOOK_LISTEN', 'WEBHOOK_SSL_CERT', 'WEBHOOK_SSL_PRIV',
                          'MONGODB_CONNECTION_STRING']
        for var in mandatory_vars:
            val = getenv(var)
            if val is None:
                raise ValueError(f"Missing environment variable: {var}")
            

def get_ssl_filepaths() -> tuple:
    """
    Load SSL certificates from the provided file paths.

    Parameters:
        - cert_file (str): Path to the certificate file.
        - key_file (str): Path to the private key file.

    Returns (tuple):
        - certificate filepath
        - key filepath
    """
    # Construct the paths to the certificate and key files
    current_dir = dirname(abspath(__file__))
    
    return join(current_dir, 'ssl', getenv("WEBHOOK_SSL_CERT")), join(current_dir, 'ssl', getenv("WEBHOOK_SSL_PRIV")) 
            

def load_command_template(command: str) -> str:
    """
    Loads the markdown template from the templates directory.
    
    Args:
        command (str): The name of the command template to load (without the .md extension)
    """
    with open(join(dirname(__file__), 'resources', f'{command}.md'), 'r', encoding='utf8', errors='ignore') as f:
        return f.read()
    
    
def pretty_join(items: list, conjunction: str ="and") -> str:
    """
    Join a list of strings with a specified conjunction before the last item.
    
    :param items: List of strings to join
    :param conjunction: The word to use before the last item (default: "and")
    :return: A single string with the items joined by commas and the conjunction
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + f' {conjunction} ' + items[-1]


class SafeFormat(object):
    def __init__(self, **kw):
        self.__dict = kw

    def __getattr__(self, name):
        if not name.startswith('__'):
            return self.__dict.get(name, '')


def escape_markdown(s: str) -> str:
    """Escape markdown reserved characters in a string."""
    for char in r"\`*_":
        # s = s.replace(char, "\\" + char)
        
        # Temporary patch ,just remove these characters for now.
        s = s.replace(char, "")
    return s

def get_commands() -> dict:
    """Fetches the commands from the templates for the help command"""
    commands = {}
    with open(join(dirname(abspath(__file__)), 'resources', 'commands.txt')) as f:
        for line in f.readlines():
            command, description = line.strip().split(' - ')
            commands[command] = description
                
    return commands