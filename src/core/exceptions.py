class RadarException(Exception):
    pass


class NewsNotFoundException(RadarException):
    pass


class DuplicateNewsException(RadarException):
    pass


class LLMException(RadarException):
    pass


class EmbeddingException(RadarException):
    pass


class DatabaseException(RadarException):
    pass


class CacheException(RadarException):
    pass

