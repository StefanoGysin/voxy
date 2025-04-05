import sys
import os

# Adiciona o diretório pai (raiz do projeto, que contém 'backend') ao sys.path
# Isso permite que 'pytest' executado da raiz encontre 'backend' como módulo
# e que os testes dentro de 'backend' importem 'app' como módulo de nível superior.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root) 