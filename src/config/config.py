import multiprocessing


class Config:
    def __init__(self, cpu_limit=1,
                 port=80, root_dir='/var/www/html'):
        self.cpu_limit = cpu_limit
        self.port = port
        self.document_root = root_dir

    def parse_config(self):
        cfg = {}
        with open('/etc/httpd.conf') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                key, val = line.split()
                cfg[key] = val

            self.port = 80 if cfg.get('port') is None else int(cfg['port'])
            self.cpu_limit = 1 if cfg.get('cpu_limit') is None else int(cfg['cpu_limit'])
            self.document_root = '/var/www/html' if cfg.get('document_root') is None else cfg['document_root']

    def __str__(self):
        return str(self.__dict__)
