# Deploy no PythonAnywhere

## 1. Criar o banco MySQL

No painel do PythonAnywhere, abra **Databases** e crie um banco MySQL. Anote o usuário, a senha, o nome completo do banco e o host MySQL, normalmente `SEU_USUARIO.mysql.pythonanywhere-services.com`.

Use exatamente os valores exibidos no painel.

## 2. Clonar e preparar o ambiente

No console Bash do PythonAnywhere:

```bash
git clone URL_DO_SEU_REPOSITORIO
cd CalendarioMecenato
git switch deploy/pythonanywhere
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se a branch ainda não estiver no remoto, publique-a antes:

```bash
git push -u origin deploy/pythonanywhere
```

## 3. Configurar variáveis secretas

Crie um arquivo `.env` na raiz do projeto. Ele não deve ser commitado:

```env
SECRET_KEY=gere-uma-chave-longa-e-aleatoria
DATABASE_URL=mysql+pymysql://USUARIO:SENHA@USUARIO.mysql.pythonanywhere-services.com/NOME_DO_BANCO
AUTO_CREATE_DB=0
SEED_DEMO_DATA=0
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@seudominio.com
ADMIN_PASSWORD=uma-senha-forte
```

Se a senha tiver caracteres especiais, faça URL-encode na senha dentro da URL ou configure `DATABASE_URL` pela área de variáveis do web app.

## 4. Criar tabelas e administrador

Com o ambiente virtual ativado:

```bash
python scripts/init_db.py
```

O script cria as tabelas e cria ou atualiza o usuário administrador indicado. Ele pode ser executado novamente sem duplicar esse usuário.

## 5. Criar o Web app

No painel **Web**:

1. Clique em **Add a new web app**.
2. Escolha **Manual configuration** e a mesma versão do Python da virtualenv.
3. Informe a virtualenv, por exemplo `/home/USUARIO/CalendarioMecenato/.venv`.
4. Informe o diretório raiz do projeto em **Code**.
5. Abra o arquivo WSGI e substitua o conteúdo por:

```python
import os
import sys

project_home = "/home/USUARIO/CalendarioMecenato"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ["SECRET_KEY"] = "use-a-mesma-chave-do-seu-env"
os.environ["DATABASE_URL"] = "mysql+pymysql://USUARIO:SENHA@USUARIO.mysql.pythonanywhere-services.com/NOME_DO_BANCO"
os.environ["AUTO_CREATE_DB"] = "0"
os.environ["SEED_DEMO_DATA"] = "0"

from wsgi import application
```

Para maior segurança, use a seção **Environment variables** do painel quando disponível e não deixe senhas em arquivo versionado.

6. Clique em **Reload** e abra a URL do PythonAnywhere.

## Atualizações futuras

```bash
cd ~/CalendarioMecenato
git pull origin deploy/pythonanywhere
source .venv/bin/activate
pip install -r requirements.txt
```

Depois, clique em **Reload** no painel Web. Para alterações de schema, execute o script apropriado antes do reload; o projeto ainda usa `db.create_all()` e não possui migrações Alembic.
