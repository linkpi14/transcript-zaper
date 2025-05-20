import streamlit as st
import os
import tempfile
import uuid
import time
from pathlib import Path
import requests
import base64
import re

# Configuração da página
st.set_page_config(
    page_title="Transcrição de Vídeos",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Título e descrição
st.title("🎬 Transcrição de Vídeos")
st.markdown("""
Este aplicativo permite transcrever o conteúdo de áudio de vídeos para texto usando a API do OpenAI Whisper.
Você pode fazer upload de um arquivo ou fornecer um link do YouTube/Instagram (requer download manual).
""")

# Função para criar diretório temporário
@st.cache_resource
def get_temp_dir():
    temp_dir = tempfile.mkdtemp()
    return temp_dir

# Função para transcrever áudio usando a API do OpenAI
def transcribe_with_openai_api(audio_file_path, api_key, language=None):
    try:
        # URL da API do OpenAI para transcrição
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        # Cabeçalhos da requisição
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Parâmetros da requisição
        data = {
            "model": "whisper-1",
        }
        
        # Adicionar idioma se especificado
        if language and language != "":
            data["language"] = language
        
        # Abrir o arquivo de áudio
        with open(audio_file_path, "rb") as f:
            # Enviar a requisição para a API
            files = {
                "file": (os.path.basename(audio_file_path), f, "audio/mpeg")
            }
            
            response = requests.post(url, headers=headers, data=data, files=files)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'text': result.get("text", ""),
                'language': language or "detectado automaticamente",
                'message': 'Transcrição concluída com sucesso'
            }
        else:
            error_message = f"Erro na API: {response.status_code} - {response.text}"
            return {
                'success': False,
                'error': error_message,
                'message': error_message
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Erro ao transcrever áudio: {str(e)}'
        }

# Inicializar o diretório temporário
temp_dir = get_temp_dir()

# Criar abas para diferentes métodos de entrada
tab1, tab2, tab3, tab4 = st.tabs(["Upload de Arquivo", "YouTube (Manual)", "Instagram (Manual)", "Configurações"])

# Lista de idiomas suportados
languages = {
    "": "Detectar automaticamente",
    "pt": "Português",
    "en": "Inglês",
    "es": "Espanhol",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
    "ja": "Japonês",
    "zh": "Chinês",
    "ru": "Russo"
}

# Formatos suportados pela API do Whisper
supported_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']

# Aba de Upload de Arquivo
with tab1:
    st.header("Upload de Arquivo")
    
    # Verificar se a chave API está configurada
    api_key = st.session_state.get("openai_api_key", "")
    
    if not api_key:
        st.warning("⚠️ Chave API da OpenAI não configurada. Por favor, vá para a aba 'Configurações' para adicionar sua chave API.")
    
    st.info(f"Formatos suportados: {', '.join(supported_formats)}")
    
    uploaded_file = st.file_uploader("Escolha um arquivo de áudio ou vídeo", type=supported_formats)
    language_upload = st.selectbox("Idioma (opcional)", options=list(languages.keys()), format_func=lambda x: languages[x], key="language_upload")
    
    if uploaded_file is not None and api_key:
        if st.button("Transcrever Arquivo", key="btn_upload"):
            # Salvar o arquivo temporariamente
            with st.spinner("Processando o arquivo..."):
                # Criar um arquivo temporário
                temp_file = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Transcrever o áudio usando a API da OpenAI
                with st.spinner("Transcrevendo o áudio..."):
                    result = transcribe_with_openai_api(temp_file, api_key, language_upload if language_upload else None)
                
                # Limpar o arquivo temporário
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                # Exibir o resultado
                if result['success']:
                    st.success("Transcrição concluída com sucesso!")
                    st.subheader("Texto Transcrito:")
                    st.text_area("", value=result['text'], height=300, key="text_upload")
                    
                    # Opções para download
                    st.download_button(
                        label="Download TXT",
                        data=result['text'],
                        file_name="transcricao.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"Erro: {result.get('message', 'Falha na transcrição')}")

# Aba do YouTube
with tab2:
    st.header("YouTube (Download Manual)")
    
    st.info("Devido a restrições de autenticação, você precisa baixar o vídeo manualmente e depois fazer upload.")
    
    # Instruções para baixar vídeos do YouTube
    st.subheader("Como baixar vídeos do YouTube:")
    st.markdown("""
    1. Copie o link do vídeo do YouTube
    2. Acesse um dos sites abaixo:
       - [y2mate.com](https://www.y2mate.com/)
       - [savefrom.net](https://en.savefrom.net/)
    3. Cole o link e baixe o vídeo em formato MP3 ou MP4
    4. Volte para a aba "Upload de Arquivo" e faça upload do arquivo baixado
    """)
    
    # Campo para o link do YouTube (apenas para referência)
    youtube_url = st.text_input("Link do YouTube (apenas para referência)", key="youtube_url")
    
    if youtube_url:
        # Validação básica da URL
        if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
            st.success("Link do YouTube válido! Siga as instruções acima para baixar o vídeo.")
            
            # Extrair o ID do vídeo para exibir uma miniatura
            youtube_id = None
            if "youtube.com" in youtube_url and "v=" in youtube_url:
                youtube_id = youtube_url.split("v=")[1].split("&")[0]
            elif "youtu.be" in youtube_url:
                youtube_id = youtube_url.split("/")[-1].split("?")[0]
            
            if youtube_id:
                st.image(f"https://img.youtube.com/vi/{youtube_id}/0.jpg", caption="Miniatura do vídeo")
        else:
            st.error("URL inválida do YouTube")

# Aba do Instagram
with tab3:
    st.header("Instagram (Download Manual)")
    
    st.info("Devido a restrições de autenticação, você precisa baixar o vídeo manualmente e depois fazer upload.")
    
    # Instruções para baixar vídeos do Instagram
    st.subheader("Como baixar vídeos do Instagram:")
    st.markdown("""
    1. Copie o link do vídeo/reels do Instagram
    2. Use um dos métodos abaixo:
       - Aplicativos: "Video Downloader for Instagram", "Reels Downloader"
       - Sites: [inflact.com](https://inflact.com/downloader/instagram/), [snapinsta.app](https://snapinsta.app/)
    3. Baixe o vídeo em formato MP4
    4. Volte para a aba "Upload de Arquivo" e faça upload do arquivo baixado
    """)
    
    # Campo para o link do Instagram (apenas para referência)
    instagram_url = st.text_input("Link do Instagram (apenas para referência)", key="instagram_url")
    
    if instagram_url:
        # Validação básica da URL
        if "instagram.com" in instagram_url:
            st.success("Link do Instagram válido! Siga as instruções acima para baixar o vídeo.")
        else:
            st.error("URL inválida do Instagram")

# Aba de Configurações
with tab4:
    st.header("Configurações")
    
    st.subheader("Chave API da OpenAI")
    
    # Campo para a chave API
    api_key_input = st.text_input(
        "Insira sua chave API da OpenAI",
        value=st.session_state.get("openai_api_key", ""),
        type="password",
        help="Você pode obter uma chave API em https://platform.openai.com/api-keys"
    )
    
    if st.button("Salvar Chave API"):
        st.session_state["openai_api_key"] = api_key_input
        st.success("Chave API salva com sucesso!")
    
    st.markdown("---")
    
    st.subheader("Como obter uma chave API da OpenAI")
    st.markdown("""
    1. Acesse [platform.openai.com](https://platform.openai.com/)
    2. Crie uma conta ou faça login
    3. Vá para "API Keys" no menu
    4. Clique em "Create new secret key"
    5. Dê um nome para sua chave e clique em "Create"
    6. Copie a chave e cole no campo acima
    
    **Nota**: A OpenAI oferece créditos gratuitos para novos usuários, mas depois disso, o serviço é pago. Consulte a [página de preços](https://openai.com/pricing) para mais informações.
    """)
    
    st.markdown("---")
    
    st.subheader("Formatos de arquivo suportados")
    st.markdown(f"""
    A API do Whisper suporta apenas os seguintes formatos:
    - {', '.join(supported_formats)}
    
    Se seu arquivo estiver em outro formato (como AVI ou MOV), você precisará convertê-lo primeiro usando sites como:
    - [Online-convert.com](https://www.online-convert.com/)
    - [Convertio](https://convertio.co/)
    """)

# Informações adicionais
st.markdown("---")
st.markdown("""
### Notas:
- Este aplicativo usa a API do OpenAI Whisper para transcrição
- Você precisa fornecer sua própria chave API da OpenAI
- O tamanho máximo do arquivo é limitado pelo Streamlit (200MB)
- A qualidade da transcrição varia conforme a clareza do áudio
""")

# Rodapé
st.markdown("---")
st.caption("Aplicativo de Transcrição de Vídeos | Desenvolvido com Streamlit")
