import redis
from dynaconf import settings

class RedisService():
    redis_client = redis.StrictRedis(
      host=settings.get('REDIS_HOST'), 
      port=settings.get('REDIS_PORT'), 
      db=settings.get('REDIS_DB'), 
      decode_responses=True)
    
    def set(self, key, value):
        self.redis_client.set(key, value)
    
    def get(self, key):
        return self.redis_client.get(key)
    
    def exists(self, key):
        return self.redis_client.exists(key)
    
    def delete(self, key):
        self.redis_client.delete(key)
