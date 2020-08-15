# Autor: Roger da Silva Machado
import os
import utime

from code_download import *

try:
    c = Code_download()
    c.download_update()
    print("\n\nAgora vai comecar o codigo que foi baixado\n")
    utime.sleep(2)
    exec(open('./exemplo.py').read()) #: como ja esta no diretorio que foi baixado os codigos executa o exemplo.py
except Exception as e:
    print('ERRO: ' +str(e))  
    
finally:
    os.chdir('/') #: usado para voltar para o diretorio / apos a execucao do codigo da pasta








