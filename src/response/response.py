from datetime import datetime


class Response:
    server = "python"
    codes = {
        200: '200 OK',
        404: '404 Not Found',
        405: '405 Method Not Allowed',
        403: '403 Forbidden',
    }
    ENDL = '\r\n'
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.swf': 'application/x-shockwave-flash',
        '.txt': 'text/txt',
        'default': 'text/plain'
    }
    allowed_methods = ["GET", "HEAD"]

    def __init__(self, status=200, content_length=None, connection="close", f_type=".html", data=b"Hello there", filename=""):
        self._status = self.codes[200] if status not in self.codes.keys() else self.codes[status]
        self._date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        self._content_length = content_length
        self._connection = connection
        self.filename = filename
        try:
            self._content_type = self.content_types[f_type]
        except KeyError:
            self._content_type = self.content_types['default']
        self._data = data
        # if status == 200:
        #     f = self._filename
        #     i = f.rfind(".")
        #     if i != -1:
        #         file_type = f[i:]
        #         self._content_type = self.content_types[file_type]

    def __str__(self):
        return str(self.__dict__)

    def _response_tml(self):
        response_tmpl = 'HTTP/1.1 {status}{ENDL}' \
                        'Server: {server}{ENDL}' \
                        'Date: {date}{ENDL}'
        if self._status == self.codes[200]:
            response_tmpl += 'Content-Length: {length}{ENDL}' \
                             'Content-Type: {type}{ENDL}{ENDL}'
        # response_tmpl += self._data.decode('utf-8')
        return response_tmpl

    def write_data(self, data):
        if isinstance(data, bytes):
            self._date += data
        elif isinstance(data, str):
            self._data += data.encode('utf-8')

    @property
    def header(self):
        # if self._status not in self.codes.items():
        #     return None
        tmpl = self._response_tml()
        # print(self.__dict__)
        return tmpl.format(status=self._status, server=self.server,
                           date=self._date, length=self._content_length,
                           type=self._content_type, ENDL=self.ENDL).encode("utf-8")


if __name__ == "__main__":
    print(Response(status=200, filename="js.js").header)
