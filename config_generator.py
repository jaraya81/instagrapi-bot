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


def generate_params(user):
    return {
        'username': user,
        'media_repo': 'media_repo.json',
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
        },
        'filter_media': {
            'like_count_min': 0,
            'like_count_max': 100,
            'comment_count_min': 0,
            'comment_count_max': 100,
            'days_ago_max': 60
        },
        'hashtag': {
            'amount': 27,
            'elements': ['ñuñoa',
                         'santiagodechile',
                         'lascondes',
                         'providencia'],
        },
        'location': {
            'amount': 27,
            'elements': ['112371848779363',
                         '152321618753643',
                         '223624443',
                         '427386520',
                         '237095835',
                         '213951068671822',
                         '214074940'],
        },
        'welcome': {
            'probability_of_execution': Instagram.random(0.7, 0.1),
            'max_by_execution': int(Instagram.random(3, 1)),
            'messages': ['Hi @$username, thanks for following me 😀👍',
                         'Hello @$username, nice to meet you. Anytime you want you can look at my profile 🙋',
                         'Hello @$full_name welcome to my world']
        },
        'like_comments': {
            'probability_of_execution': Instagram.random(0.7, 0.1),
            'max_medias_by_execution': int(Instagram.random(2, 1)),
            'max_likes_by_execution': int(Instagram.random(3, 1)),
        },
        'follow': {
            'probability_of_execution': Instagram.random(0.7, 0.1),
            'max_by_execution': int(Instagram.random(8, 1)),
        },
        'unfollow': {
            'probability_of_execution': Instagram.random(0.5, 0.1),
            'max_by_execution': int(Instagram.random(3, 1)),
            'follows_to_start': int(Instagram.random(200, 50)),
        }

    }


def generate_config_file(user, password):
    params = generate_params(user)
    client = Instagram.login(user, password)
    if not client.user_id:
        raise Exception('Error')

    path_user = get_user_path(user)

    Instagram.write_file(params, Instagram.get_config_path(path_user))
    Instagram.write_file(
        client.get_settings(),
        Instagram.get_credential_path(path_user))

    log.info(f"Pedro '{user}' created at '{path_user}'")


def input_credential():
    import getpass
    print("Creating a new account...")
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

    generate_config_file(user, password)


if __name__ == "__main__":
    import os

    main()
