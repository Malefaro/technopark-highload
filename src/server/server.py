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
                print(f'task is {task}')
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


STEP = 8

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

    @coro
    def _read_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                chunk = f.read(STEP)
                yield chunk
                while chunk:
                    chunk = f.read(STEP)
                    yield chunk
        raise StopIteration

    @coro
    def write_answer(self, con, req: Request):
        resp = self._handle_request(req)
        con.send(resp.header)
        rf = self._read_file(resp.filename)
        while True:
            try:
                chunk = next(rf)
            except StopIteration:
                break
            except FileNotFoundError:
                break
            con.send(chunk)
            yield
        con.close()
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
        if self._static_dir not in abspath(filepath):
            status = 403
        return Response(status=status, content_length=file_size, f_type=file_type, filename=filepath)




    @coro
    def add_connection(self, new_con):# server: socket.socket, epoll):
        # con, _ = server.accept()
        # con.setblocking(0)
        # print(f'add conn {con}')
        # epoll.register(con.fileno(), select.EPOLLIN)
        con = new_con
        print(f"add new conn {con}")
        yield
        print(f"afet yield {con}")
        msg = b''
        while True:
            data = b''
            try:
                print("BEFORE DATA", con)
                try:
                    data = con.recv(STEP)
                except socket.error as e:
                    print(f'catch error in add_connection {e}')
                    yield
                    continue
                print(f"DATA {data}")
            except ConnectionResetError:
                print("Closed!")
                con.close()
                raise StopIteration
            except Exception as e:
                print("EXCEPTION:", e)
            #print(f'data {data}, strip data {data.strip()}')
            if data.strip():
                #print(f'add data: {data}')
                msg += data
                yield
            else:
                print("STOP ITER")
                req = Request(msg.decode('utf-8'))
                print(msg)
                print(req)
                self._loop.create_task(self.write_answer(con, req))
                raise StopIteration

    @coro
    def start(self):
        server = socket.socket(*self._socket_opts)
        epoll = select.epoll()
        epoll.register(server.fileno(), select.EPOLLIN)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._host, self._port))
        server.listen(5)
        server.setblocking(0)
        server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_fd = server.fileno()
        print("starting server at {}:{}".format(self._host, self._port))
        try:
            while True:
                events = epoll.poll(0.1)
                print(f"some events : {events}")
                for fileno, event in events:
                    if fileno == server_fd:
                        print(f'i am catch first event {event}')
                        con, _ = server.accept()
                        con.setblocking(0)
                        epoll.register(con.fileno(), select.EPOLLIN)
                        self._loop.create_task(self.add_connection(con))
                        print(f'After adding task')
                    elif event & select.EPOLLIN:
                        print(f'I am catch event {event}')
                    elif event & select.EPOLLOUT:
                        pass
                yield
        except KeyboardInterrupt:
            print("server stop")
        except Exception as e:
            print(f'SOME EXCEPTION {e}', e)
        finally:
            server.close()
            epoll.unregister(server.fileno())
            epoll.close()

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