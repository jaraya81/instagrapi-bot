from tinydb import TinyDB, Query
import unittest
import logging_r


class Static:
    TAGS = 'tags'
    MEDIA = 'media'
    TABLE_MEDIAS = 'medias'
    PK = 'pk'
    ID = 'id'


class MediaRepo:
    def __init__(self, path):
        self.log = logging_r.get_logger(__name__, **{
            "level": "INFO",
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
        })

        self.db = TinyDB(path, **{
            'indent': 4,
            'ensure_ascii': False,
            'encoding': 'utf8'
        })

    def get_medias_by_locations(self, locations):
        medias = []
        if locations is not None:
            for location in locations:
                medias.extend(
                    self.db.table(Static.TABLE_MEDIAS).search(
                        Query()['location']['pk'] == location))

        return medias

    def get_medias_by_hashtags(self, hashtags):
        import re

        medias = []
        if hashtags is not None:
            for hashtag in hashtags:
                medias.extend(
                    self.db.table(Static.TABLE_MEDIAS).search(
                        Query()['caption_text'].matches('[\\d\\D]*' + hashtag + ' [\\d\\D]*', re.IGNORECASE)))

        return medias

    def get_medias(self, locations=None, hashtags=None):
        medias = []
        medias.extend(self.get_medias_by_locations(locations))
        medias.extend(self.get_medias_by_hashtags(hashtags))
        return medias

    def identify_medias(self, medias):
        medias_to_add = []
        medias_to_update = []

        for media in medias:
            medias_repo = self.db.table(Static.TABLE_MEDIAS).search(
                Query()[Static.ID] == media[Static.ID])
            if len(medias_repo) == 0:
                medias_to_add.extend([media])
            else:
                medias_to_update.extend([media])

        return medias_to_add, medias_to_update

    def insert_medias(self, medias):

        medias_to_add, medias_to_update = self.identify_medias(medias)

        self.db.table(Static.TABLE_MEDIAS).insert_multiple(medias_to_add)
        self.log.info(f"added {len(medias_to_add)} new medias")
        for media in medias_to_update:
            self.db.table(Static.TABLE_MEDIAS).upsert(media, Query()[Static.ID] == media[Static.ID])
        self.log.info(f"updated {len(medias_to_update)} medias")


class Tests(unittest.TestCase):
    def test_get_medias(self):
        media_repo = MediaRepo('repo_test.json')
        media_repo.insert_medias([{
            'id': 'id1',
            'caption_text': '#vitacura es una comuna de Chile'
        }])
        medias = media_repo.get_medias(hashtags=['vitacura'])
        self.assertEqual(1, len(medias))
        medias = media_repo.get_medias(hashtags=['providencia'])
        self.assertEqual(0, len(medias))

    def test_update_media(self):
        media_repo = MediaRepo('repo_test.json')
        media_repo.insert_medias([{
            'id': 'id2',
            'caption_text': '#santiago es la capital de Chile'

        }])
        medias = media_repo.get_medias(hashtags=['santiago'])
        self.assertEqual(1, len(medias))
        medias = media_repo.get_medias(hashtags=['lala'])
        self.assertEqual(0, len(medias))

    def test_get_medias_by_locations(self):
        media_repo = MediaRepo('repo_test.json')
        media_insert = {
            'id': 'id003',
            'location': {
                'pk': 1234
            }
        }

        media_repo.db.table(Static.TABLE_MEDIAS).upsert(media_insert, Query()[Static.ID] == media_insert[
            Static.ID])

        medias = media_repo.get_medias_by_locations([1234])
        self.assertEqual(1, len(medias))
        medias = media_repo.get_medias_by_locations([123])
        self.assertEqual(0, len(medias))

    def test_get_medias_by_hashtag(self):
        media_repo = MediaRepo('repo_test.json')
        media_insert = {
            'id': 'id004',
            'caption_text': 'Hola acá seguimos en jaja#soledad y #Ciudadbolivar '
        }

        media_repo.db.table(Static.TABLE_MEDIAS).upsert(media_insert, Query()[Static.ID] == media_insert[
            Static.ID])

        medias = media_repo.get_medias_by_hashtags(['ciudadbolivar'])
        self.assertEqual(1, len(medias))
        medias = media_repo.get_medias_by_hashtags(['ciudad'])
        self.assertEqual(0, len(medias))
