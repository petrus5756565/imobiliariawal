import json
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMOVEIS_JSON = os.path.join(DATA_DIR, "imoveis.json")
USUARIOS_JSON = os.path.join(DATA_DIR, "usuarios.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB por requisição

# ---------- dados da imobiliária (edite aqui) ----------
SITE = {
    "nome": os.environ.get("SITE_NOME", "Waltraud Blunk Corretora de Imóveis"),
    "telefone_fixo": os.environ.get("SITE_TELEFONE_FIXO", "(47) 99934-4115"),
    "whatsapp": os.environ.get("SITE_WHATSAPP", "5547999344115"),
    "whatsapp_exibicao": os.environ.get("SITE_WHATSAPP_EXIBICAO", "(47) 99934-4115"),
    "plantao": os.environ.get("SITE_PLANTAO", "(47) 99934-4115"),
    "email": os.environ.get("SITE_EMAIL", "contato@waltraudblunk.com.br"),
    "endereco": os.environ.get("SITE_ENDERECO", "Rua Exemplo, 123 - Bairro"),
    "cidade_uf": os.environ.get("SITE_CIDADE_UF", "Joinville - SC"),
    "creci": os.environ.get("SITE_CRECI", "CRECI Nº 025676"),
    "facebook": os.environ.get("SITE_FACEBOOK", "#"),
    "instagram": os.environ.get("SITE_INSTAGRAM", "#"),
    "youtube": os.environ.get("SITE_YOUTUBE", "#"),
}


@app.context_processor
def injetar_site():
    return {"site": SITE}


@app.template_filter("moeda")
def moeda(valor):
    p = _preco_float(valor)
    if p is None:
        return "Consulte"
    texto = f"{p:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


# ---------- utilidades de dados ----------

def _ler_json(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def listar_imoveis():
    return _ler_json(IMOVEIS_JSON)


def salvar_imoveis(imoveis):
    _salvar_json(IMOVEIS_JSON, imoveis)


def obter_imovel(imovel_id):
    for im in listar_imoveis():
        if im["id"] == imovel_id:
            return im
    return None


def listar_usuarios():
    return _ler_json(USUARIOS_JSON)


def arquivo_permitido(nome):
    return "." in nome and nome.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------- autenticação ----------

def login_obrigatorio(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("usuario"):
            flash("Faça login para acessar essa página.", "erro")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorada


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        usuarios = listar_usuarios()
        encontrado = next((u for u in usuarios if u["usuario"] == usuario), None)
        if encontrado and check_password_hash(encontrado["senha_hash"], senha):
            session["usuario"] = usuario
            flash("Login realizado com sucesso.", "sucesso")
            return redirect(url_for("admin_dashboard"))
        flash("Usuário ou senha incorretos.", "erro")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    flash("Você saiu da área da corretora.", "sucesso")
    return redirect(url_for("index"))


# ---------- páginas públicas ----------

def _preco_float(valor):
    """Converte string de preço (ex: '350.000,00' ou '350000') em float."""
    if valor is None:
        return None
    limpo = str(valor).strip().replace("R$", "").strip()
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


@app.route("/")
def index():
    imoveis = listar_imoveis()

    finalidade = request.args.get("finalidade", "")
    tipo = request.args.get("tipo", "")
    cidade = request.args.get("cidade", "")
    bairro = request.args.get("bairro", "")
    valor_faixa = request.args.get("valor", "")

    if finalidade:
        imoveis = [i for i in imoveis if i.get("tipo") == finalidade]
    if tipo:
        imoveis = [i for i in imoveis if i.get("categoria", "") == tipo]
    if cidade:
        imoveis = [i for i in imoveis if cidade.lower() in i.get("cidade", "").lower()]
    if bairro:
        imoveis = [i for i in imoveis if bairro.lower() in i.get("bairro", "").lower()]
    if valor_faixa:
        faixas = {
            "ate230": (None, 230000),
            "230-350": (230000, 350000),
            "350-500": (350000, 500000),
            "500-750": (500000, 750000),
            "750-1000": (750000, 1000000),
            "1000-1500": (1000000, 1500000),
            "1500-3000": (1500000, 3000000),
            "acima3000": (3000000, None),
        }
        minimo, maximo = faixas.get(valor_faixa, (None, None))

        def dentro_da_faixa(im):
            p = _preco_float(im.get("preco"))
            if p is None:
                return False
            if minimo is not None and p < minimo:
                return False
            if maximo is not None and p > maximo:
                return False
            return True

        imoveis = [i for i in imoveis if dentro_da_faixa(i)]

    imoveis.sort(key=lambda i: i.get("criado_em", ""), reverse=True)
    todos = listar_imoveis()
    cidades = sorted({i.get("cidade", "") for i in todos if i.get("cidade")})
    bairros = sorted({i.get("bairro", "") for i in todos if i.get("bairro")})
    categorias = sorted({i.get("categoria", "") for i in todos if i.get("categoria")})
    return render_template("index.html", imoveis=imoveis, cidades=cidades, bairros=bairros,
                            categorias=categorias, finalidade_filtro=finalidade,
                            tipo_filtro=tipo, cidade_filtro=cidade, bairro_filtro=bairro,
                            valor_filtro=valor_faixa)


@app.route("/imovel/<imovel_id>")
def ver_imovel(imovel_id):
    imovel = obter_imovel(imovel_id)
    if not imovel:
        abort(404)
    return render_template("imovel.html", imovel=imovel)


# ---------- área da corretora ----------

@app.route("/admin")
@login_obrigatorio
def admin_dashboard():
    imoveis = listar_imoveis()
    imoveis.sort(key=lambda i: i.get("criado_em", ""), reverse=True)
    return render_template("admin_dashboard.html", imoveis=imoveis)


@app.route("/admin/novo", methods=["GET", "POST"])
@login_obrigatorio
def admin_novo_imovel():
    if request.method == "POST":
        imovel_id = uuid.uuid4().hex[:10]
        fotos_salvas = _processar_fotos(request.files.getlist("fotos"), imovel_id)

        novo = {
            "id": imovel_id,
            "titulo": request.form.get("titulo", "").strip(),
            "tipo": request.form.get("tipo", "venda"),
            "categoria": request.form.get("categoria", "").strip(),
            "preco": request.form.get("preco", "").strip(),
            "cidade": request.form.get("cidade", "").strip(),
            "bairro": request.form.get("bairro", "").strip(),
            "quartos": request.form.get("quartos", "").strip(),
            "suites": request.form.get("suites", "").strip(),
            "banheiros": request.form.get("banheiros", "").strip(),
            "vagas": request.form.get("vagas", "").strip(),
            "area_construida": request.form.get("area_construida", "").strip(),
            "area_terreno": request.form.get("area_terreno", "").strip(),
            "descricao": request.form.get("descricao", "").strip(),
            "whatsapp": request.form.get("whatsapp", "").strip(),
            "destaque": bool(request.form.get("destaque")),
            "fotos": fotos_salvas,
            "criado_em": datetime.utcnow().isoformat(),
        }

        imoveis = listar_imoveis()
        imoveis.append(novo)
        salvar_imoveis(imoveis)
        flash("Imóvel cadastrado com sucesso.", "sucesso")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_form.html", imovel=None)


@app.route("/admin/editar/<imovel_id>", methods=["GET", "POST"])
@login_obrigatorio
def admin_editar_imovel(imovel_id):
    imoveis = listar_imoveis()
    imovel = next((i for i in imoveis if i["id"] == imovel_id), None)
    if not imovel:
        abort(404)

    if request.method == "POST":
        imovel["titulo"] = request.form.get("titulo", "").strip()
        imovel["tipo"] = request.form.get("tipo", "venda")
        imovel["categoria"] = request.form.get("categoria", "").strip()
        imovel["preco"] = request.form.get("preco", "").strip()
        imovel["cidade"] = request.form.get("cidade", "").strip()
        imovel["bairro"] = request.form.get("bairro", "").strip()
        imovel["quartos"] = request.form.get("quartos", "").strip()
        imovel["suites"] = request.form.get("suites", "").strip()
        imovel["banheiros"] = request.form.get("banheiros", "").strip()
        imovel["vagas"] = request.form.get("vagas", "").strip()
        imovel["area_construida"] = request.form.get("area_construida", "").strip()
        imovel["area_terreno"] = request.form.get("area_terreno", "").strip()
        imovel["descricao"] = request.form.get("descricao", "").strip()
        imovel["whatsapp"] = request.form.get("whatsapp", "").strip()
        imovel["destaque"] = bool(request.form.get("destaque"))

        novas_fotos = _processar_fotos(request.files.getlist("fotos"), imovel_id)
        if novas_fotos:
            imovel.setdefault("fotos", []).extend(novas_fotos)

        salvar_imoveis(imoveis)
        flash("Imóvel atualizado.", "sucesso")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_form.html", imovel=imovel)


@app.route("/admin/excluir/<imovel_id>", methods=["POST"])
@login_obrigatorio
def admin_excluir_imovel(imovel_id):
    imoveis = listar_imoveis()
    imoveis = [i for i in imoveis if i["id"] != imovel_id]
    salvar_imoveis(imoveis)
    flash("Imóvel excluído.", "sucesso")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/excluir-foto/<imovel_id>/<foto>", methods=["POST"])
@login_obrigatorio
def admin_excluir_foto(imovel_id, foto):
    imoveis = listar_imoveis()
    imovel = next((i for i in imoveis if i["id"] == imovel_id), None)
    if imovel and foto in imovel.get("fotos", []):
        imovel["fotos"].remove(foto)
        caminho = os.path.join(UPLOAD_FOLDER, imovel_id, foto)
        if os.path.exists(caminho):
            os.remove(caminho)
        salvar_imoveis(imoveis)
        flash("Foto removida.", "sucesso")
    return redirect(url_for("admin_editar_imovel", imovel_id=imovel_id))


def _processar_fotos(arquivos, imovel_id):
    salvos = []
    pasta_imovel = os.path.join(UPLOAD_FOLDER, imovel_id)
    for arquivo in arquivos:
        if arquivo and arquivo.filename and arquivo_permitido(arquivo.filename):
            os.makedirs(pasta_imovel, exist_ok=True)
            nome_seguro = secure_filename(arquivo.filename)
            nome_final = f"{uuid.uuid4().hex[:8]}_{nome_seguro}"
            arquivo.save(os.path.join(pasta_imovel, nome_final))
            salvos.append(nome_final)
    return salvos


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)
