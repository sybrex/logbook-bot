from fabric.tasks import task


SYSTEMD_SERVICE = 'logbook-bot'
USERNAME = 'deployer'
PROJECT_PATH = '/srv/www/logbook-bot'
GIT_REPOSITORY = 'logbook-bot.github.com:sybrex/logbook-bot.git'
GIT_KEY = '~/.ssh/github-deployer'


@task
def install(c):
    """
    Install project
    pipenv run fab install --hosts ip
    """
    c.run(f'mkdir {PROJECT_PATH}')
    with c.cd(PROJECT_PATH):
        c.run(f'git clone {GIT_REPOSITORY} .')
        c.run('export PIPENV_VENV_IN_PROJECT="enabled" && pipenv install')


@task
def upload(c, local, remote):
    """
    Upload file
    pipenv run fab upload --local /path/to/local/file.txt --remote relative/path/to/file.txt --hosts ip
    """
    c.put(local, f'{PROJECT_PATH}/{remote}')


@task
def download(c, remote, local):
    """
    Download file
    pipenv run fab download --remote relative/path/to/file.txt --local /path/to/local/file.ini --hosts ip
    """
    c.get(f'{PROJECT_PATH}/{remote}', local)


@task
def deploy(c, branch='master', deps=True):
    """
    Deploy updates to server
    pipenv run fab deploy --branch master --deps --hosts ip
    """
    with c.cd(PROJECT_PATH):
        print('Update code')
        c.run(f'git fetch origin && git checkout {branch} && git pull origin {branch}')
        if deps:
            print('Installing dependencies')
            c.run('pipenv install')
            service(c, SYSTEMD_SERVICE, 'restart')


@task
def service(c, name="nginx", action="restart"):
    """
    System service status|start|stop|restart
    pipenv run fab service --name nginx --action stop --hosts ip
    """
    c.run(f'sudo service {name} {action}')

