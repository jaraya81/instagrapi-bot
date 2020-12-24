import json

import numpy
from instagrapi import Client
from instagrapi.types import Media, Location
from tinydb import TinyDB, Query
from repository_medias import MediaRepo


class Static:
    CONFIG_FILE = 'config.json'
    CREDENTIAL_FILE = 'credential.json'
    DB_FILE = 'db.json'

    USER = 'user'
    TABLE_MEDIA = 'media'
    TABLE_FOLLOWING = 'following'
    TABLE_FOLLOWERS = 'followers'
    TABLE_UNFOLLOWING = 'unfollowing'

    PK = 'pk'
    DB = 'db'
    LOGGING = 'logging'
    PATH = 'path'
    USERNAME = 'username'


class Instagram:

    def __init__(self, user_path):
        import logging_r
        self.params = Instagram.read_config(user_path)

        self.log = logging_r.get_logger(type(self).__name__, **self.params.pop(Static.LOGGING))
        self.username = self.params.pop(Static.USERNAME)
        self.log.info(f"Starting '{self.username}' Instagram")

        self.db = TinyDB(Instagram.get_db_path(user_path), **{
            'indent': 4,
            'ensure_ascii': False,
            'encoding': 'utf8'
        })
        self.media_repo = MediaRepo(self.params.pop('media_repo'))
        self.client = Client(Instagram.read_credential(user_path))

    @staticmethod
    def get_base_path(root_path, username):
        import os
        return os.path.join(root_path, username.replace('@', '_'))

    @staticmethod
    def transform_text(template, params):
        from string import Template
        t = Template(template)
        return t.safe_substitute(**params)

    def update_medias(self, hashtags_or_locations_pk,
                      amount=27,
                      media_type='hashtag',
                      find_by_type='top'):
        """
        Get medias by hashtags
        :param media_type: hashtag or location
        :param hashtags_or_locations_pk: hashtags or locations array
        :param amount:
        :param find_by_type: top, recent or both
        :return:
        """
        if media_type == 'hashtag':
            for hashtag in hashtags_or_locations_pk:
                if find_by_type is 'top' or find_by_type is 'both':
                    amount_top = 9 if amount > 9 else amount
                    self.media_repo.insert_medias(
                        list(map(lambda x: Instagram.map_media(x),
                                 self.client.hashtag_medias_top(name=hashtag,
                                                                amount=amount_top))))
                if find_by_type is 'recent' or find_by_type is 'both':
                    amount_recent = 27 if amount > 27 else amount
                    self.media_repo.insert_medias(
                        list(map(lambda x: Instagram.map_media(x),
                                 self.client.hashtag_medias_recent(
                                     name=hashtag,
                                     amount=amount_recent)
                                 )))
        elif media_type == 'location':
            for location_pk in hashtags_or_locations_pk:
                if find_by_type is 'top' or find_by_type is 'both':
                    amount_top = 9 if amount > 9 else amount
                    self.media_repo.insert_medias(
                        list(map(lambda x: Instagram.map_media(x),
                                 self.client.location_medias_top(location_pk=int(location_pk),
                                                                 amount=amount_top)
                                 )))

                if find_by_type is 'recent' or find_by_type is 'both':
                    amount_recent = 27 if amount > 27 else amount
                    self.media_repo.insert_medias(
                        list(map(lambda x: Instagram.map_media(x),
                                 self.client.location_medias_recent(
                                     location_pk=int(location_pk),
                                     amount=amount_recent)
                                 )))

    def update_medias_by_locations(self, locations_pk,
                                   amount,
                                   find_by_type):
        self.log.info(f"get medias by locations '{locations_pk}'")
        return self.update_medias(hashtags_or_locations_pk=locations_pk,
                                  amount=amount,
                                  media_type='location',
                                  find_by_type=find_by_type)

    def update_medias_by_hashtags(self, hashtags,
                                  amount,
                                  find_by_type):
        self.log.info(f"get medias by hashtags '{hashtags}'")
        return self.update_medias(hashtags_or_locations_pk=hashtags,
                                  amount=amount,
                                  media_type='hashtag',
                                  find_by_type=find_by_type)

    def unfollow(self, user):
        """
        Unfollow a user
        :param user:
        :return:
        """
        if user[Static.PK] not in map(lambda x: x[Static.PK], self.get_unfollowing()):
            result = self.client.user_unfollow(user[Static.PK])
            self.insert_unfollowing([user])
            self.sleep(30)
            return result
        else:
            self.log.info(f"You are already unfollowing {user[Static.USERNAME]}")

    def follow(self, user):
        """
        Follow a user
        :param user:
        :return:
        """
        if user[Static.PK] not in map(lambda x: x[Static.PK], self.get_following()):
            result = self.client.user_follow(user[Static.PK])
            self.insert_following([user])
            self.sleep(30)
            return result
        else:
            self.log.info(f"You are already following {user[Static.USERNAME]}")
            return True

    @staticmethod
    def login(username, password):
        client = Client()
        client.login(username, password)
        return client

    def filter_media(self, medias,
                     like_count_min=None,
                     like_count_max=None,
                     comment_count_min=None,
                     comment_count_max=None,
                     used_to_follow=False,
                     days_ago_max=None):
        """
        Filter medias
        :param days_ago_max:
        :param comment_count_max:
        :param like_count_max:
        :param medias: list of medias
        :param used_to_follow: the user of the media is not among the followers
        :param like_count_min: minimum number of likes of the media
        :param comment_count_min: minimum number of comments of the media
        :return:
        """

        from datetime import datetime, timedelta

        medias = list(filter(lambda x: not used_to_follow or (
                used_to_follow and x[Static.USER][Static.PK] not in map(lambda f: f[Static.PK], self.get_following())),
                             medias))
        medias = list(
            filter(lambda x: True if like_count_min is None else x['like_count'] >= like_count_min, medias))
        medias = list(
            filter(lambda x: True if like_count_max is None else x['like_count'] <= like_count_max, medias))
        medias = list(filter(lambda x: True if comment_count_min is None else x['comment_count'] >= comment_count_min,
                             medias))
        medias = list(filter(lambda x: True if comment_count_max is None else x['comment_count'] <= comment_count_max,
                             medias))
        if days_ago_max is not None:
            days_back = datetime.now() - timedelta(days=days_ago_max)
            medias = list(filter(
                lambda x: days_ago_max is None or x['taken_at'] is None or datetime.strptime(
                    x['taken_at'],
                    '%Y-%m-%d, %H:%M:%S'
                ) > days_back,
                medias))

        return list(dict([(media[Static.PK], media) for media in medias]).values())

    @staticmethod
    def write_file(data, path_file, default=None):
        """
        Write a file
        :param default:
        :param data:
        :param path_file:
        :return:
        """
        from pathlib import Path

        path_user = Path(path_file)
        path_user.parent.mkdir(exist_ok=True)

        with open(path_file, 'w', encoding='utf8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=True, default=default)

    @staticmethod
    def read_file(path_file, object_hook=None):
        """
        Read a file
        :param object_hook:
        :param path_file:
        :return:
        """
        with open(path_file, 'r', encoding='utf8') as json_file:
            return json.load(json_file, object_hook=object_hook)

    @staticmethod
    def random(number, scale=None):
        """
        Generate a random number by Normal Distribution
        :param number: a number
        :param scale: deviation, if None is 5% of number
        :return:
        """
        return numpy.random.normal(number,
                                   scale=number * 0.05 if scale is None else scale
                                   )

    def sleep(self, seconds):
        """
        Sleep
        :param seconds: media of seconds
        :return:
        """
        import time
        seconds = Instagram.random(seconds, seconds * 0.15)
        seconds = seconds if seconds > 0 else 0
        self.log.info(f'sleep {seconds} seconds...')
        time.sleep(seconds)

    @staticmethod
    def shuffle_and_trim(elements, size):
        """
        Shuffle and trim a list of element
        :param elements: list of element
        :param size: media size of trim
        :return:
        """
        import random as rnd
        size = int(Instagram.random(size, size * 0.2))
        size = 0 if size < 0 else size
        rnd.shuffle(elements)
        return elements[:len(elements) if len(elements) < size else size]

    @staticmethod
    def map_location(location: Location):
        if location is None:
            return None
        return {
            Static.PK: location.pk,
            'name': location.name,
            'address': location.address,
            'lng': location.lng,
            'lat': location.lat,
            'external_id': location.external_id,
            'external_id_source': location.external_id_source,
        }

    @staticmethod
    def map_media(media: Media):
        if media is None:
            return None
        return {
            Static.PK: media.pk,
            'id': media.id,
            'code': media.code,
            'taken_at': media.taken_at.strftime("%Y-%m-%d, %H:%M:%S"),
            'media_type': media.media_type,
            'product_type': media.product_type,
            Static.USER: Instagram.map_user(media.user),
            'comment_count': media.comment_count,
            'like_count': media.like_count,
            'caption_text': media.caption_text,
            'thumbnail_url': '' if media.thumbnail_url is None else str(media.thumbnail_url),
            'location': Instagram.map_location(media.location),
            'video_url': '' if media.video_url is None else str(media.video_url),
            'view_count': media.view_count,
            'video_duration': media.video_duration,
            'title': media.title
        }

    @staticmethod
    def map_user(user):
        if user is None:
            return None
        return {
            Static.PK: user.pk,
            Static.USERNAME: user.username,
            'full_name': user.full_name,
            'profile_pic_url': user.profile_pic_url,
            'is_private': user.is_private if 'is_private' in user else None,
            'is_verified': user.is_verified if 'is_verified' in user else None,
            'media_count': user.media_count if 'media_count' in user else None,
            'follower_count': user.follower_count if 'follower_count' in user else None,
            'following_count': user.following_count if 'following_count' in user else None,
            'biography': user.biography if 'biography' in user else None,
            'external_url': user.external_url if 'external_url' in user else None,
            'is_business': user.is_business if 'is_business' in user else None,

        }

    def insert_unfollowing(self, users):
        """
        Insert a unfollowing to db.json

        :param users:
        :return:
        """
        for user in users:
            if len(self.db.table(Static.TABLE_UNFOLLOWING).search(Query()[Static.PK] == user[Static.PK])) == 0:
                self.db.table(Static.TABLE_UNFOLLOWING).insert(user)

    def get_unfollowing(self):
        """
        Get all unfollowing
        :return:
        """
        return self.db.table(Static.TABLE_UNFOLLOWING).all()

    def insert_following(self, users):
        """
        Insert a following to db.json
        :param users:
        :return:
        """
        for user in users:
            if len(self.db.table(Static.TABLE_FOLLOWING).search(Query()[Static.PK] == user[Static.PK])) == 0:
                self.db.table(Static.TABLE_FOLLOWING).insert(user)

    def get_following(self):
        """
        Get all following from db.json
        :return:
        """
        return self.db.table(Static.TABLE_FOLLOWING).all()

    def get_to_unfollowing(self):
        return list(
            filter(
                lambda f: f[Static.PK] not in map(
                    lambda u: u[Static.PK],
                    self.get_unfollowing()
                ),
                self.get_following()
            )
        )

    def user_followers(self, user_id: int, use_cache: bool = False, amount: int = 0):
        return list(map(
            lambda x: Instagram.map_user(x),
            list(self.client.user_followers(
                user_id=user_id,
                use_cache=use_cache,
                amount=amount
            ).values())
        ))

    def filter_new_followers(self, users):
        users_to_add = []
        for user in users:
            if len(self.db.table(Static.TABLE_FOLLOWERS).search(
                    Query()[Static.PK] == user[Static.PK])) == 0:
                users_to_add.extend([user])
        return users_to_add

    def get_followers(self):
        return self.db.table(Static.TABLE_FOLLOWERS).all()

    def insert_followers(self, users):
        users_to_add = self.filter_new_followers(users)

        self.db.table(Static.TABLE_FOLLOWERS).insert_multiple(users_to_add)
        for user in users_to_add:
            self.log.info(f"added follower: {user[Static.PK]}: {user[Static.USERNAME]}")

    def send_welcome(self, user, texts: list):
        import random
        if len(texts) > 0:
            idx = random.randint(0, len(texts) - 1)
            text = texts[idx]
            self.log.info(f"Sending welcome message to {user[Static.USERNAME]}")
            self.client.direct_send(Instagram.transform_text(text, user), [user[Static.PK]])
        else:
            self.log.warning(f"Messages templates not configure")

    @classmethod
    def get_config_path(cls, user_path):
        import os
        return os.path.join(user_path, Static.CONFIG_FILE)

    @classmethod
    def read_config(cls, user_path):
        return Instagram.read_file(Instagram.get_config_path(user_path))

    @classmethod
    def get_db_path(cls, user_path):
        import os
        return os.path.join(user_path, Static.DB_FILE)

    @classmethod
    def get_credential_path(cls, user_path):
        import os
        return os.path.join(user_path, Static.CREDENTIAL_FILE)

    @classmethod
    def read_credential(cls, user_path):
        return Instagram.read_file(Instagram.get_credential_path(user_path))
