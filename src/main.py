from server.server import *
from config.config import Config


@coro
def f(a, b, name):
    for i in range(10):
        # print("f loop")
        print(f"[step {i}]{name}: a={a}, b={b}")
        yield (a, b)


# cfg = Config()
# cfg.parse_config()
# loop = Loop()
# # c1 = f(1, 2, "c1")
# # c2 = f(3, 4, "c2")
# # loop.create_task(c1)
# # loop.create_task(c2)
# server = Server(loop=loop, port=cfg.port, static_dir=cfg.document_root)
# # server = Server(loop=loop, static_dir='/var/www/html')
# loop.create_task(server.start())
# loop.run()

# server = Server(loop=loop, static_dir='/var/www/html')
# server.start()

if __name__ == '__main__':

    cfg = Config()
    cfg.parse_config()
    forks = []
    d_loop = Loop()
    server = Server(loop=d_loop, port=cfg.port, static_dir=cfg.document_root)
    for x in range(0, int(cfg.cpu_limit)):
        process_id = os.fork()
        forks.append(process_id)
        if process_id == 0:
            loop = Loop()
            server._loop = loop
            print('PID:', os.getpid())
            # server = Server(loop=loop, static_dir='/var/www/html')
            loop.create_task(server.start())
            loop.run()

    for process_id in forks:
        os.waitpid(process_id, 0)
