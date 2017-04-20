import os

# my config file.

rss_files_paths = ['/mnt/sda3/rss_files', 'C:\\Users\\lundgrel\\Downloads', 'C:\\Users\\leif\\Downloads']
rss_files_ext = ('.mp3', '.mp4', '.wav')
rss_files_webpath = '/filedownload'

def listen_port():

    penv = os.environ.get('PORT')
    if penv is not None:
        print('PORT env was set to ' + penv)
        return int(penv)
    else:
        print('PORT env was not set, defaulting to 5189')
        return 5189
