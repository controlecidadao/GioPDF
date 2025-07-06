import streamlit as st
import pytesseract
from PIL import Image
import io
import os
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz  # PyMuPDF
import base64
from pathlib import Path
import subprocess
import json
import shutil

# Configuração da página
st.set_page_config(
    page_title="Gio PDF",
    page_icon="🪁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 30px;
    }
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f8f9fa;
        margin: 20px 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stProgress > div > div > div > div {
        background-color: #2E86AB;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h2 class="main-header">🪁 GioPDF</h2>', unsafe_allow_html=True)
st.markdown('<h4 class="main-header">Conversor PDF para PDF Pesquisável</h4>', unsafe_allow_html=True)

# Função para configurar o Tesseract (ajustar caminho conforme necessário)
def setup_tesseract():
    """Configura o caminho do Tesseract baseado no sistema operacional"""
    
    # Para Windows (ajustar caminho conforme instalação)
    if os.name == 'nt':
        tesseract_paths = [
            fr'{os.getcwd()}\Tesseract-OCR\tesseract.exe', # Caminho do arquivo tesseract.exe no diretório local
            #r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            #r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME')),
            #r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
    
    # Para Linux/Mac, assumir que está no PATH
    try:
        pytesseract.get_tesseract_version()
        return True
    except:
        return False

# Função para converter PDF em imagens usando PyMuPDF
def pdf_to_images(pdf_file, dpi=200):
    """Converte PDF em lista de imagens PIL usando PyMuPDF"""
    try:
        # Ler o PDF usando PyMuPDF
        pdf_bytes = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        images = []
        # Calcular matriz de zoom baseada no DPI
        zoom = dpi / 72.0  # 72 é o DPI padrão
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            
            # Renderizar página como imagem
            pix = page.get_pixmap(matrix=matrix)
            
            # Converter para PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            images.append(pil_image)
        
        pdf_document.close()
        return images
    
    except Exception as e:
        st.error(f"Erro ao converter PDF em imagens: {str(e)}")
        return None

# Função para realizar OCR em uma imagem
def perform_ocr(image, language='por'):
    """Realiza OCR em uma imagem PIL"""
    try:
        # Configurações do OCR
        config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang=language, config=config)
        return text
    except Exception as e:
        st.error(f"Erro no OCR: {str(e)}")
        return ""

# Função para comprimir imagem
def compress_image(image, quality=85, max_size=(1200, 1600)):
    """Comprime uma imagem PIL"""
    # Redimensionar se necessário
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Converter para RGB se necessário
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Comprimir
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='JPEG', quality=quality, optimize=True)
    img_buffer.seek(0)
    
    return Image.open(img_buffer)

# Função para criar PDF pesquisável
def create_searchable_pdf(images, texts, compress=False, quality=85):
    """Cria PDF pesquisável com imagens e texto OCR"""
    try:
        pdf_buffer = io.BytesIO()
        
        # Usar o tamanho da primeira imagem como referência
        if images:
            page_width = images[0].size[0]
            page_height = images[0].size[1]
            page_size = (page_width, page_height)
        else:
            page_size = A4
        
        c = canvas.Canvas(pdf_buffer, pagesize=page_size)
        
        for i, (image, text) in enumerate(zip(images, texts)):
            if compress:
                image = compress_image(image, quality=quality)
            
            # Salvar imagem temporariamente
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=quality if compress else 95)
            img_buffer.seek(0)
            
            # Adicionar imagem à página
            c.drawImage(ImageReader(img_buffer), 0, 0, width=page_size[0], height=page_size[1])
            
            # Adicionar texto invisível para pesquisa
            if text.strip():
                # Configurar texto invisível
                c.setFillColorRGB(1, 1, 1, alpha=0)  # Texto transparente
                c.setFont("Helvetica", 8)
                
                # Dividir texto em linhas e posicionar
                lines = text.split('\n')
                y_position = page_size[1] - 50
                
                for line in lines[:50]:  # Limitar número de linhas
                    if line.strip():
                        try:
                            c.drawString(50, y_position, line[:100])  # Limitar tamanho da linha
                            y_position -= 12
                            if y_position < 50:
                                break
                        except:
                            continue
            
            c.showPage()
        
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    except Exception as e:
        st.error(f"Erro ao criar PDF pesquisável: {str(e)}")
        return None


# Função para obter informações do PDF
def get_pdf_info(pdf_bytes):
    """Obtém informações básicas do PDF"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        info = {
            "pages": doc.page_count,
            "size_mb": len(pdf_bytes) / (1024 * 1024),
            "title": doc.metadata.get("title", "N/A"),
            "author": doc.metadata.get("author", "N/A")
        }
        doc.close()
        return info
    except:
        return None

# Função para extrair texto existente do PDF
def extract_existing_text(pdf_bytes):
    """Extrai texto já existente no PDF"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_pages = []
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_pages.append(text.strip())
        
        doc.close()
        return text_pages
    except:
        return []

# Função para verificar se PDF precisa de OCR
def needs_ocr(pdf_bytes, min_text_length=50):
    """Verifica se o PDF precisa de OCR baseado na quantidade de texto existente"""
    try:
        existing_text = extract_existing_text(pdf_bytes)
        total_text = ' '.join(existing_text)
        
        # Se há pouco texto, provavelmente precisa de OCR
        if len(total_text.strip()) < min_text_length:
            return True, "PDF contém pouco ou nenhum texto"
        
        # Verificar se o texto parece ser de OCR ruim (muitos caracteres especiais)
        special_chars = sum(1 for char in total_text if not char.isalnum() and char not in ' \n\t.,!?;:-')
        if special_chars / len(total_text) > 0.3:
            return True, "PDF pode conter texto de OCR de baixa qualidade"
        
        return False, "PDF já contém texto pesquisável"
    except:
        return True, "Erro ao analisar PDF - aplicando OCR"

# Sidebar com configurações
st.sidebar.header("⚙️ Configurações")

# Configurações de OCR
st.sidebar.subheader("OCR")
ocr_language = st.sidebar.selectbox(
    "Idioma do OCR",
    ["por", "eng", "spa", "fra", "deu", "ita"],
    help="Idioma principal do texto no PDF"
)

language_names = {
    "por": "Português",
    "eng": "Inglês", 
    #"spa": "Espanhol",
    #"fra": "Francês",
    #"deu": "Alemão",
    #"ita": "Italiano"
}

st.sidebar.info(f"Idioma selecionado: {language_names[ocr_language]}")

# Configurações de qualidade
st.sidebar.subheader("Qualidade e Compressão")
dpi_setting = st.sidebar.slider("DPI das imagens", 150, 300, 200, 25)
compress_output = st.sidebar.checkbox("Comprimir PDF de saída", value=True)
compression_quality = st.sidebar.slider("Qualidade da compressão", 50, 95, 85, 5)

# Configurações avançadas
st.sidebar.subheader("Configurações Avançadas")
auto_detect_ocr = st.sidebar.checkbox("Detectar automaticamente se precisa de OCR", value=True)
force_ocr = st.sidebar.checkbox("Forçar OCR mesmo se já houver texto", value=False)

# Verificar se o Tesseract está configurado
if not setup_tesseract():
    st.error("❌ Tesseract não encontrado! Por favor, instale o Tesseract OCR.")
    st.info("💡 Instruções de instalação:")
    st.code("""
    Windows: Baixe em https://github.com/UB-Mannheim/tesseract/wiki
    Linux: sudo apt-get install tesseract-ocr tesseract-ocr-por
    Mac: brew install tesseract
    """)
    st.stop()

# Área de upload
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "📁 Arraste e solte seus arquivos PDF aqui ou clique para selecionar",
    type=['pdf'],
    accept_multiple_files=True,
    help="Selecione um ou mais arquivos PDF para conversão"
)
st.markdown('</div>', unsafe_allow_html=True)





gs_path = fr"{os.getcwd()}\gs10.05.1\bin\gswin64c.exe"  # Caminho do executável
icc_path = fr"{os.getcwd()}\gs10.05.1\iccprofiles\srgb.icc"

def convert_to_pdfa_with_ghostscript(input_pdf_bytes):
    """Converte um PDF comum para PDF/A-2B usando Ghostscript com tratamento de erros melhorado"""
    try:
        # 1. Preparação dos arquivos temporários
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "input.pdf")
        output_path = os.path.join(temp_dir, "output_pdfa.pdf")
        pdfa_def_path = os.path.join(temp_dir, "pdfa_def.ps")
        
        # Escrever o arquivo de entrada
        with open(input_path, "wb") as input_file:
            input_file.write(input_pdf_bytes)
        
        # 2. Configuração do perfil ICC (verificação redundante)
        #icc_dir = os.path.join(os.path.dirname(gs_path), "iccprofiles")
        icc_profile_path = icc_path.replace('\\', '/') #os.path.join(icc_dir, "srgb.icc")
        
        if not os.path.exists(icc_profile_path):
            # Tentar caminho alternativo
            icc_profile_path = os.path.join(os.path.dirname(gs_path), "Resources", "ICC", "sRGB.icc")
            if not os.path.exists(icc_profile_path):
                st.error("Perfil ICC não encontrado. Verifique a instalação do Ghostscript.")
                return None

        # 3. Criar arquivo de definição PDF/A
        pdfa_def_content = f"""%!
[ /Title (Documento convertido)
  /Author (Conversor PDF/A)
  /Subject (Documento PDF/A)
  /Keywords (PDF/A, Digital Preservation)
  /DOCINFO pdfmark

[ /_objdef {{icc_PDFA}} /type /stream /OBJ pdfmark
[ {{icc_PDFA}} << /N 3 >> /PUT pdfmark
[ {{icc_PDFA}} <</Length {os.path.getsize(icc_profile_path)}>> /PUT pdfmark
[ {{icc_PDFA}} ({icc_profile_path}) (r) file /PUT pdfmark

[ /_objdef {{OutputIntent_PDFA}} /type /dict /OBJ pdfmark
[ {{OutputIntent_PDFA}} <<
  /Type /OutputIntent
  /S /GTS_PDFA1
  /DestOutputProfile {{icc_PDFA}}
  /OutputConditionIdentifier (sRGB IEC61966-2.1)
  /Info (sRGB IEC61966-2.1)
>> /PUT pdfmark

[ /_objdef {{Catalog}} /type /dict /OBJ pdfmark
[ {{Catalog}} <<
  /Type /Catalog
  /OutputIntents [ {{OutputIntent_PDFA}} ]
  /MarkInfo << /Marked true >>
>> /PUT pdfmark
"""
        with open(pdfa_def_path, "w", encoding="utf-8") as pdfa_def_file:
            pdfa_def_file.write(pdfa_def_content)

        # 4. Configurar comando Ghostscript
        command = [
            gs_path,
            "-dNOSAFER",  # Permite acesso a arquivos (necessário para alguns casos)
            "-dPDFA=1",
            "-dBATCH",
            "-dNOPAUSE",
            "-dNOOUTERSAVE",
            "-sColorConversionStrategy=RGB",
            "-sProcessColorModel=DeviceRGB",
            "-sDEVICE=pdfwrite",
            "-dPDFACompatibilityPolicy=1",
            f"-sOutputICCProfile={icc_profile_path}",
            f"-sOutputFile={output_path}",
            pdfa_def_path,
            input_path
        ]

        # 5. Executar Ghostscript com tratamento de erro detalhado
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # Timeout de 5 minutos
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except subprocess.TimeoutExpired:
            st.error("Timeout: Ghostscript demorou muito para processar o arquivo")
            return None
        except subprocess.CalledProcessError as e:
            error_details = {
                "returncode": e.returncode,
                "cmd": " ".join(e.cmd),
                "stderr": e.stderr,
                "stdout": e.stdout
            }
            st.error(f"Erro detalhado do Ghostscript:\n{json.dumps(error_details, indent=2)}")
            return None

        # 6. Verificar resultado
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            st.error("Ghostscript não gerou um arquivo de saída válido")
            return None

        # 7. Ler e retornar o PDF/A
        with open(output_path, "rb") as output_file:
            output_bytes = output_file.read()

        return output_bytes

    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None
    finally:
        # Limpeza dos arquivos temporários
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            st.warning(f"Não foi possível limpar arquivos temporários: {str(e)}")

# Processamento dos arquivos
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s) com sucesso!")
    
    # Criar colunas para layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Arquivos para Processamento")
        
        for i, uploaded_file in enumerate(uploaded_files):
            with st.expander(f"📄 {uploaded_file.name}"):
                # Mostrar informações do arquivo
                file_info = get_pdf_info(uploaded_file.read())
                uploaded_file.seek(0)  # Reset file pointer
                
                if file_info:
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric("Páginas", file_info["pages"])
                        st.metric("Tamanho", f"{file_info['size_mb']:.2f} MB")
                    with col_info2:
                        st.text(f"Título: {file_info['title']}")
                        st.text(f"Autor: {file_info['author']}")
                
                # Verificar se precisa de OCR
                if auto_detect_ocr and not force_ocr:
                    needs_ocr_result, ocr_reason = needs_ocr(uploaded_file.read())
                    uploaded_file.seek(0)
                    
                    if needs_ocr_result:
                        st.warning(f"🔍 OCR necessário: {ocr_reason}")
                    else:
                        st.info(f"✅ {ocr_reason}")
    
    with col2:
        st.subheader("🎛️ Controles")
        
        if st.button("🚀 Iniciar Conversão", type="primary", use_container_width=True):
            total_files = len(uploaded_files)
            
            # Barra de progresso geral
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            converted_files = []
            
            for file_idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processando: {uploaded_file.name}")
                
                # Verificar se precisa de OCR
                skip_ocr = False
                if auto_detect_ocr and not force_ocr:
                    needs_ocr_result, ocr_reason = needs_ocr(uploaded_file.read())
                    uploaded_file.seek(0)
                    
                    if not needs_ocr_result:
                        skip_ocr = True
                        status_text.text(f"PDF já pesquisável: {uploaded_file.name}")
                        
                        # Apenas copiar o arquivo original e converter para PDF/A
                        original_pdf = uploaded_file.read()
                        pdfa_pdf = convert_to_pdfa_with_ghostscript(original_pdf)
                        if pdfa_pdf:
                            converted_files.append({
                                'name': uploaded_file.name.replace('.pdf', '_pdfa.pdf'),
                                'data': pdfa_pdf
                            })
                        else:
                            # Se falhar a conversão, salva o PDF original
                            converted_files.append({
                                'name': uploaded_file.name.replace('.pdf', '_original.pdf'),
                                'data': original_pdf
                            })
                        uploaded_file.seek(0)
                        progress_bar.progress((file_idx + 1) / total_files)
                        continue
                
                # Converter PDF em imagens usando PyMuPDF
                progress_bar.progress((file_idx * 4) / (total_files * 4))
                images = pdf_to_images(uploaded_file, dpi=dpi_setting)
                
                if images:
                    # Realizar OCR
                    progress_bar.progress((file_idx * 4 + 1) / (total_files * 4))
                    texts = []
                    
                    for img_idx, image in enumerate(images):
                        text = perform_ocr(image, language=ocr_language)
                        texts.append(text)
                        
                        # Atualizar progresso do OCR
                        ocr_progress = (img_idx + 1) / len(images)
                        total_progress = (file_idx * 4 + 1 + ocr_progress) / (total_files * 4)
                        progress_bar.progress(total_progress)
                    
                    # Criar PDF pesquisável
                    progress_bar.progress((file_idx * 4 + 3) / (total_files * 4))
                    searchable_pdf = create_searchable_pdf(images, texts, compress=compress_output, quality=compression_quality)
                    
                    # Converter para PDF/A
                    if searchable_pdf:
                        pdfa_pdf = convert_to_pdfa_with_ghostscript(searchable_pdf)
                        if pdfa_pdf:
                            converted_files.append({
                                'name': uploaded_file.name.replace('.pdf', '_pdfa.pdf'),
                                'data': pdfa_pdf
                            })
                        else:
                            # Se falhar a conversão, salva o PDF original pesquisável
                            converted_files.append({
                                'name': uploaded_file.name.replace('.pdf', '_pesquisavel.pdf'),
                                'data': searchable_pdf
                            })
                    
                    progress_bar.progress((file_idx * 4 + 4) / (total_files * 4))
                
                uploaded_file.seek(0)  # Reset file pointer
            
            # Finalizar
            progress_bar.progress(1.0)
            status_text.text("✅ Conversão concluída!")
            
            # Mostrar resultados
            if converted_files:
                st.success(f"🎉 {len(converted_files)} arquivo(s) processado(s) com sucesso!")
                
                # Downloads individuais
                st.subheader("📥 Downloads")
                for file_info in converted_files:
                    st.download_button(
                        label=f"⬇️ Baixar {file_info['name']}",
                        data=file_info['data'],
                        file_name=file_info['name'],
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # Download em lote (ZIP)
                if len(converted_files) > 1:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_info in converted_files:
                            zip_file.writestr(file_info['name'], file_info['data'])
                    
                    zip_buffer.seek(0)
                    st.download_button(
                        label="📦 Baixar Todos (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="pdfs_processados.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            else:
                st.error("❌ Nenhum arquivo foi processado com sucesso.")

# Informações adicionais
st.markdown("---")
st.markdown("### 💡 Dicas de Uso")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🎯 Qualidade do OCR**
    - Use DPI alto (200-300) para melhor reconhecimento
    - Selecione o idioma correto
    - PDF com texto nítido funciona melhor
    """)

with col2:
    st.markdown("""
    **📏 Compressão**
    - Ative compressão para arquivos menores
    - Qualidade 85% oferece bom equilíbrio
    - Arquivos grandes podem demorar mais
    """)

with col3:
    st.markdown("""
    **🔍 Detecção Automática**
    - Sistema detecta se PDF precisa de OCR
    - Economiza tempo em PDFs já pesquisáveis
    - Use "Forçar OCR" se necessário
    """)

#st.markdown("---")
#st.markdown("### 🆕 Novidades desta Versão")

#st.info("""
#**✨ Melhorias implementadas:**
#- 🚀 **Sem dependência do pdf2image** - Usa apenas PyMuPDF para conversão
#- 🧠 **Detecção automática de OCR** - Identifica se PDF já é pesquisável
#- ⚡ **Processamento mais rápido** - Menos bibliotecas, mais performance
#- 🔍 **Análise de texto existente** - Evita OCR desnecessário
#- 🎛️ **Controles avançados** - Mais opções de configuração
#""")

st.markdown("---")
st.markdown(
    f"Desenvolvido usando Python, Streamlit, Tesseract OCR e PyMuPDF"
)