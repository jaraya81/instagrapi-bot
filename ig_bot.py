#!/usr/bin/python

import threading


class Activity:
    WELCOME = 'welcome'
    FOLLOW = 'follow'
    UNFOLLOW = 'unfollow'


def welcome_new_followers():
    log.info('welcome_new_followers')
    followers = ig.filter_new_followers(ig.user_followers(ig.client.user_id, amount=50))
    if len(ig.get_followers()) != 0:
        max_by_execution = int(ig.random(parameters['welcome']['max_by_execution']))
        followers = followers[0:len(followers) if len(followers) < max_by_execution else max_by_execution]
        ig.insert_followers(followers)
        for follower in followers:
            ig.send_welcome(follower, parameters['welcome']['messages'])
            ig.sleep(40)
    else:
        ig.insert_followers(followers)


def update_medias():
    ig.update_medias_by_locations(
        parameters['location']['elements'],
        amount=parameters['location']['amount'],
        find_by_type='both'
    )
    ig.update_medias_by_hashtags(
        parameters['hashtag']['elements'],
        amount=parameters['hashtag']['amount'],
        find_by_type='both'
    )


def unfollow():
    to_unfollowing = ig.get_to_unfollowing()

    if len(to_unfollowing) > parameters['unfollow']['follows_to_start']:
        triple = parameters['unfollow']['max_by_execution'] * 10
        to_unfollowing = to_unfollowing[:len(to_unfollowing) if triple > len(
            to_unfollowing) else triple]

        to_unfollowing = Instagram.shuffle_and_trim(to_unfollowing, parameters['unfollow']['max_by_execution'])

        for idx, to_unfollow in enumerate(to_unfollowing):
            log.info(
                f"UNFOLLOW ({idx + 1}/{len(to_unfollowing)}): {to_unfollow[Static.USERNAME]} -> "
                f"{ig.unfollow(to_unfollow)}")


def follow():
    medias = []
    medias.extend(ig.media_repo.get_medias(locations=parameters['location']['elements'],
                                           hashtags=parameters['hashtag']['elements']))

    medias = ig.filter_media(medias,
                             like_count_min=parameters['filter_media']['like_count_min'],
                             like_count_max=parameters['filter_media']['like_count_max'],
                             comment_count_min=parameters['filter_media']['comment_count_min'],
                             comment_count_max=parameters['filter_media']['comment_count_max'],
                             used_to_follow=True,
                             days_ago_max=parameters['filter_media']['days_ago_max'] if 'days_ago_max' in
                                                                                        parameters[
                                                                                            'filter_media'] else None)

    if len(medias) < parameters['follow']['max_by_execution']:
        update_medias()
        medias.extend(ig.media_repo.get_medias(locations=parameters['location']['elements'],
                                               hashtags=parameters['hashtag']['elements']))

        medias = ig.filter_media(medias,
                                 like_count_min=parameters['filter_media']['like_count_min'],
                                 like_count_max=parameters['filter_media']['like_count_max'],
                                 comment_count_min=parameters['filter_media']['comment_count_min'],
                                 comment_count_max=parameters['filter_media']['comment_count_max'],
                                 used_to_follow=True)

    medias = Instagram.shuffle_and_trim(medias, parameters['follow']['max_by_execution'])

    for idx, media in enumerate(medias):
        log.info(
            f"FOLLOW ({idx + 1}/{len(medias)}): "
            f"{media[Static.USER][Static.USERNAME]} -> "
            f"{ig.follow(media[Static.USER])}")


def is_sleeping():
    import time
    result = time.localtime(time.time())
    return 1 < result.tm_hour < 8


def is_your_turn(probability):
    import random
    return random.random() < probability


def main():
    if is_sleeping():
        log.info("::: bot sleep :::")
        return
    log.info("Starting bot in thread %s" % threading.current_thread())

    if is_your_turn(parameters[Activity.WELCOME]['probability_of_execution']):
        welcome_new_followers()
    else:
        log.info(f"{Activity.WELCOME} it's not your turn")

    if is_your_turn(parameters[Activity.FOLLOW]['probability_of_execution']):
        follow()
    else:
        log.info(f"{Activity.FOLLOW} it's not your turn")

    if is_your_turn(parameters[Activity.UNFOLLOW]['probability_of_execution']):
        unfollow()
    else:
        log.info(f"{Activity.UNFOLLOW} it's not your turn")

    log.info("::: end bot :::")


def run_threaded(job_func):
    log.info("run_threaded")
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


def exec_bot():
    import schedule
    import time

    main()
    schedule.every(61).to(87).minutes.do(run_threaded, main)
    while 1:
        schedule.run_pending()
        time.sleep(1)


def get_path_user():
    import getopt
    import sys

    opt_list, args = getopt.getopt(sys.argv[1:], 'p:', ['--path'])

    path_user = ''
    for opt, arg in opt_list:
        if opt in ('-p', '--path'):
            path_user = arg

    if not path_user:
        raise Exception(f"The configuration path is required")

    return path_user


if __name__ == "__main__":
    from instagram import Instagram, Static

    ig = Instagram(get_path_user())
    parameters = ig.params
    log = ig.log
    exec_bot()
