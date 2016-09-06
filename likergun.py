#!/usr/bin/env python3

import requests
import time
import random
import argparse


class APIHelper:
    def __init__(self, token):
        self.token = token;

    def apiRequest(self, method, params = {}):
        params['access_token'] = self.token
        params['v'] = "5.37"
        res = requests.get("https://api.vk.com/method/" + method, params=params).json()
        while 'error' in res :
            if res['error']['error_code'] == 6:
                time.sleep(0.42)
                res = requests.get("https://api.vk.com/method/" + method, params=params).json()
            else:
                print(res['error']['error_msg'])
                break
        return res

    def wallGet(self, owner_id, count, offset):
        params = {
            'owner_id': owner_id,
            'count': count,
            'offset': offset,
        }
        return self.apiRequest("wall.get", params)

    def photosGet(self, owner_id, count, offset, no_saved):
        params = {
            'owner_id': owner_id,
            'count': count,
            'offset': offset,
            'extended': 1,
            'no_service_albums': no_saved
        }
        return self.apiRequest("photos.getAll", params)

    def marketGet(self, owner_id, count, offset):
        params = {
            'owner_id': owner_id,
            'count': count,
            'offset': offset,
            'extended': 1
        }
        return self.apiRequest("market.get", params)

    def addLike(self, owner_id, post_id, typee):
        params = {
            'owner_id': owner_id,
            'item_id': post_id,
            'type': typee
        }
        return self.apiRequest("likes.add", params)

    def addLilkeCaptha(self, owner_id, post_id, captcha_sid, captcha_key, typee):
        params = {
            'owner_id': owner_id,
            'item_id': post_id,
            'type': typee,
            'captcha_sid': captcha_sid,
            'captcha_key': captcha_key,
        }
        return self.apiRequest("likes.add", params)


class Liker:
    def __init__(self, helper, target, block_size=100, sleep_time=1, sleep_time_max=2):
        self.api = helper
        self.target = target
        self.block_size = block_size
        self.sleeptime = sleep_time
        self.sleeptimemax = sleep_time_max

    def _like_items(self, elements, it_type):
        random.shuffle(elements)
        while len(elements) > 0:
            post = elements.pop()
            post_id = post['id']
            if post['likes']['user_likes'] == 1:
                print(str(post_id) + " already liked, skipping")
                continue
            response = self.api.addLike(self.target, post['id'], it_type)
            if 'error' in response and response['error']['error_code'] == 14:
                print("OMG Captcha error on " + str(post['id']) + "!11")
                if captcha_enabled:
                    print(chr(7), end="")
                    print(response['error']['captcha_img'])
                    ans = input("enter captcha: ")
                    self.api.addLilkeCaptha(self.target, post['id'], response['error']['captcha_sid'], ans, it_type)
                else:
                    elements.append(post)
                    sleep = random.randint(30, 70)
                    print("sleeping " + str(sleep))
                    time.sleep(sleep)
                    continue
            elif 'error' in response and response['error']['error_code'] == 9:
                print("OMG FUCKING FLOOD CONTROL!11")
                elements = []
                return False
            elif 'error' in response:
                print('Unknown error, blya')
                return False
            print("Liked " + str(post['id']) + ", " + str(len(elements)) + " left")
            time.sleep(random.randint(self.sleeptime, self.sleeptimemax))
        return True

    def _get_count(self, getterf):
        return getterf(self.target, 1, 0)['response']['count']

    def _get_elems(self, getterf, block_size, offset):
        return getterf(self.target, block_size, offset)['response']['items']

    def _like(self, getterf, typee):
        offset = 0
        count = self._get_count(getterf)
        while count > 0:
            posts = self._get_elems(getterf, self.block_size, offset)
            res = self._like_items(posts, typee)
            count -= self.block_size
            offset += self.block_size
            if not res:
                count = -1
                return False
            print("New block")
        return True

    def like_wall(self):
        return self._like(self.api.wallGet, 'post')

    def like_market(self):
        return self._like(self.api.marketGet, 'market')

    def like_photos(self, no_service):
        if no_service:
            no_saved = 1
        else:
            no_saved = 0
        return self._like(lambda t,b,o : self.api.photosGet(t,b,o, no_saved), 'photo')


def parseargs():
    parser = argparse.ArgumentParser(description="""Likes some user or group in vk.com. 
    You should place your access token in tokenfile""")
    parser.add_argument('target', metavar='TARGET_ID', help='Id which you like', type=int)
    parser.add_argument('--tokenfile', default='tokenfile', required=False, 
        help='Name of file where your access token is')
    parser.add_argument('-w', '--wall', help='Like wall', action='store_true')
    parser.add_argument('-m', '--market', help='Like market (only for groups)', action='store_true')
    parser.add_argument('-p', '--photos', help='Like photos. Specify two times (-pp) to like service albums too',
         action='count')
    group = parser.add_argument_group('Like tuning', description="""If you set small time, you like faster, 
    but you can be banned with higher probability""")
    group.add_argument('--sleepmin', help='Minimum amount to sleep between likes', type=int, required=False, default=1)
    group.add_argument('--sleepmax', help='Maximum amount to sleep between likes', type=int, required=False, default=2)
    group.add_argument('--blocksize', help='Batch size', type=int, required=False, default=100)
    return parser.parse_args()

def get_token(tokenfile):
    with open(tokenfile) as f:
        return f.readline().rstrip()

def main():
    args = parseargs()
    token = get_token(args.tokenfile)
    helper = APIHelper(token)
    liker = Liker(helper, args.target, args.blocksize, args.sleepmin, args.sleepmax)
    not_failed = True
    if args.wall and not_failed:
        not_failed = liker.like_wall()
    if args.market and not_failed:
        not_failed = liker.like_market()
    if args.photos == 2 and not_failed:
        not_failed = liker.like_photos(no_service=False)
    elif args.photos == 1 and not_failed:
        not_failed = liker.like_photos(no_service=True)

if __name__ == '__main__':
    main()
    