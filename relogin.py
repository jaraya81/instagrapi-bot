from instagram import Instagram
import getopt
import sys
import logging_r

log = logging_r.get_logger(__name__, **{
    "level": "INFO",
    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
})

opt_list, args = getopt.getopt(sys.argv[1:], 'p:')

path = ''
for opt, arg in opt_list:
    if opt in ('-p', '--path'):
        path = arg

if not path:
    raise Exception(f'Path -p is required')


def get_user_path(user):
    return os.path.join(path, user.replace('@', '_'))


def relogin(user, password):
    client = Instagram.login(user, password)
    if not client.user_id:
        raise Exception('Error')

    path_user = get_user_path(user)

    Instagram.write_file(
        client.get_settings(),
        Instagram.get_credential_path(path_user))

    log.info(f"'{user}' relogin in '{path_user}'")


def input_credential():
    import getpass
    print("Relogin account...")
    while 1:
        user = input("Enter the Instagram username or email: ")
        if not user:
            continue
        if os.path.exists(get_user_path(user)):
            print(f'Configuration of "{user}" already exists, retry with another user')
            print()
            continue
        break

    while 1:
        p_1 = getpass.getpass(prompt='Enter the Instagram password: ')
        if not p_1:
            continue

        p_2 = getpass.getpass(prompt='Re-enter your Instagram password: ')
        if p_1 != p_2:
            print('Password does not match, please try again')
            print()
            continue
        break
    return user, p_1


def main():
    # to tests
    # user, password = (user_default, pass_default)

    user, password = input_credential()
    relogin(user, password)


if __name__ == "__main__":
    import os

    main()
