import redis


class RedisService():
    redis_client = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True)

    def set(self, key, value):
        self.redis_client.set(key, value)

    def get(self, key):
        return self.redis_client.get(key)

    def exists(self, key):
        return self.redis_client.exists(key)

    def delete(self, key):
        self.redis_client.delete(key)
