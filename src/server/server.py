import socket
import select
from response.response import Response
from request.request import Request
from pathlib import Path
from os.path import getsize, abspath
import os


# class coro:
#     def __init__(self, func):
#         self._callable = func
#
#     def __call__(self, *args, **kwargs):
#         func = self._callable(*args, **kwargs)
#         func.send(None)
#         return func

def coro(f):
    def func(*args, **kwargs):
        c = f(*args, **kwargs)
        c.send(None)
        return c

    return func


class Loop:
    def __init__(self):
        self._tasks = []

    def create_task(self, coro):
        self._tasks.append(coro)

    def _step(self):
        for task in self._tasks:
            try:
                #print(f'task is {task}')
                next(task)
            except StopIteration:
                print(f'task complete {task}')
                self._tasks.remove(task)

    def run_until_complete(self):
        while self._tasks:
            self._step()

    def run(self):
        while True:
            self._step()


STEP = 1024


class Server:
    def __init__(self, loop, host='0.0.0.0', port=3000,
                 socket_opts=[socket.AF_INET, socket.SOCK_STREAM],
                 allowed_methods=["GET", "HEAD"], static_dir="/var/www/html"):
        self._host = host
        self._port = port
        self._static_dir = static_dir
        self._socket_opts = socket_opts
        self._loop: Loop = loop
        self._allowed_methods = allowed_methods
        self._tasks = {}

        server = socket.socket(*self._socket_opts)
        # epoll = select.epoll()
        # epoll.register(server.fileno(), select.EPOLLIN)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._host, self._port))
        server.listen(5)
        server.setblocking(0)
        server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_fd = server.fileno()
        self.server = server
        # self.epoll = epoll
        print("starting server at {}:{}".format(self._host, self._port))

    @coro
    def _read_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                yield
                chunk = f.read(STEP)
                # if b'<body>' in chunk:
                #     chunk = chunk.split(b'<body>')[0] + b'\r\n\r\n'
                yield chunk
                # while b'<body>' not in chunk and chunk:
                #     chunk = f.read(STEP)
                #     if b'<body>' in chunk:
                #         chunk = chunk.split(b'<body>')[0] + b'\r\n\r\n'
                #     yield chunk
                while chunk:
                    chunk = f.read(STEP)
                    yield chunk

        raise StopIteration


    def _handle_request(self, req: Request):
        uri = req.uri
        method = req.method
        filepath = self._static_dir + uri.split('?')[0]
        file = Path(filepath)
        status = ''
        if not file.exists():
            status = 404
        if file.is_dir() and filepath[-1:] == '/':
            filepath += 'index.html'
        elif file.is_dir():
            filepath += '/index.html'
        if req.method not in self._allowed_methods:
            status = 405
        i = filepath.rfind(".")

        if i != -1:
            file_type = filepath[i:]
        else:
            file_type = 'default'
        file_size = 0
        try:
            file_size = getsize(filepath)
            status = 200
        except FileNotFoundError:
            status = 404
            if filepath.split('/')[-1] == "index.html":
                status = 403
        if self._static_dir not in abspath(filepath):
            status = 403
        if method not in self._allowed_methods:
            status = 405
        print(f'check response {Response(status=status, content_length=file_size, f_type=file_type, filename=filepath)}')
        return Response(status=status, content_length=file_size, f_type=file_type, filename=filepath)

    @coro
    def read_request(self, new_con, epoll):
        con = new_con
        print(f'creating new con {con}')
        msg = b''
        yield
        while True:
            data = b''
            try:
                data = con.recv(STEP)
            except ConnectionResetError:
                con.close()
                raise StopIteration
            except socket.error:
                pass
            if data.strip():
                msg += data
            else:
                req = Request(msg.decode('utf-8'))
                print(f"msg: {msg} in con: {con.fileno()}\nreq: {req}")
                epoll.modify(con.fileno(), select.EPOLLOUT)
                new_task = self.send_response(con, epoll, req)
                self._tasks[con.fileno()] = new_task
                raise StopIteration

    @coro
    def send_response(self, new_con, epoll, req: Request):
        con = new_con
        if not req.is_valid:
            epoll.unregister(con.fileno())
            con.close()
            raise StopIteration
        resp = self._handle_request(req)
        print(f'req {req}')
        print(f"send resp: {resp.header} [{resp.filename}]")
        con.send(resp.header)
        if resp._status != resp.codes[200]:
            epoll.unregister(con.fileno())
            con.close()
            raise StopIteration
        rf = self._read_file(resp.filename)
        while True:
            try:
                chunk: bytes = next(rf)
                if req.method == "HEAD":
                    if b'<head>' not in chunk or b'</head>' not in chunk:
                        yield
                        continue
                    if b'<head>' in chunk:
                        chunk = chunk[chunk.find(b'<head>'):]
                    elif b'</head>' in chunk:
                        chunk = chunk[:chunk.find(b'</head>')]
            except StopIteration:
                break
            except FileNotFoundError:
                break
            try:
                con.send(chunk)
            except BrokenPipeError:
                break
            yield
        epoll.unregister(con.fileno())
        con.close()
        raise StopIteration


    @coro
    def start(self):
        # server = socket.socket(*self._socket_opts)
        # epoll = select.epoll()
        # epoll.register(server.fileno(), select.EPOLLIN)
        # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # server.bind((self._host, self._port))
        # server.listen(5)
        # server.setblocking(0)
        # server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # server_fd = server.fileno()
        # print("starting server at {}:{}".format(self._host, self._port))
        # epoll = self.epoll
        server = self.server
        epoll = select.epoll()
        epoll.register(server.fileno(), select.EPOLLIN)
        server_fd = server.fileno()
        try:
            while True:
                events = epoll.poll(0.1)
                # print(f"some events : {events}")
                for fileno, event in events:
                    if fileno == server_fd:
                        con, _ = server.accept()
                        con.setblocking(0)
                        epoll.register(con.fileno(), select.EPOLLIN)
                        # task = self.add_connection(con)
                        task = self.read_request(con, epoll)
                        # self._loop.create_task(task)
                        self._tasks[con.fileno()] = task
                    elif event & select.EPOLLIN:
                        try:
                            next(self._tasks[fileno])
                        except StopIteration:
                            pass
                    elif event & select.EPOLLOUT:
                        try:
                            next(self._tasks[fileno])
                        except StopIteration:
                            pass
                yield
        except KeyboardInterrupt:
            print("server stop")
        # except Exception as e:
        #     print(f'SOME EXCEPTION {e}', e)
        finally:
            epoll.unregister(server.fileno())
            epoll.close()
            server.close()

    def stop(self):
        pass


if __name__ == '__main__':
    loop = Loop()
    server = Server(loop, static_dir='/Users/kexibq/repos/technopark-highload')
    testdata = '''GET /Dockerfile'''
    r = Request(testdata)
    print(r)
    resp = server.handle_request(r)
    print(resp.header)
