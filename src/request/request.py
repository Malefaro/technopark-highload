ENDL = '\r\n'


class Request:
    allowed_methods = ["GET", "HEAD"]

    def __init__(self, data: str):
        request = data.split(ENDL, 1)[0]
        args = request.split(" ")
        if len(args) == 2:
            self._method = args[0]
            self._uri = args[1]
            self._protocol = None
        elif len(args) > 2:
            self._method = args[0]
            self._uri = args[1]
            self._protocol = args[2]
        else:
            self._method = None
            self._uri = None
            self._protocol = None

    def __str__(self):
        return str(self.__dict__)

    @property
    def is_valid(self):
        if self._method in self.allowed_methods and self._uri:
            return True
        return False

    @property
    def method(self):
        return self._method

    @property
    def uri(self):
        return self._uri

    @property
    def protocol(self):
        return self._protocol


if __name__ == "__main__":
    testdata = '''GET /Dockerfile'''
    r = Request(testdata)
    print(r)
    print(r.method)
    print(r.is_valid)

