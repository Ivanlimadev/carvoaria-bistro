import flet as ft
import os
import platform
import base64
import time
import re
import shutil
import unicodedata
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, HRFlowable

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None

os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["FLET_SECRET_KEY"] = "curriculo_expresso_2026"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
PDF_DIR = os.path.join(APP_DIR, "assets", "pdfs")
PDF_RETENTION_SECONDS = 60 * 60 * 24
UPLOAD_DEBUG_LOG = os.path.join(UPLOAD_DIR, "upload_debug.log")

def main(page: ft.Page):

    # Referência para armazenar arquivo em memória
    arquivo_imagem_base64 = {"valor": None}
    caminho_foto_arquivo = {"valor": None}
    upload_destinos = {}
    ultimo_pdf = {"nome": None, "caminho": None}
    formato_foto = {"valor": "quadrada"}
    foto_upload_estado = {
        "em_andamento": False,
        "selecionada": False,
        "finalizado": False,
        "nome_esperado": None,
    }
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    MAX_UPLOAD_BYTES = 12 * 1024 * 1024

    def log_upload_debug(mensagem: str):
        try:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(UPLOAD_DEBUG_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {mensagem}\n")
        except Exception:
            pass

    def atualizar_status_foto(mensagem: str, cor: str = "white70"):
        return

    def atualizar_visual_preview_foto():
        if formato_foto["valor"] == "redonda":
            img_preview.border_radius = 999
        else:
            img_preview.border_radius = 8

    def chaves_nome_arquivo(nome_arquivo: str):
        nome_arquivo = (nome_arquivo or "").strip()
        nome_base = os.path.basename(nome_arquivo)
        nome_base_lower = nome_base.lower()
        nome_base_slug = slug_nome_arquivo(nome_base)
        return [
            nome_arquivo,
            nome_arquivo.lower(),
            nome_base,
            nome_base_lower,
            nome_base_slug,
        ]

    def arquivo_pronto_para_leitura(caminho: str):
        if not caminho or not os.path.exists(caminho):
            return False
        try:
            tamanho = os.path.getsize(caminho)
            if tamanho <= 0:
                return False
            with open(caminho, "rb") as f:
                cabecalho = f.read(16)
            return len(cabecalho) > 0
        except Exception:
            return False

    def aguardar_arquivo_pronto(caminho: str, tentativas: int = 40, intervalo: float = 0.2):
        ultimo_tamanho = -1
        estabilidade = 0
        for _ in range(tentativas):
            if caminho and os.path.exists(caminho):
                try:
                    tamanho_atual = os.path.getsize(caminho)
                except Exception:
                    tamanho_atual = -1

                if tamanho_atual > 0:
                    if tamanho_atual == ultimo_tamanho:
                        estabilidade += 1
                    else:
                        estabilidade = 0
                    ultimo_tamanho = tamanho_atual

                    if estabilidade >= 1 and arquivo_pronto_para_leitura(caminho):
                        return caminho

            time.sleep(intervalo)
        return None

    def localizar_arquivo_upload(nome_arquivo_evento: str):
        nome_arquivo_evento = (nome_arquivo_evento or "").strip()
        nome_base = os.path.basename(nome_arquivo_evento)

        candidatos = []
        for chave in chaves_nome_arquivo(nome_arquivo_evento):
            caminho = upload_destinos.get(chave)
            if caminho:
                candidatos.append(caminho)

        if nome_base:
            candidatos.append(os.path.join(UPLOAD_DIR, nome_base))

        try:
            arquivos_upload = os.listdir(UPLOAD_DIR)
        except Exception:
            arquivos_upload = []

        for arquivo in arquivos_upload:
            if nome_base and arquivo.endswith(nome_base):
                candidatos.append(os.path.join(UPLOAD_DIR, arquivo))

        # Fallback mobile/web: usa arquivos de imagem recentes se o callback vier com nome inconsistente.
        agora = time.time()
        extensoes_img = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        for arquivo in arquivos_upload:
            nome_arquivo = arquivo.lower()
            if not nome_arquivo.endswith(extensoes_img):
                continue
            caminho_arquivo = os.path.join(UPLOAD_DIR, arquivo)
            try:
                if agora - os.path.getmtime(caminho_arquivo) <= 180:
                    candidatos.append(caminho_arquivo)
            except Exception:
                continue

        vistos = set()
        candidatos_unicos = []
        for candidato in candidatos:
            if candidato and candidato not in vistos:
                vistos.add(candidato)
                candidatos_unicos.append(candidato)

        for _ in range(40):
            for candidato in candidatos_unicos:
                if os.path.exists(candidato):
                    pronto = aguardar_arquivo_pronto(candidato)
                    if pronto:
                        return pronto
            time.sleep(0.2)

        return None

    def carregar_preview(caminho_arquivo: str, nome_exibicao: str):
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError("arquivo nao encontrado")

        # Preview leve em base64 para garantir exibicao consistente no mobile.
        if Image is not None:
            with Image.open(caminho_arquivo) as im:
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                im.thumbnail((380, 380))
                buff = BytesIO()
                im.save(buff, format="JPEG", quality=72, optimize=True)
                preview_bytes = buff.getvalue()
        else:
            with open(caminho_arquivo, "rb") as f:
                preview_bytes = f.read()

        arquivo_imagem_base64["valor"] = base64.b64encode(preview_bytes).decode()
        caminho_foto_arquivo["valor"] = caminho_arquivo
        foto_upload_estado["em_andamento"] = False
        img_preview.src = None
        img_preview.src_base64 = arquivo_imagem_base64["valor"]
        atualizar_visual_preview_foto()
        img_wrapper.visible = True

        caminho_foto.value = nome_exibicao
        atualizar_status_foto("Pronta para gerar PDF", "#56D364")
        page.snack_bar = ft.SnackBar(ft.Text(f"Foto carregada: {nome_exibicao}", color="white"))
        page.snack_bar.open = True
        page.update()

    def alterar_formato_foto(e):
        novo_formato = (e.control.value or "quadrada").strip().lower()
        if novo_formato not in ("quadrada", "redonda"):
            novo_formato = "quadrada"
        formato_foto["valor"] = novo_formato
        if img_wrapper.visible:
            atualizar_visual_preview_foto()
            img_preview.update()

    def upload_progresso(e: ft.FilePickerUploadEvent):
        try:
            if foto_upload_estado["finalizado"]:
                return

            nome_evento = (getattr(e, "file_name", "") or "").strip()
            chaves_evento = chaves_nome_arquivo(nome_evento)
            evento_relacionado = any(ch in upload_destinos for ch in chaves_evento)
            log_upload_debug(f"on_upload file_name={nome_evento} progress={getattr(e, 'progress', None)} related={evento_relacionado} error={getattr(e, 'error', None)}")

            if e.error:
                if not evento_relacionado and not foto_upload_estado["em_andamento"]:
                    return
                foto_upload_estado["em_andamento"] = False
                atualizar_status_foto("Erro no upload", "#FF6B6B")
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro no upload: {e.error}", color="#FF6B6B"))
                page.snack_bar.open = True
                page.update()
                return

            if e.progress is not None and e.progress < 1:
                foto_upload_estado["em_andamento"] = True
                percentual = int(e.progress * 100)
                atualizar_status_foto(f"Enviando... {percentual}%", "#F0C674")
                return

            if e.progress is not None and e.progress >= 1:
                atualizar_status_foto("Finalizando upload...", "#8AB4F8")
                destino = localizar_arquivo_upload(e.file_name)
                log_upload_debug(f"destino_resolvido={destino}")

                if destino and os.path.exists(destino):
                    try:
                        carregar_preview(destino, os.path.basename(destino))
                        foto_upload_estado["finalizado"] = True
                        log_upload_debug("preview_carregado_com_sucesso")
                    except Exception as err:
                        foto_upload_estado["em_andamento"] = False
                        foto_upload_estado["selecionada"] = False
                        if not arquivo_imagem_base64["valor"]:
                            img_wrapper.visible = False
                        atualizar_status_foto("Erro ao processar foto", "#FF6B6B")
                        page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao ler foto enviada. Tente JPG/PNG menor: {str(err)[:90]}", color="#FF6B6B"))
                        page.snack_bar.open = True
                        page.update()
                else:
                    foto_upload_estado["em_andamento"] = False
                    foto_upload_estado["selecionada"] = False
                    atualizar_status_foto("Upload concluido, mas foto nao encontrada", "#FF6B6B")
                    page.snack_bar = ft.SnackBar(ft.Text("Upload concluido, mas arquivo nao foi encontrado no servidor.", color="#FF6B6B"))
                    page.snack_bar.open = True
                    page.update()
        except Exception as err:
            foto_upload_estado["em_andamento"] = False
            foto_upload_estado["selecionada"] = False
            atualizar_status_foto("Erro inesperado no upload", "#FF6B6B")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro inesperado: {str(err)[:120]}", color="#FF6B6B"))
            page.snack_bar.open = True
            page.update()

    def processar_arquivo(e: ft.FilePickerResultEvent):
        if not e.files:
            atualizar_status_foto("Nenhuma foto selecionada", "white70")
            return

        try:
            arquivo = e.files[0]
            upload_destinos.clear()
            foto_upload_estado["selecionada"] = True
            foto_upload_estado["finalizado"] = False
            foto_upload_estado["nome_esperado"] = arquivo.name
            log_upload_debug(f"pick_file name={arquivo.name} size={getattr(arquivo, 'size', None)} path={getattr(arquivo, 'path', None)}")
            atualizar_status_foto("Processando foto...", "#8AB4F8")

            if getattr(arquivo, "size", None) and arquivo.size > MAX_UPLOAD_BYTES:
                raise ValueError("Arquivo muito grande. Envie uma foto com no maximo 12MB.")

            # Desktop/local: o path costuma existir e pode ser lido diretamente.
            if arquivo.path and os.path.exists(arquivo.path):
                nome_base_local = os.path.basename(arquivo.name).replace(" ", "_")
                nome_servidor_local = f"{int(time.time())}_{nome_base_local}"
                destino_local = os.path.join(UPLOAD_DIR, nome_servidor_local)
                shutil.copy2(arquivo.path, destino_local)
                carregar_preview(destino_local, arquivo.name)
                foto_upload_estado["finalizado"] = True
                return

            # Web: enviar arquivo do navegador para o servidor primeiro.
            nome_base = os.path.basename(arquivo.name).replace(" ", "_")
            nome_servidor = f"{int(time.time())}_{nome_base}"
            destino_relativo = nome_servidor
            destino_absoluto = os.path.join(UPLOAD_DIR, nome_servidor)
            for chave in chaves_nome_arquivo(arquivo.name):
                upload_destinos[chave] = destino_absoluto
            for chave in chaves_nome_arquivo(nome_base):
                upload_destinos[chave] = destino_absoluto
            for chave in chaves_nome_arquivo(nome_servidor):
                upload_destinos[chave] = destino_absoluto

            file_picker.upload([
                ft.FilePickerUploadFile(
                    arquivo.name,
                    upload_url=page.get_upload_url(destino_relativo, 600),
                )
            ])

            foto_upload_estado["em_andamento"] = True
            atualizar_status_foto("Enviando... 0%", "#F0C674")
            page.snack_bar = ft.SnackBar(ft.Text("Enviando foto...", color="white"))
            page.snack_bar.open = True

            # Fallback para mobile/web: conclui o fluxo mesmo se on_upload nao disparar.
            destino_sincrono = aguardar_arquivo_pronto(destino_absoluto, tentativas=30, intervalo=0.2)
            if destino_sincrono and not foto_upload_estado["finalizado"]:
                try:
                    carregar_preview(destino_sincrono, arquivo.name)
                    foto_upload_estado["finalizado"] = True
                    log_upload_debug("fallback_sincrono_preview_ok")
                except Exception as err_preview:
                    log_upload_debug(f"fallback_sincrono_preview_erro={str(err_preview)[:120]}")
        except Exception as err:
            foto_upload_estado["em_andamento"] = False
            atualizar_status_foto("Erro no upload", "#FF6B6B")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro no upload da foto: {str(err)[:80]}", color="#FF6B6B"))
            page.snack_bar.open = True
        page.update()

    def iniciar_upload(e):
        """Abre o diálogo de seleção de arquivo"""
        atualizar_status_foto("Selecione uma foto", "#8AB4F8")
        file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"],
            allow_multiple=False
        )

    file_picker = ft.FilePicker(on_result=processar_arquivo, on_upload=upload_progresso)
    page.overlay.append(file_picker)

    # CONFIG
    page.title = "Currículo Expresso Pro"
    if not getattr(page, "web", False):
        page.window_width = 500
        page.window_height = 850
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "auto"
    page.padding = 0

    COR_AZUL = "#00B4DB"
    COR_CAMPO = "#252525"

    cores_modelos = {"1": "#00B4DB", "2": "#4CAF50", "3": "#FF5722", "4": "#D4AF37", "5": "#C9A876"}

    lista_exp = []
    lista_edu = []
    lista_idiomas = []
    lista_cursos = []

    def slug_nome_arquivo(texto: str) -> str:
        texto = (texto or "").strip().lower()
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
        return texto or "usuario"

    def limpar_pdfs_antigos(max_age_seconds: int = PDF_RETENTION_SECONDS):
        if not os.path.exists(PDF_DIR):
            return
        agora = time.time()
        for nome_arquivo in os.listdir(PDF_DIR):
            caminho_arquivo = os.path.join(PDF_DIR, nome_arquivo)
            if not os.path.isfile(caminho_arquivo):
                continue
            if not nome_arquivo.lower().endswith(".pdf"):
                continue
            try:
                if agora - os.path.getmtime(caminho_arquivo) > max_age_seconds:
                    os.remove(caminho_arquivo)
            except Exception:
                # Ignora arquivos bloqueados ou com erro de permissao.
                pass

    def validar_campos_obrigatorios() -> list[str]:
        faltando = []
        if not (nome.value or "").strip():
            faltando.append("Nome Completo")
        if not (cidade.value or "").strip():
            faltando.append("Cidade/Estado")
        if not ((email.value or "").strip() or (tel.value or "").strip()):
            faltando.append("E-mail ou Telefone")
        return faltando

    def data_texto_valida(valor: str) -> bool:
        texto = (valor or "").strip()
        if not texto:
            return True
        digitos = re.sub(r"\D", "", texto)
        if len(digitos) != 8:
            return False
        try:
            datetime.strptime(digitos, "%d%m%Y")
            return True
        except ValueError:
            return False

    modelo_cv = None
    idioma = "pt"

    modelo_text = ft.Text("Visualize os modelos e selecione um para gerar o PDF.", color="white70", size=16)
    titulo_modelos_ref = {"control": None}
    menu_modelos_ref = {"control": None}
    modelos_corpo_ref = {"control": None}
    modelo_names = {1: "Clássico", 2: "Moderno", 3: "Elegante", 4: "Dark", 5: "Premium"}

    def formatar_data_no_blur(e):
        valor_atual = (e.control.value or "").strip()
        apenas_digitos = re.sub(r"\D", "", valor_atual)[:8]

        if len(apenas_digitos) == 8:
            e.control.value = f"{apenas_digitos[:2]}/{apenas_digitos[2:4]}/{apenas_digitos[4:8]}"
        else:
            # Mantem apenas os digitos digitados se ainda estiver incompleto.
            e.control.value = apenas_digitos

        e.control.update()

    # Referências dos containers de modelos
    modelo_containers = {}
    modelo_select_buttons = {}

    def atualizar_estado_modelo_ui():
        nomes_localizados = {
            1: t("classico"),
            2: t("moderno"),
            3: t("elegante"),
            4: t("dark"),
            5: t("premium"),
        }

        if modelo_cv is None:
            modelo_text.value = t("modelo_nao_selecionado")
            modelo_text.color = "white70"
        else:
            modelo_text.value = f"{t('modelo_selecionado_label')}: {nomes_localizados.get(modelo_cv, '')}"
            modelo_text.color = "white"

        cores = {1: "#00B4DB", 2: "#4CAF50", 3: "#FF5722", 4: "#D4AF37", 5: "#C9A876"}
        for i in [1, 2, 3, 4, 5]:
            if i in modelo_containers:
                cor_selecionada = cores[i] if i == modelo_cv else "#333"
                cor_bg = cores[i] if i == modelo_cv else "#1e1e1e"
                modelo_containers[i].border = ft.border.all(2, cor_selecionada)
                modelo_containers[i].bgcolor = cor_bg

            if i in modelo_select_buttons:
                botao = modelo_select_buttons[i]
                selecionado = i == modelo_cv
                botao.text = t("selecionado") if selecionado else t("selecionar")
                botao.bgcolor = cores[i] if selecionado else "#2B2B2B"
                botao.color = "black" if selecionado else "white"

        if "btn_gerar_pdf" in locals():
            btn_gerar_pdf.disabled = modelo_cv is None
        if "btn_baixar_ultimo_pdf" in locals():
            btn_baixar_ultimo_pdf.disabled = False

    def selecionar_modelo_visual(num):
        nonlocal modelo_cv
        modelo_cv = num

        atualizar_estado_modelo_ui()

        # Fecha o painel de modelos para revelar o botão Gerar PDF
        if modelos_corpo_ref["control"] is not None:
            modelos_corpo_ref["control"].visible = False
            # Atualiza o ícone da seta
            if menu_modelos_ref["control"] is not None:
                menu_modelos_ref["control"].name = ft.icons.KEYBOARD_ARROW_DOWN

        page.snack_bar = ft.SnackBar(ft.Text(f"{t('modelo_selecionado_toast')} {modelo_names.get(num, '')}!"))
        page.snack_bar.open = True
        page.update()

    def selecionar_idioma_visual(lang):
        nonlocal idioma
        idioma = lang
        atualizar_idioma_ui()
        page.update()

    def Campo(label, hint="", multi=False, mask=False):
        return ft.TextField(
            label=label,
            hint_text=hint,
            multiline=multi,
            min_lines=3 if multi else 1,
            max_length=10 if mask else None,
            keyboard_type=ft.KeyboardType.TEXT,
            input_filter=None,
            autocorrect=False,
            enable_suggestions=False,
            border_color=COR_AZUL,
            border_radius=12,
            bgcolor=COR_CAMPO,
            text_size=14,
            label_style=ft.TextStyle(color=COR_AZUL),
            focused_border_color="white",
            on_change=None,
            on_blur=formatar_data_no_blur if mask else None
        )

    def fechar_outros(e):
        if e.data == "true":
            for tile in menu_accordion.controls:
                if isinstance(tile, ft.ExpansionTile) and tile != e.control:
                    tile.expanded = False
            page.update()

    # ===== TRADUÇÃO =====
    def t(chave):
        traducoes = {
            "pt": {
                "resumo": "Resumo", "experiencia": "Experiência", "educacao": "Educação", "habilidades": "Habilidades", "idiomas": "Idiomas", "cursos": "Cursos",
                "foto_perfil": "Foto do Perfil", "nome_completo": "Nome Completo", "dados_pessoais": "Dados Pessoais", "data_nascimento": "Data de Nascimento", "nacionalidade": "Nacionalidade", "cidade_estado": "Cidade/Estado",
                "contato": "Contato", "email": "E-mail", "telefone": "Telefone / WhatsApp", "links": "LinkedIn / GitHub", "resumo_profissional": "Resumo Profissional", "conte_trajetoria": "Conte sua trajetória...",
                "empresa": "Empresa", "cargo": "Cargo", "data_inicio": "Data Início", "data_fim": "Data Fim", "adicionar": "ADICIONAR +",
                "instituicao": "Instituição", "curso": "Curso", "habilidades_tecnicas": "Habilidades Técnicas e Pessoais", "ex_python_excel": "Ex: Python, Excel",
                "idioma_nivel": "Idioma e Nível", "curso_certificacao": "Curso / Certificação", "idioma_cv": "🌍 Idioma do CV", "curriculo_expresso": "CURRÍCULO EXPRESSO",
                "escolha_modelo": "Escolha o modelo do CV:", "classico": "Clássico", "moderno": "Moderno", "elegante": "Elegante", "gerar_pdf": "GERAR PDF PROFISSIONAL",
                "dark": "Dark", "premium": "Premium", "adicionar_foto": "Adicionar Foto", "baixar_ultimo_pdf": "BAIXAR ULTIMO PDF",
                "visualizar_modelos": "Escolha seu modelo PDF", "selecionar": "Selecionar", "selecionado": "Selecionado",
                "modelo_nao_selecionado": "Visualize os modelos e selecione um para gerar o PDF.",
                "modelo_selecionado_label": "Modelo selecionado", "modelo_selecionado_toast": "Modelo selecionado:",
                "selecione_modelo_antes_gerar": "Selecione um modelo antes de gerar o PDF."
            },
            "en": {
                "resumo": "Summary", "experiencia": "Experience", "educacao": "Education", "habilidades": "Skills", "idiomas": "Languages", "cursos": "Courses",
                "foto_perfil": "Profile Photo", "nome_completo": "Full Name", "dados_pessoais": "Personal Data", "data_nascimento": "Date of Birth", "nacionalidade": "Nationality", "cidade_estado": "City/State",
                "contato": "Contact", "email": "E-mail", "telefone": "Phone / WhatsApp", "links": "LinkedIn / GitHub", "resumo_profissional": "Professional Summary", "conte_trajetoria": "Tell your journey...",
                "empresa": "Company", "cargo": "Position", "data_inicio": "Start Date", "data_fim": "End Date", "adicionar": "ADD +",
                "instituicao": "Institution", "curso": "Course", "habilidades_tecnicas": "Technical and Personal Skills", "ex_python_excel": "Ex: Python, Excel",
                "idioma_nivel": "Language and Level", "curso_certificacao": "Course / Certification", "idioma_cv": "🌍 CV Language", "curriculo_expresso": "CURRICULUM EXPRESS",
                "escolha_modelo": "Choose the CV model:", "classico": "Classic", "moderno": "Modern", "elegante": "Elegant", "gerar_pdf": "GENERATE PROFESSIONAL PDF",
                "dark": "Dark", "premium": "Premium", "adicionar_foto": "Add Photo", "baixar_ultimo_pdf": "DOWNLOAD LAST PDF",
                "visualizar_modelos": "Choose your PDF model", "selecionar": "Select", "selecionado": "Selected",
                "modelo_nao_selecionado": "Review the models and select one before generating the PDF.",
                "modelo_selecionado_label": "Selected model", "modelo_selecionado_toast": "Selected model:",
                "selecione_modelo_antes_gerar": "Select a model before generating the PDF."
            },
            "es": {
                "resumo": "Resumen", "experiencia": "Experiencia", "educacao": "Educación", "habilidades": "Habilidades", "idiomas": "Idiomas", "cursos": "Cursos",
                "foto_perfil": "Foto de Perfil", "nome_completo": "Nombre Completo", "dados_pessoais": "Datos Personales", "data_nascimento": "Fecha de Nacimiento", "nacionalidade": "Nacionalidad", "cidade_estado": "Ciudad/Estado",
                "contato": "Contacto", "email": "Correo Electrónico", "telefone": "Teléfono / WhatsApp", "links": "LinkedIn / GitHub", "resumo_profissional": "Resumen Profesional", "conte_trajetoria": "Cuenta tu trayectoria...",
                "empresa": "Empresa", "cargo": "Cargo", "data_inicio": "Fecha de Inicio", "data_fim": "Fecha de Fin", "adicionar": "AGREGAR +",
                "instituicao": "Institución", "curso": "Curso", "habilidades_tecnicas": "Habilidades Técnicas y Personales", "ex_python_excel": "Ej: Python, Excel",
                "idioma_nivel": "Idioma y Nivel", "curso_certificacao": "Curso / Certificación", "idioma_cv": "🌍 Idioma del CV", "curriculo_expresso": "CURRÍCULO EXPRESS",
                "escolha_modelo": "Elige el modelo del CV:", "classico": "Clásico", "moderno": "Moderno", "elegante": "Elegante", "gerar_pdf": "GENERAR PDF PROFESIONAL",
                "dark": "Dark", "premium": "Premium", "adicionar_foto": "Agregar Foto", "baixar_ultimo_pdf": "DESCARGAR ULTIMO PDF",
                "visualizar_modelos": "Elige tu modelo PDF", "selecionar": "Seleccionar", "selecionado": "Seleccionado",
                "modelo_nao_selecionado": "Visualiza los modelos y selecciona uno antes de generar el PDF.",
                "modelo_selecionado_label": "Modelo seleccionado", "modelo_selecionado_toast": "Modelo seleccionado:",
                "selecione_modelo_antes_gerar": "Selecciona un modelo antes de generar el PDF."
            }
        }
        return traducoes[idioma].get(chave, chave)

    # ================= PDF =================
    def gerar_pdf(e):
        if modelo_cv is None:
            page.snack_bar = ft.SnackBar(ft.Text(t("selecione_modelo_antes_gerar")), open=True)
            page.update()
            return

        if foto_upload_estado["em_andamento"]:
            page.snack_bar = ft.SnackBar(ft.Text("Aguarde: upload da foto ainda em andamento."), open=True)
            page.update()
            return

        campos_faltando = validar_campos_obrigatorios()
        if campos_faltando:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Preencha os campos obrigatorios: {', '.join(campos_faltando)}"),
                open=True,
            )
            page.update()
            return

        datas_invalidas = []
        if not data_texto_valida(nasc.value):
            datas_invalidas.append(t("data_nascimento"))
        if not data_texto_valida(exp_ini.value):
            datas_invalidas.append(f"{t('experiencia')} - {t('data_inicio')}")
        if not data_texto_valida(exp_fim.value):
            datas_invalidas.append(f"{t('experiencia')} - {t('data_fim')}")
        if not data_texto_valida(edu_ini.value):
            datas_invalidas.append(f"{t('educacao')} - {t('data_inicio')}")
        if not data_texto_valida(edu_fim.value):
            datas_invalidas.append(f"{t('educacao')} - {t('data_fim')}")
        if not data_texto_valida(curso_ini.value):
            datas_invalidas.append(f"{t('cursos')} - {t('data_inicio')}")
        if not data_texto_valida(curso_fim.value):
            datas_invalidas.append(f"{t('cursos')} - {t('data_fim')}")

        if datas_invalidas:
            page.snack_bar = ft.SnackBar(ft.Text(f"Datas invalidas: {', '.join(datas_invalidas)}"), open=True)
            page.update()
            return

        nomes_modelos = {1: "Clássico", 2: "Moderno", 3: "Elegante", 4: "Dark", 5: "Premium"}
        page.snack_bar = ft.SnackBar(ft.Text(f"Gerando PDF - Modelo {modelo_cv} ({nomes_modelos.get(modelo_cv, 'Desconhecido')})"))
        page.snack_bar.open = True
        page.update()
        limpar_pdfs_antigos()
        nome_slug = slug_nome_arquivo(nome.value)
        pdf_filename = f"curriculo_{nome_slug}_{int(time.time())}.pdf"
        pdf_filepath = os.path.join(PDF_DIR, pdf_filename)
        os.makedirs(PDF_DIR, exist_ok=True)
        doc = SimpleDocTemplate(pdf_filepath, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        
        styles = getSampleStyleSheet()
        cor_modelo = cores_modelos[str(modelo_cv)]
        bullet_item = "•"
        
        if modelo_cv == 1:  # Clássico
            bullet_item = "•"
            estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=26, textColor=colors.HexColor(cor_modelo), spaceAfter=10, fontName='Helvetica-Bold', alignment=0)
            estilo_secao = ParagraphStyle('Secao', parent=styles['Heading2'], fontSize=11, textColor=colors.white, backColor=colors.HexColor('#008CB0'), spaceBefore=13, spaceAfter=7, fontName='Helvetica-Bold', alignment=0, leftIndent=0, rightIndent=0, borderPadding=5)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=10.9, leading=16, spaceAfter=6, fontName='Helvetica', textColor=colors.HexColor('#111827'))
            estilo_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=10.8, leftIndent=10, bulletIndent=0, fontName='Helvetica', textColor=colors.HexColor('#1F2937'))
        elif modelo_cv == 2:  # Moderno
            bullet_item = "■"
            estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor(cor_modelo), spaceAfter=10, fontName='Helvetica-Bold', alignment=1)
            estilo_secao = ParagraphStyle('Secao', parent=styles['Heading2'], fontSize=12, textColor=colors.white, backColor=colors.HexColor(cor_modelo), spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold', alignment=0)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=11, leading=15, spaceAfter=6, fontName='Helvetica')
            estilo_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=11, leftIndent=12, bulletIndent=0, fontName='Helvetica')
        elif modelo_cv == 3:  # Elegante
            bullet_item = "•"
            estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=23, textColor=colors.HexColor(cor_modelo), spaceAfter=10, fontName='Times-Bold', alignment=1)
            estilo_secao = ParagraphStyle('Secao', parent=styles['Heading2'], fontSize=11.8, textColor=colors.HexColor(cor_modelo), spaceBefore=16, spaceAfter=6, fontName='Times-Bold', alignment=1)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=10.9, leading=16.5, spaceAfter=5, fontName='Times-Roman', alignment=4, leftIndent=10, rightIndent=10)
            estilo_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=10.9, leftIndent=18, bulletIndent=6, fontName='Times-Roman', textColor=colors.HexColor('#3F2E1D'))
        elif modelo_cv == 4:  # Dark
            bullet_item = "◆"
            estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=25, textColor=colors.HexColor(cor_modelo), spaceAfter=8, fontName='Helvetica-Bold', alignment=0)
            estilo_secao = ParagraphStyle('Secao', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor(cor_modelo), backColor=colors.HexColor("#F5F5F5"), spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold', alignment=0)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=10.5, leading=15, spaceAfter=5, fontName='Helvetica', textColor=colors.HexColor('#2A2A2A'))
            estilo_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=10.5, leftIndent=12, bulletIndent=0, fontName='Helvetica', textColor=colors.HexColor('#2A2A2A'))
        elif modelo_cv == 5:  # Premium
            bullet_item = "◆"
            estilo_nome = ParagraphStyle('Nome', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor(cor_modelo), spaceAfter=10, fontName='Helvetica-Bold', alignment=0)
            estilo_secao = ParagraphStyle('Secao', parent=styles['Heading2'], fontSize=11.5, textColor=colors.white, backColor=colors.HexColor('#1A2F4A'), spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold', alignment=0)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=10.8, leading=15.5, spaceAfter=5, fontName='Helvetica', textColor=colors.HexColor('#2C3E50'))
            estilo_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=10.8, leftIndent=12, bulletIndent=0, fontName='Helvetica', textColor=colors.HexColor('#2C3E50'))

        elementos = []

        def adicionar_titulo_secao(chave_titulo: str):
            titulo = t(chave_titulo).upper()
            if modelo_cv == 1:
                titulo = f"<b>{titulo}</b>"
            elif modelo_cv == 3:
                titulo = f"<i>{titulo}</i>"
            elif modelo_cv == 4:
                titulo = f"<b>{titulo}</b>"

            elementos.append(Paragraph(titulo, estilo_secao))
            if modelo_cv == 1:
                elementos.append(Spacer(1, 4))
            elif modelo_cv == 3:
                elementos.append(HRFlowable(width="52%", thickness=0.7, color=colors.HexColor(cor_modelo), spaceBefore=1, spaceAfter=5))

        dados_pessoais_pdf = []
        if (nome.value or "").strip():
            dados_pessoais_pdf.append(f"{t('nome_completo')}: {nome.value.strip()}")
        if (nasc.value or "").strip():
            dados_pessoais_pdf.append(f"{t('data_nascimento')}: {nasc.value.strip()}")
        if (nacionalidade.value or "").strip():
            dados_pessoais_pdf.append(f"{t('nacionalidade')}: {nacionalidade.value.strip()}")
        if (cidade.value or "").strip():
            dados_pessoais_pdf.append(f"{t('cidade_estado')}: {cidade.value.strip()}")

        contato_pdf = []
        if (email.value or "").strip():
            contato_pdf.append(f"{t('email')}: {email.value.strip()}")
        if (tel.value or "").strip():
            contato_pdf.append(f"{t('telefone')}: {tel.value.strip()}")
        if (link.value or "").strip():
            contato_pdf.append(f"{t('links')}: {link.value.strip()}")

        nome_cabecalho = (nome.value or "").strip().upper() if (nome.value or "").strip() else "CURRICULO"
        cabecalho = [Paragraph(f"<b>{nome_cabecalho}</b>", estilo_nome)]

        tamanho_foto_pdf = 96
        foto_pdf_path = caminho_foto_arquivo["valor"]
        img_pdf = None
        aviso_foto_pdf = None

        # Se formato redondo for escolhido, tenta gerar avatar circular em PNG.
        if formato_foto["valor"] == "redonda" and Image is not None:
            fonte_bytes = None
            if foto_pdf_path and os.path.exists(foto_pdf_path):
                try:
                    with open(foto_pdf_path, "rb") as f:
                        fonte_bytes = f.read()
                except Exception:
                    fonte_bytes = None

            if fonte_bytes is None and arquivo_imagem_base64["valor"]:
                try:
                    fonte_bytes = base64.b64decode(arquivo_imagem_base64["valor"])
                except Exception:
                    fonte_bytes = None

            if fonte_bytes is not None:
                try:
                    with Image.open(BytesIO(fonte_bytes)) as im:
                        im = im.convert("RGBA")
                        lado = min(im.size)
                        left = (im.width - lado) // 2
                        top = (im.height - lado) // 2
                        im = im.crop((left, top, left + lado, top + lado)).resize((420, 420))

                        mascara = Image.new("L", (420, 420), 0)
                        ImageDraw.Draw(mascara).ellipse((0, 0, 419, 419), fill=255)

                        avatar = Image.new("RGBA", (420, 420), (255, 255, 255, 0))
                        avatar.paste(im, (0, 0), mascara)

                        buff_round = BytesIO()
                        avatar.save(buff_round, format="PNG")
                        buff_round.seek(0)
                        img_pdf = RLImage(buff_round, width=tamanho_foto_pdf, height=tamanho_foto_pdf)
                except Exception:
                    img_pdf = None

        # 1) Tentar usar o arquivo salvo no servidor.
        if img_pdf is None and foto_pdf_path and os.path.exists(foto_pdf_path):
            try:
                img_pdf = RLImage(foto_pdf_path, width=tamanho_foto_pdf, height=tamanho_foto_pdf)
            except Exception:
                # Alguns formatos (ex.: HEIC/WEBP) podem falhar no ReportLab.
                if Image is not None:
                    try:
                        with Image.open(foto_pdf_path) as im:
                            if im.mode not in ("RGB", "L"):
                                im = im.convert("RGB")
                            buff = BytesIO()
                            im.save(buff, format="PNG")
                            buff.seek(0)
                            img_pdf = RLImage(buff, width=tamanho_foto_pdf, height=tamanho_foto_pdf)
                    except Exception:
                        img_pdf = None

        # 2) Fallback para o base64 exibido no preview.
        if img_pdf is None and arquivo_imagem_base64["valor"]:
            try:
                imagem_bytes = base64.b64decode(arquivo_imagem_base64["valor"])
                buff = BytesIO(imagem_bytes)
                buff.seek(0)
                img_pdf = RLImage(buff, width=tamanho_foto_pdf, height=tamanho_foto_pdf)
            except Exception:
                if Image is not None:
                    try:
                        buff_in = BytesIO(base64.b64decode(arquivo_imagem_base64["valor"]))
                        with Image.open(buff_in) as im:
                            if im.mode not in ("RGB", "L"):
                                im = im.convert("RGB")
                            buff_out = BytesIO()
                            im.save(buff_out, format="PNG")
                            buff_out.seek(0)
                            img_pdf = RLImage(buff_out, width=tamanho_foto_pdf, height=tamanho_foto_pdf)
                    except Exception:
                        img_pdf = None

        if img_pdf is not None:
            if modelo_cv == 2:  # Moderno: foto à esquerda
                tabela_header = Table([[img_pdf, cabecalho]], colWidths=[100, 400])
            else:
                tabela_header = Table([[cabecalho, img_pdf]], colWidths=[380, 120])
        else:
            aviso_foto_pdf = "⚠ Foto nao foi inserida no PDF. Tente JPG ou PNG."
            tabela_header = Table([[cabecalho]], colWidths=[500])

        tabela_header.setStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor(cor_modelo)),
            ]
        )

        if modelo_cv == 1:
            tabela_header.setStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.1, colors.HexColor(cor_modelo)),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F9FF")),
                    ("LINEABOVE", (0, 0), (-1, -1), 0.9, colors.HexColor(cor_modelo)),
                ]
            )
        elif modelo_cv == 3:
            tabela_header.setStyle(
                [
                    ("LINEABOVE", (0, 0), (-1, -1), 0.9, colors.HexColor(cor_modelo)),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.9, colors.HexColor(cor_modelo)),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7EF")),
                ]
            )
        elif modelo_cv == 4:  # Dark
            tabela_header.setStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 2, colors.HexColor(cor_modelo)),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F8F8")),
                ]
            )
        elif modelo_cv == 5:  # Premium
            tabela_header.setStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#1A2F4A")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                ]
            )

        elementos.append(tabela_header)
        elementos.append(Spacer(1, 15))

        if modelo_cv == 3 and (dados_pessoais_pdf or contato_pdf):
            bloco_pessoal = "<br/>".join(dados_pessoais_pdf) if dados_pessoais_pdf else ""
            bloco_contato = "<br/>".join(contato_pdf) if contato_pdf else ""
            dados_contato_tabela = Table(
                [[
                    Paragraph(f"<b>{t('dados_pessoais').upper()}</b><br/>{bloco_pessoal}", estilo_texto),
                    Paragraph(f"<b>{t('contato').upper()}</b><br/>{bloco_contato}", estilo_texto),
                ]],
                colWidths=[250, 250],
            )
            dados_contato_tabela.setStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, colors.HexColor(cor_modelo)),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
            elementos.append(dados_contato_tabela)
        else:
            if dados_pessoais_pdf:
                adicionar_titulo_secao("dados_pessoais")
                for linha in dados_pessoais_pdf:
                    elementos.append(Paragraph(linha, estilo_texto))

            if contato_pdf:
                adicionar_titulo_secao("contato")
                for linha in contato_pdf:
                    elementos.append(Paragraph(linha, estilo_texto))

        if modelo_cv == 3:  # Elegante: adicionar linha decorativa
            elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(cor_modelo)))
            elementos.append(Spacer(1, 10))

        if resumo.value:
            if modelo_cv == 2:  # Moderno: resumo em negrito
                adicionar_titulo_secao("resumo")
                elementos.append(Paragraph(f"<b>{resumo.value}</b>", estilo_texto))
            else:
                adicionar_titulo_secao("resumo")
                elementos.append(Paragraph(resumo.value, estilo_texto))

        experiencias_pdf = list(lista_exp)
        if exp_emp.value or exp_car.value or exp_ini.value or exp_fim.value:
            experiencias_pdf.append({
                "emp": exp_emp.value,
                "car": exp_car.value,
                "ini": exp_ini.value,
                "fim": exp_fim.value,
            })

        if experiencias_pdf:
            adicionar_titulo_secao("experiencia")
            for exp in experiencias_pdf:
                elementos.append(Paragraph(f"<b>{exp['car']}</b> - {exp['emp']} ({exp['ini']} - {exp['fim']})", estilo_item))

        educacoes_pdf = list(lista_edu)
        if edu_inst.value or edu_cur.value or edu_ini.value or edu_fim.value:
            educacoes_pdf.append({
                "inst": edu_inst.value,
                "cur": edu_cur.value,
                "ini": edu_ini.value,
                "fim": edu_fim.value,
            })

        if educacoes_pdf:
            adicionar_titulo_secao("educacao")
            for edu in educacoes_pdf:
                elementos.append(Paragraph(f"<b>{edu['cur']}</b> - {edu['inst']} ({edu['ini']} - {edu['fim']})", estilo_item))

        if habs.value:
            adicionar_titulo_secao("habilidades")
            elementos.append(Paragraph(habs.value, estilo_texto))

        idiomas_pdf = list(lista_idiomas)
        if idioma_field.value:
            idiomas_pdf.append(idioma_field.value)

        if idiomas_pdf:
            adicionar_titulo_secao("idiomas")
            for i in idiomas_pdf:
                elementos.append(Paragraph(f"{bullet_item} {i}", estilo_item))

        cursos_pdf = list(lista_cursos)
        if curso_nome.value or curso_ini.value or curso_fim.value:
            cursos_pdf.append({
                "nome": curso_nome.value,
                "ini": curso_ini.value,
                "fim": curso_fim.value,
            })

        if cursos_pdf:
            adicionar_titulo_secao("cursos")
            for cur in cursos_pdf:
                elementos.append(Paragraph(f"{bullet_item} {cur['nome']} ({cur['ini']} - {cur['fim']})", estilo_item))

        try:
            doc.build(elementos)
            ultimo_pdf["nome"] = pdf_filename
            ultimo_pdf["caminho"] = pdf_filepath
            if aviso_foto_pdf:
                page.snack_bar = ft.SnackBar(ft.Text(aviso_foto_pdf), open=True)
                page.update()
            if getattr(page, 'web', False):
                # Modo web: PDF salvo em assets/pdfs e servido estaticamente
                page.launch_url(f"/pdfs/{pdf_filename}", web_window_name="_blank")
                page.snack_bar = ft.SnackBar(ft.Text("✅ PDF gerado! Abrindo em nova aba..."), open=True)
            else:
                # Modo desktop: abre o arquivo localmente
                sistema = platform.system()
                if sistema == "Windows": os.startfile(pdf_filepath)
                elif sistema == "Darwin": os.system(f'open "{pdf_filepath}"')
                else: os.system(f'xdg-open "{pdf_filepath}"')
                page.snack_bar = ft.SnackBar(ft.Text("✅ PDF gerado com sucesso!"), open=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao gerar PDF: {ex}"), open=True)
        page.update()

    def baixar_ultimo_pdf(e):
        nome_arquivo = ultimo_pdf["nome"]
        caminho_arquivo = ultimo_pdf["caminho"]
        if not nome_arquivo or not caminho_arquivo or not os.path.exists(caminho_arquivo):
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum PDF gerado ainda."), open=True)
            page.update()
            return

        if getattr(page, "web", False):
            page.launch_url(f"/pdfs/{nome_arquivo}", web_window_name="_blank")
        else:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(caminho_arquivo)
            elif sistema == "Darwin":
                os.system(f'open "{caminho_arquivo}"')
            else:
                os.system(f'xdg-open "{caminho_arquivo}"')

    # ================= UI IDIOMA =================
    def botao_idioma(label, lang):
        return ft.Container(
            content=ft.Text(label, weight="bold"),
            padding=10,
            bgcolor=COR_AZUL if idioma == lang else "#1e1e1e",
            border_radius=8,
            on_click=lambda e: selecionar_idioma_visual(lang)
        )

    linha_idiomas = ft.Row(spacing=10)

    # --- CAMPOS ---
    caminho_foto = Campo("Foto do Perfil")
    img_preview = ft.Image(width=120, height=120, fit=ft.ImageFit.COVER, border_radius=8)
    img_wrapper = ft.Container(content=img_preview, visible=False)

    nome = Campo("Nome Completo")
    nasc = Campo("Data de Nascimento", "Ex: 01011990", mask=True)
    nacionalidade = Campo("Nacionalidade")
    cidade = Campo("Cidade/Estado")

    email = Campo("E-mail")
    tel = Campo("Telefone / WhatsApp")
    link = Campo("LinkedIn / GitHub")

    resumo = Campo("Resumo Profissional", "Conte sua trajetória...", True)

    # EXPERIENCIA
    exp_emp = Campo("Empresa")
    exp_car = Campo("Cargo")
    exp_ini = Campo("Data Início", "DDMMYYYY", mask=True)
    exp_fim = Campo("Data Fim", "DDMMYYYY", mask=True)
    view_exp = ft.Column()

    def add_exp(e):
        if exp_emp.value:
            lista_exp.append({"emp": exp_emp.value, "car": exp_car.value, "ini": exp_ini.value, "fim": exp_fim.value})
            view_exp.controls.append(ft.Text(f"• {exp_car.value} @ {exp_emp.value} ({exp_ini.value}-{exp_fim.value})", color="white70"))
            exp_emp.value = exp_car.value = exp_ini.value = exp_fim.value = ""
            page.update()

    # EDUCACAO
    edu_inst = Campo("Instituição")
    edu_cur = Campo("Curso")
    edu_ini = Campo("Data Início", "DDMMYYYY", mask=True)
    edu_fim = Campo("Data Fim", "DDMMYYYY", mask=True)
    view_edu = ft.Column()

    def add_edu(e):
        if edu_inst.value:
            lista_edu.append({"inst": edu_inst.value, "cur": edu_cur.value, "ini": edu_ini.value, "fim": edu_fim.value})
            view_edu.controls.append(ft.Text(f"• {edu_cur.value} @ {edu_inst.value} ({edu_ini.value}-{edu_fim.value})", color="white70"))
            edu_inst.value = edu_cur.value = edu_ini.value = edu_fim.value = ""
            page.update()

    habs = Campo("Habilidades Técnicas e Pessoais", "Ex: Python, Excel", True)

    idioma_field = Campo("Idioma e Nível")
    view_idioma = ft.Column()
    def add_idioma(e):
        if idioma_field.value:
            lista_idiomas.append(idioma_field.value)
            view_idioma.controls.append(ft.Text(f"• {idioma_field.value}", color="white70"))
            idioma_field.value = ""; page.update()

    # CURSOS
    curso_nome = Campo("Curso / Certificação")
    curso_ini = Campo("Data Início", "DDMMYYYY", mask=True)
    curso_fim = Campo("Data Fim", "DDMMYYYY", mask=True)
    view_curso = ft.Column()

    def add_curso(e):
        if curso_nome.value:
            lista_cursos.append({"nome": curso_nome.value, "ini": curso_ini.value, "fim": curso_fim.value})
            view_curso.controls.append(ft.Text(f"• {curso_nome.value} ({curso_ini.value}-{curso_fim.value})", color="white70"))
            curso_nome.value = curso_ini.value = curso_fim.value = ""
            page.update()

    # --- MENU ACCORDION ---
    aba_foto = ft.ExpansionTile(title=ft.Text("📷 0. FOTO DE PERFIL", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([img_wrapper, ft.ElevatedButton("Adicionar Foto", on_click=iniciar_upload, bgcolor=COR_AZUL, color="black")], horizontal_alignment=ft.CrossAxisAlignment.CENTER))])
    aba_dados = ft.ExpansionTile(title=ft.Text("👤 1. DADOS PESSOAIS", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([nome, nasc, nacionalidade, cidade]))])
    aba_contato = ft.ExpansionTile(title=ft.Text("📞 2. CONTATO", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([email, tel, link]))])
    aba_resumo = ft.ExpansionTile(title=ft.Text("📝 3. RESUMO PROFISSIONAL", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=resumo)])
    aba_exp = ft.ExpansionTile(title=ft.Text("💼 4. EXPERIÊNCIA", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([exp_emp, exp_car, exp_ini, exp_fim, ft.ElevatedButton("ADICIONAR +", on_click=add_exp, bgcolor=COR_AZUL, color="white"), view_exp]))])
    aba_edu = ft.ExpansionTile(title=ft.Text("🎓 5. EDUCAÇÃO", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([edu_inst, edu_cur, edu_ini, edu_fim, ft.ElevatedButton("ADICIONAR +", on_click=add_edu, bgcolor=COR_AZUL, color="white"), view_edu]))])
    aba_hab = ft.ExpansionTile(title=ft.Text("⚡ 6. HABILIDADES", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=habs)])
    aba_idioma = ft.ExpansionTile(title=ft.Text("🌐 7. IDIOMAS", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([idioma_field, ft.ElevatedButton("ADICIONAR +", on_click=add_idioma, bgcolor=COR_AZUL, color="white"), view_idioma]))])
    aba_curso = ft.ExpansionTile(title=ft.Text("📜 8. CURSOS", weight="bold", color=COR_AZUL), on_change=fechar_outros, controls=[ft.Container(padding=15, content=ft.Column([curso_nome, curso_ini, curso_fim, ft.ElevatedButton("ADICIONAR +", on_click=add_curso, bgcolor=COR_AZUL, color="white"), view_curso]))])

    def atualizar_idioma_ui():
        linha_idiomas.controls = [
            botao_idioma("🇵🇹 PT", "pt"),
            botao_idioma("🇬🇧 EN", "en"),
            botao_idioma("🇪🇸 ES", "es"),
        ]
        # Update field labels
        caminho_foto.label = t("foto_perfil")
        nome.label = t("nome_completo")
        nasc.label = t("data_nascimento")
        nacionalidade.label = t("nacionalidade")
        cidade.label = t("cidade_estado")
        email.label = t("email")
        tel.label = t("telefone")
        link.label = t("links")
        resumo.label = t("resumo_profissional")
        resumo.hint_text = t("conte_trajetoria")
        exp_emp.label = t("empresa")
        exp_car.label = t("cargo")
        exp_ini.label = t("data_inicio")
        exp_fim.label = t("data_fim")
        edu_inst.label = t("instituicao")
        edu_cur.label = t("curso")
        edu_ini.label = t("data_inicio")
        edu_fim.label = t("data_fim")
        habs.label = t("habilidades_tecnicas")
        habs.hint_text = t("ex_python_excel")
        idioma_field.label = t("idioma_nivel")
        curso_nome.label = t("curso_certificacao")
        curso_ini.label = t("data_inicio")
        curso_fim.label = t("data_fim")
        # Update accordion titles
        aba_foto.title = ft.Text(f"📷 0. {t('foto_perfil').upper()}", weight="bold", color=COR_AZUL)
        aba_dados.title = ft.Text(f"👤 1. {t('dados_pessoais').upper()}", weight="bold", color=COR_AZUL)
        aba_contato.title = ft.Text(f"📞 2. {t('contato').upper()}", weight="bold", color=COR_AZUL)
        aba_resumo.title = ft.Text(f"📝 3. {t('resumo').upper()}", weight="bold", color=COR_AZUL)
        aba_exp.title = ft.Text(f"💼 4. {t('experiencia').upper()}", weight="bold", color=COR_AZUL)
        aba_edu.title = ft.Text(f"🎓 5. {t('educacao').upper()}", weight="bold", color=COR_AZUL)
        aba_hab.title = ft.Text(f"⚡ 6. {t('habilidades').upper()}", weight="bold", color=COR_AZUL)
        aba_idioma.title = ft.Text(f"🌐 7. {t('idiomas').upper()}", weight="bold", color=COR_AZUL)
        aba_curso.title = ft.Text(f"📜 8. {t('cursos').upper()}", weight="bold", color=COR_AZUL)
        # Update buttons
        for control in aba_exp.controls[0].content.controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "ADICIONAR +":
                control.text = t("adicionar")
        for control in aba_edu.controls[0].content.controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "ADICIONAR +":
                control.text = t("adicionar")
        for control in aba_idioma.controls[0].content.controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "ADICIONAR +":
                control.text = t("adicionar")
        for control in aba_curso.controls[0].content.controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "ADICIONAR +":
                control.text = t("adicionar")
        for control in aba_foto.controls[0].content.controls:
            if isinstance(control, ft.ElevatedButton) and "Adicionar Foto" in control.text:
                control.text = t("adicionar_foto")

        btn_gerar_pdf.text = t("gerar_pdf")
        btn_baixar_ultimo_pdf.text = t("baixar_ultimo_pdf")
        if titulo_modelos_ref["control"] is not None:
            titulo_modelos_ref["control"].value = t("visualizar_modelos")
        atualizar_estado_modelo_ui()
        page.update()

    menu_accordion = ft.Column([aba_foto, aba_dados, aba_contato, aba_resumo, aba_exp, aba_edu, aba_hab, aba_idioma, aba_curso])

    def criar_opcao_modelo(numero: int, card: ft.Container):
        botao = ft.ElevatedButton(
            t("selecionar"),
            on_click=lambda e, n=numero: selecionar_modelo_visual(n),
            bgcolor="#2B2B2B",
            color="white",
            width=180,
        )
        modelo_select_buttons[numero] = botao
        return ft.Container(
            padding=10,
            border_radius=14,
            bgcolor="#161616",
            content=ft.Column(
                [card, botao],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # Criar cards de modelo
    modelo_1_container = ft.Container(
        content=ft.Column([
            ft.Text("CLÁSSICO", size=12, weight="bold", color="#00B4DB"),
            ft.Container(
                content=ft.Column([
                    ft.Text("NOME", size=11, weight="bold", color="white"),
                    ft.Text("Data | Nac | Cidade", size=8, color="white70"),
                    ft.Text("Email | Tel", size=8, color="white70"),
                    ft.Divider(height=2, color="#00B4DB"),
                    ft.Text("RESUMO", size=9, weight="bold", color="#00B4DB"),
                    ft.Text("Seu resumo...", size=7, color="white70"),
                    ft.Text("EXPERIÊNCIA", size=9, weight="bold", color="#00B4DB"),
                    ft.Text("• Cargo", size=7, color="white70"),
                ], spacing=1),
                padding=6,
                bgcolor="#1a1a1a",
                border_radius=4,
                height=70
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=2),
        padding=12,
        bgcolor="#00B4DB",
        border=ft.border.all(2, "#00B4DB"),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000050"),
        on_click=lambda e: selecionar_modelo_visual(1),
        width=118,
        height=138
    )

    modelo_2_container = ft.Container(
        content=ft.Column([
            ft.Text("MODERNO", size=12, weight="bold", color="#4CAF50"),
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Container(width=35, height=35, bgcolor="#333", border_radius=6),
                        ft.Text("NOME", size=9, weight="bold", color="white"),
                    ], width=45, spacing=2),
                    ft.Column([
                        ft.Text("RESUMO", size=8, weight="bold", color="#4CAF50"),
                        ft.Text("Texto...", size=7, color="white70"),
                        ft.Text("EXP", size=8, weight="bold", color="#4CAF50"),
                        ft.Text("• Cargo", size=7, color="white70"),
                    ], spacing=1),
                ], spacing=3),
                padding=6,
                bgcolor="#1a1a1a",
                border_radius=4,
                height=70
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=2),
        padding=12,
        bgcolor="#1e1e1e",
        border=ft.border.all(2, "#333"),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000050"),
        on_click=lambda e: selecionar_modelo_visual(2),
        width=118,
        height=138
    )

    modelo_3_container = ft.Container(
        content=ft.Column([
            ft.Text("ELEGANTE", size=12, weight="bold", color="#FF5722"),
            ft.Container(
                content=ft.Column([
                    ft.Container(content=ft.Text("NOME", size=10, weight="bold", color="white"), alignment=ft.alignment.center),
                    ft.Container(content=ft.Text("Data | Nac", size=8, color="white70"), alignment=ft.alignment.center),
                    ft.Divider(height=2, color="#FF5722"),
                    ft.Container(content=ft.Text("RESUMO", size=9, weight="bold", color="#FF5722"), alignment=ft.alignment.center),
                    ft.Container(content=ft.Text("Elegância...", size=7, color="white70"), alignment=ft.alignment.center),
                    ft.Container(content=ft.Text("EXPERIÊNCIA", size=9, weight="bold", color="#FF5722"), alignment=ft.alignment.center),
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER),
                padding=6,
                bgcolor="#1a1a1a",
                border_radius=4,
                height=70
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=2),
        padding=12,
        bgcolor="#1e1e1e",
        border=ft.border.all(2, "#333"),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000050"),
        on_click=lambda e: selecionar_modelo_visual(3),
        width=118,
        height=138
    )

    modelo_4_container = ft.Container(
        content=ft.Column([
            ft.Text("DARK", size=12, weight="bold", color="#D4AF37"),
            ft.Container(
                content=ft.Column([
                    ft.Text("NOME", size=11, weight="bold", color="#D4AF37"),
                    ft.Text("Data | Nac | Cidade", size=8, color="#B0B0B0"),
                    ft.Text("Email | Tel", size=8, color="#B0B0B0"),
                    ft.Divider(height=2, color="#D4AF37"),
                    ft.Text("RESUMO", size=9, weight="bold", color="#D4AF37"),
                    ft.Text("Seu resumo...", size=7, color="#B0B0B0"),
                    ft.Text("EXPERIÊNCIA", size=9, weight="bold", color="#D4AF37"),
                    ft.Text("◆ Cargo", size=7, color="#B0B0B0"),
                ], spacing=1),
                padding=6,
                bgcolor="#1a1a1a",
                border_radius=4,
                height=70
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=2),
        padding=12,
        bgcolor="#0A0A0A",
        border=ft.border.all(2, "#D4AF37"),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000050"),
        on_click=lambda e: selecionar_modelo_visual(4),
        width=118,
        height=138
    )

    modelo_5_container = ft.Container(
        content=ft.Column([
            ft.Text("PREMIUM", size=12, weight="bold", color="#C9A876"),
            ft.Container(
                content=ft.Column([
                    ft.Text("NOME", size=11, weight="bold", color="#1A2F4A"),
                    ft.Text("Data | Nac | Cidade", size=8, color="#5A6C7D"),
                    ft.Text("Email | Tel", size=8, color="#5A6C7D"),
                    ft.Divider(height=2, color="#C9A876"),
                    ft.Text("RESUMO", size=9, weight="bold", color="#1A2F4A"),
                    ft.Text("Seu resumo...", size=7, color="#5A6C7D"),
                    ft.Text("EXPERIÊNCIA", size=9, weight="bold", color="#1A2F4A"),
                    ft.Text("◆ Cargo", size=7, color="#5A6C7D"),
                ], spacing=1),
                padding=6,
                bgcolor="#FAFAFA",
                border_radius=4,
                height=70
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=2),
        padding=12,
        bgcolor="#F5F5F5",
        border=ft.border.all(2, "#C9A876"),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000050"),
        on_click=lambda e: selecionar_modelo_visual(5),
        width=118,
        height=138
    )

    # Guardar referências dos containers
    modelo_containers[1] = modelo_1_container
    modelo_containers[2] = modelo_2_container
    modelo_containers[3] = modelo_3_container
    modelo_containers[4] = modelo_4_container
    modelo_containers[5] = modelo_5_container

    btn_gerar_pdf = ft.ElevatedButton(
        t("gerar_pdf"),
        on_click=gerar_pdf,
        bgcolor=COR_AZUL,
        color="black",
        height=50,
        width=260,
        disabled=True,
    )

    btn_baixar_ultimo_pdf = ft.OutlinedButton(
        t("baixar_ultimo_pdf"),
        on_click=baixar_ultimo_pdf,
        height=50,
        width=260,
    )

    titulo_modelos = ft.Text(t("visualizar_modelos"), color=COR_AZUL, size=16, weight="bold")
    titulo_modelos_ref["control"] = titulo_modelos

    seta_modelos = ft.Icon(name=ft.icons.KEYBOARD_ARROW_DOWN, color=COR_AZUL)
    menu_modelos_ref["control"] = seta_modelos

    modelos_corpo = ft.Column(
        [
            modelo_text,
            ft.Column(
                [
                    criar_opcao_modelo(1, modelo_1_container),
                    criar_opcao_modelo(2, modelo_2_container),
                    criar_opcao_modelo(3, modelo_3_container),
                    criar_opcao_modelo(4, modelo_4_container),
                    criar_opcao_modelo(5, modelo_5_container),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    modelos_corpo_ref["control"] = modelos_corpo

    def toggle_modelos(e):
        modelos_corpo.visible = not modelos_corpo.visible
        seta_modelos.name = ft.icons.KEYBOARD_ARROW_UP if modelos_corpo.visible else ft.icons.KEYBOARD_ARROW_DOWN
        page.update()

    header_modelos = ft.Container(
        content=ft.Row(
            [titulo_modelos, seta_modelos],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        on_click=toggle_modelos,
        padding=ft.padding.symmetric(vertical=8, horizontal=4),
    )

    menu_modelos = ft.Column([header_modelos, modelos_corpo], spacing=0)

    secao_modelos = ft.Container(
        padding=15,
        border_radius=16,
        bgcolor="#171717",
        border=ft.border.all(1, "#2A2A2A"),
        content=ft.Column(
            [
                menu_modelos,
                ft.Column(
                    [btn_gerar_pdf, btn_baixar_ultimo_pdf],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    atualizar_idioma_ui()

    page.add(
        ft.SafeArea(
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("🌍 Idioma do CV", color="white", size=16, weight="bold"),
                    linha_idiomas,
                    ft.Divider(color=COR_AZUL),
                    ft.Text("CURRÍCULO EXPRESSO", size=28, weight="bold", color=COR_AZUL),
                    ft.Divider(color=COR_AZUL),
                    menu_accordion,
                    secao_modelos,
                ],
                spacing=14,
                tight=True,
                ),
            )
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, host="0.0.0.0", port=8550, upload_dir=UPLOAD_DIR, assets_dir="assets")
