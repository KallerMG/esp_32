# Autor: Roger da Silva Machado
# Codigo baseado na versao do: https://github.com/rdehuyss/micropython-ota-updater

import usocket
import os
import gc
import machine



class Ota_updater:
# Classe utilizada para realizar o download e update dos codigos com base no projeto privado do github 

    def __init__(self, github_repo, main_dir, module=''):
    # Metodo de inicializacao
    # @param github_repo: url do GitHub;
    # @param main_dir: pasta onde vao estar os codigos que serao atualizados;
    # @param headers: utilizado para usar projeto privado do GitHub.
        self.http_client = HttpClient()
        self.github_repo = github_repo.rstrip('/').replace('https://github.com', 'https://api.github.com/repos')
        self.main_dir = main_dir
        self.module = module.rstrip('/')

    def apply_pending_updates_if_available(self):
    # Metodo que verifica se tem atualizacao que ja foi baixada para realizar o update dos codigos

        try:
            # caso exista a pasta next eh porque foi baixado um codigo
            if 'next' in os.listdir(self.module):
                # caso exista um arquivo .version na pasta next eh apagado diretorio presente em self.main_dir
                # e o diretorio next vira main, assim eh realizado a atualizacao dos codigos
                if '.version' in os.listdir(self.modulepath('next')):
                    self.rmtree(self.modulepath(self.main_dir))
                    os.rename(self.modulepath('next'), self.modulepath(self.main_dir))
                    return True
                # caso nao exita o arquivo apaga o diretorio next
                else:
                    self.rmtree(self.modulepath('next'))
                    return False
            else:
                return False
        
        except Exception as e: 
            print("Deu erro no update via Ota: " + str(e))
            

            
    def download_updates_if_available(self):
    # Metodo que verifica se a versao do codigo no GitHub e mais nova que a que esta na esp
        try:
            # caso nao exista o diretorio presente em self.main_dir, o mesmo eh criado para evitar erros
            if(self.main_dir not in os.listdir()):
                os.mkdir(self.main_dir)
            current_version = self.get_version(self.modulepath(self.main_dir))#: busca a versao do codigo local
            latest_version = self.get_latest_version() #: busca a versao do codigo no projeto do GitHub
            
            # se a versao do GitHub eh mais nova eh entao realizado o download dos codigos 
            if latest_version > current_version:
                # caso ja exita um diretorio next o mesmo eh apagado
                if('next' in os.listdir()):
                    self.rmtree('next')
                os.mkdir(self.modulepath('next'))#: cria o diretorio next para conter os codigos novos
                self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)#: realiza o download dos codigos

                #cria o arquivo .version na pasta next com o numero da versao
                with open(self.modulepath('next/.version'), 'w') as versionfile:
                    versionfile.write(latest_version)
                    versionfile.close()
                return True
            return False
        # caso tenha dado algum erro na execucao eh gravado o erro no arquivo buffer no diretorio presente em self.main_dir
        except Exception as e: 
            print("Deu erro no download via Ota: " + str(e))
            # caso tenha criado a pasta next a mesma eh apagada
            if('next' in os.listdir()):
                self.rmtree('next')
                
    def rmtree(self, directory):
    # Metodo usado para apagar arquivos ou diretorios passados por parametro
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            if is_dir:
                self.rmtree(directory + '/' + entry[0])

            else:
                os.remove(directory + '/' + entry[0])

        os.rmdir(directory)

    def get_version(self, directory, version_file_name='.version'):
    # Metodo que verifica a versao atual do codigo, para isso ele le o numero da versao no arquivo .version no diretorio self.main_dir
        if version_file_name in os.listdir(directory):

            f = open(directory + '/' + version_file_name)
            version = f.read()
            f.close()
            return version
        return '0.0' # caso nao exita o arquivo retorna 0.0 para ser realizado o download da nova versao dos codigos

    def get_latest_version(self):
    # Metodo que busca a versao do ultimo release do projeto do GitHub
        latest_release = self.http_client.get(self.github_repo + '/releases/latest')
        version = latest_release.json()['tag_name']
        latest_release.close()
        return version

    def download_all_files(self, root_url, version):
    # Metodo que realiza o download dos codigos do projeto no GitHub e armazena-os no diretorio next 
        file_list = self.http_client.get(root_url + '?ref=refs/tags/' + version)
        for file in file_list.json():
            if file['type'] == 'file':
                download_url = file['download_url']
                download_path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                self.download_file(download_url.replace('refs/tags/', ''), download_path)
            elif file['type'] == 'dir':
                path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                os.mkdir(path)
                self.download_all_files(root_url + '/' + file['name'], version)

        file_list.close()

    def download_file(self, url, path):
    # Metodo que faz o donwload de cada arquivo
        with open(path, 'w') as outfile:
            try:
                response = self.http_client.get(url)
                outfile.write(response.text)
            finally:

                response.close()
                outfile.close()
                gc.collect()

    def modulepath(self, path):
        return self.module + '/' + path if self.module else path


class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = 'utf-8'
        self._cached = None


    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)


class HttpClient:

    def request(self, method, url, data=None, json=None, headers={}, stream=None):
        try:
            proto, dummy, host, path = url.split('/', 3)
        except ValueError:
            proto, dummy, host = url.split('/', 2)
            path = ''
        if proto == 'http:':
            port = 80
        elif proto == 'https:':
            import ussl
            port = 443
        else:
            raise ValueError('Unsupported protocol: ' + proto)

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == 'https:':
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b'%s /%s HTTP/1.0\r\n' % (method, path))
            if not 'Host' in headers:
                s.write(b'Host: %s\r\n' % host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                s.write(k)
                s.write(b': ')
                s.write(headers[k])
                s.write(b'\r\n')
            # add user agent
            s.write('User-Agent')
            s.write(b': ')
            s.write('MicroPython OTAUpdater')
            s.write(b'\r\n')
            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b'Content-Type: application/json\r\n')
            if data:
                s.write(b'Content-Length: %d\r\n' % len(data))
            s.write(b'\r\n')
            if data:
                s.write(data)

            l = s.readline()
            # print(l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ''
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = s.readline()
                if not l or l == b'\r\n':
                    break
                # print(l)
                if l.startswith(b'Transfer-Encoding:'):
                    if b'chunked' in l:
                        raise ValueError('Unsupported ' + l)
                elif l.startswith(b'Location:') and not 200 <= status <= 299:
                    raise NotImplementedError('Redirects not yet supported')
        except OSError:
            s.close()
            raise

        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        return resp

    def head(self, url, **kw):
        return self.request('HEAD', url, **kw)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def patch(self, url, **kw):
        return self.request('PATCH', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)
