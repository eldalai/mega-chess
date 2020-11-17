from datetime import timedelta
import os
import redis

REDIS_URL = os.environ.get('REDIS_URL')
redis_pool = redis.from_url(url=REDIS_URL, db=0)

for key in redis_pool.keys('board*'):
    print(key)
    # redis_pool.expire(key, timedelta(minutes=30))
for key in redis_pool.keys('turn*'):
    print(key)
    # redis_pool.expire(key, timedelta(minutes=30))
