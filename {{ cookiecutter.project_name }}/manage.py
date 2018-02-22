from __future__ import print_function
import subprocess
import argparse
import os


def parse_ssh_config():
    ssh_config = os.path.expanduser('~') + '/.ssh/config'
    host_name = None
    remotes = {}
    with open(ssh_config, 'r') as f:
        for line in f:
            if line.startswith('Host') and '*' not in line:
                # starts of host config
                host_name = line.strip().split(' ')[1]
                remotes[host_name] = {}

            elif not line.strip():
                # find new line, change flag
                continue

            # else is config detail
            elif line.strip().startswith('Hostname'):
                remotes[host_name]['hostname'] = line.strip().split(' ')[1]

            elif line.strip().startswith('User'):
                remotes[host_name]['user'] = line.strip().split(' ')[1]

            else:
                continue
    return remotes


def get_project_name():
    return os.path.basename(os.getcwd())


def list_remote():
    remotes = parse_ssh_config()
    for name, remote in remotes.items():
        hostname = remote['hostname']
        user = remote['user']
        print(name, '{}@{}'.format(user, hostname))


def create_remote_dir(args):
    print('creating dir', args.folder, 'on remote machine', args.remote_name)
    project_name = get_project_name()
    folder = args.folder
    if folder[-1] != '/':
        folder = folder + '/'
    subprocess.check_call([
        'ssh', args.remote_name, 'mkdir -p ~/dev/{}/{}'.format(
            project_name, folder)
    ])


# push and pull retain the same rsync command
# the only difference is how the src and dest are put
# so use concept of local_folder and remote_folder
# and each can be src and dest depends on push or pull
def push_or_pull(args):
    folder = args.folder

    remote = parse_ssh_config()[args.remote_name]
    project_name = get_project_name()
    if args.create_dir:
        create_remote_dir(args, project_name)

    if args.dry_run:
        rsync_opt = ['-aznP']
    else:
        rsync_opt = ['-azP']

        rsync_base_command = ['rsync'] + rsync_opt
    local_folder = folder
    if local_folder[-1] != '/':
        local_folder = local_folder + '/'

    remote_folder = '{}@{}:~/dev/{}/{}'.format(
        remote['user'], remote['hostname'], project_name, folder)

    if remote_folder[-1] != '/':
        remote_folder = remote_folder + '/'

    return rsync_base_command, [local_folder], [remote_folder]


def execute_rsync(command):
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as err:
        if err.returncode == 12:
            print('possibly the directory is not exist on remote machine')
            print('create using --create-dir flag')


def push(args):
    base, local_folder, remote_folder = push_or_pull(args)
    rsync_command = base + local_folder + remote_folder
    execute_rsync(rsync_command)


def pull(args):
    base, local_folder, remote_folder = push_or_pull(args)
    rsync_command = base + remote_folder + local_folder
    execute_rsync(rsync_command)


def add_remote(args):
    # create git remote on local
    project_name = get_project_name()
    remote = parse_ssh_config()[args.remote_name]
    ssh_url_git = 'ssh://{}@{}/~/dev/repo/{}.git'.format(remote['user'], remote['hostname'], project_name)
    command = ['git', 'remote', 'add', args.remote_name, ssh_url_git]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as err:
        if err.returncode == 128:
            print('remote {} already exists, delete it first'.format(args.remote_name))
        else:
            print(err)
        exit(2)
    else:
        print('add local git remote')

    # create remote dev directory
    # create remote repo directory
    # create post hooks
    # everything will be handled by setup_remote.sh on remote machine

    base = ['ssh', args.remote_name]
    # check first if the script exists in remote
    command = '[ -f ~/bin/setup_remote.sh ]'
    return_code = subprocess.call(base + ['[ -f ~/bin/setup_remote.sh ]'])
    if return_code == 1:
        print('cannot find ~/bin/setup_remote.sh in remote machine')
        exit(1)

    # execute setup_remote.sh
    print('setup remote')
    command = base + ['~/bin/setup_remote.sh {}'.format(project_name)]
    try:
        output = subprocess.check_output(command)
    except subprocess.CalledProcessError as err:
        print(err)
    else:
        for line in output.decode().split('\n'):
            print(line)


def remote(args):
    if args.remote == 'list':
        list_remote()
    elif args.remote == 'add':
        add_remote(args)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='commands', dest='command')

# subparser for push
sp_push = subparsers.add_parser('push')
sp_push.add_argument('remote_name')
sp_push.add_argument('folder')
sp_push.add_argument('-n', '--dry-run', action='store_true')
sp_push.add_argument('-c', '--create-dir', action='store_true')

# subparser for pull
sp_pull = subparsers.add_parser('pull')
sp_pull.add_argument('remote_name')
sp_pull.add_argument('folder')
sp_pull.add_argument('-n', '--dry-run', action='store_true')
sp_pull.add_argument('-c', '--create-dir', action='store_true')

# subparser for remote
sp_rem = subparsers.add_parser('remote')
sp_rem.add_argument('remote', choices=['list', 'add'], help='list all remote machines, add git remote on local, create git repo, and create git working dir on remote')
sp_rem.add_argument('remote_name', nargs='?')

args = parser.parse_args()

if args.command == 'push':
    push(args)
elif args.command == 'pull':
    pull(args)
elif args.command == 'remote':
    remote(args)
else:
    print('no command', args.command)

# if args.command == 'push':
#     pass
# elif args.command

# if args.list_remote:
#     list_remote()
#     exit(0)
