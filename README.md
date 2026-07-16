# Site - Waltraud Blunk Corretora de Imóveis

Site com página pública de imóveis (busca por finalidade, tipo, cidade,
bairro e faixa de valor) e área de login para a corretora cadastrar imóveis
e fotos. Sem banco de dados externo — tudo é salvo em arquivos JSON dentro
da pasta `data/` e as fotos em `static/uploads/`.

## Personalizar nome, telefones, endereço etc.

Abra `app.py` e edite o dicionário `SITE` no topo do arquivo (nome da
imobiliária, telefones, WhatsApp, e-mail, endereço, CRECI e redes sociais).
Já vem preenchido com os dados da Waltraud Blunk:

- Telefone / WhatsApp / Plantão: (47) 99934-4115
- CRECI Nº 025676

Também dá para configurar isso por variáveis de ambiente (`SITE_NOME`,
`SITE_WHATSAPP`, etc.) se preferir não mexer no código, o que é útil ao
publicar no Render.

## Rodando no seu computador (VS Code)

1. Abra a pasta no VS Code.
2. No terminal do VS Code:
   ```
   python3 -m venv venv
   source venv/bin/activate        # no Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
3. Acesse http://localhost:5000

## Login da corretora

- Usuário: `corretora`
- Senha provisória: `mudar123`

**Troque essa senha antes de publicar o site.** Para gerar uma nova senha:

```
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA_NOVA'))"
```

Copie o resultado e cole no campo `senha_hash` do arquivo `data/usuarios.json`.

## Cadastrando imóveis

Depois de logar em `/login`, use "Área da Corretora" no menu para acessar o
painel (`/admin`), onde dá para cadastrar, editar e excluir imóveis, além de
enviar/remover fotos. Os imóveis de exemplo em `data/imoveis.json` podem ser
apagados pelo próprio painel.

## Publicando (Render, gratuito)

O Vercel não guarda arquivos entre acessos (é serverless), então fotos e
cadastros feitos pela corretora não ficariam salvos. Por isso o deploy aqui é
para o **Render**, que mantém um servidor ligado com disco persistente:

1. Suba esta pasta para um repositório no GitHub.
2. Em https://render.com, crie um "New Web Service" e conecte o repositório.
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Em "Environment", adicione a variável `SECRET_KEY` com um valor aleatório,
   e (opcional) as variáveis `SITE_NOME`, `SITE_TELEFONE_FIXO`,
   `SITE_WHATSAPP`, `SITE_WHATSAPP_EXIBICAO`, `SITE_PLANTAO`, `SITE_EMAIL`,
   `SITE_ENDERECO`, `SITE_CIDADE_UF`, `SITE_CRECI`, `SITE_FACEBOOK`,
   `SITE_INSTAGRAM`, `SITE_YOUTUBE`.
5. Em "Disks", adicione um disco persistente montado em `/opt/render/project/src/data`
   e outro em `/opt/render/project/src/static/uploads` — isso garante que os
   imóveis e fotos cadastrados pela corretora não se percam a cada deploy.
6. Clique em "Create Web Service".

## Estrutura

```
app.py                          -> aplicação Flask (rotas públicas e de admin)
data/imoveis.json               -> dados dos imóveis
data/usuarios.json              -> login da corretora
static/uploads/                 -> fotos enviadas (uma pasta por imóvel)
static/img/logo.jpeg            -> logo da imobiliária
static/css/style.css            -> visual do site
templates/base.html             -> layout base (cabeçalho, menu, rodapé, botão WhatsApp)
templates/index.html            -> página inicial com busca e listagem
templates/imovel.html           -> página de detalhes do imóvel
templates/login.html            -> login da corretora
templates/admin_dashboard.html  -> painel com lista de imóveis
templates/admin_form.html       -> formulário de cadastro/edição
```

## Sobre o visual

Paleta vinho + dourado, inspirada na identidade visual da logo (cabeçalho
com telefones e WhatsApp, menu, busca em destaque com filtros de finalidade/
tipo/cidade/bairro/valor, cards de imóveis com selo de Venda/Locação, rodapé
com endereço e CRECI, botão flutuante de WhatsApp). As cores estão nas
variáveis CSS no topo de `static/css/style.css`, então dá para ajustar
facilmente se quiser.
