# helpers.py
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai
from google.cloud import texttospeech
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import moviepy.editor as mp
import moviepy.audio.fx.all as afx
from PIL import Image
import numpy as np

# Carrega as variáveis de ambiente (como a GOOGLE_API_KEY) do seu ficheiro .env
# O worker.py também precisa de carregar estas variáveis
load_dotenv()

# Definição de todas as pastas do projeto
PASTA_IMAGENS = "imagens"
PASTA_VIDEOS_BASE = "videos"
PASTA_TRANSCRICAO = "transcricao"
PASTA_ROTEIRO = "roteiro_narracao"
PASTA_NARRACAO = "narracao"
PASTA_VIDEO_SEM_TRILHA = "video_sem_trilha"
PASTA_TRILHA_SONORA = "trilha_sonora"
PASTA_VIDEO_FINAL = "video_final"

def verificar_status():
    """Verifica a existência de ficheiros em cada pasta para determinar o estado do projeto."""
    status = {
        'transcricao': None, 'roteiro': None, 'narracao': None,
        'imagens': [], 'videos_base': [], 
        'video_sem_trilha': None, 'trilha_sonora': [], 'video_final': None
    }
    # A lógica de verificação está correta e verifica todas as pastas
    if os.path.exists(PASTA_TRANSCRICAO) and any(f.endswith('.txt') for f in os.listdir(PASTA_TRANSCRICAO)):
        status['transcricao'] = os.listdir(PASTA_TRANSCRICAO)[0]
    if os.path.exists(PASTA_ROTEIRO) and any(f.endswith('.txt') for f in os.listdir(PASTA_ROTEIRO)):
        status['roteiro'] = os.listdir(PASTA_ROTEIRO)[0]
    if os.path.exists(PASTA_NARRACAO) and any(f.endswith('.mp3') for f in os.listdir(PASTA_NARRACAO)):
        status['narracao'] = os.listdir(PASTA_NARRACAO)[0]
    if os.path.exists(PASTA_IMAGENS):
        status['imagens'] = sorted([f for f in os.listdir(PASTA_IMAGENS) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if os.path.exists(PASTA_VIDEOS_BASE):
        status['videos_base'] = sorted([f for f in os.listdir(PASTA_VIDEOS_BASE) if f.lower().endswith('.mp4')])
    if os.path.exists(PASTA_VIDEO_SEM_TRILHA) and any(f.endswith('.mp4') for f in os.listdir(PASTA_VIDEO_SEM_TRILHA)):
        status['video_sem_trilha'] = os.listdir(PASTA_VIDEO_SEM_TRILHA)[0]
    if os.path.exists(PASTA_TRILHA_SONORA):
        status['trilha_sonora'] = sorted([f for f in os.listdir(PASTA_TRILHA_SONORA) if f.lower().endswith('.mp3')])
    if os.path.exists(PASTA_VIDEO_FINAL) and any(f.endswith('.mp4') for f in os.listdir(PASTA_VIDEO_FINAL)):
        status['video_final'] = os.listdir(PASTA_VIDEO_FINAL)[0]
    return status

def excluir_arquivo(etapa, arquivos_especificos=None):
    """Exclui ficheiros de uma determinada etapa."""
    pastas = {
        'transcricao': PASTA_TRANSCRICAO, 'roteiro': PASTA_ROTEIRO, 'narracao': PASTA_NARRACAO,
        'imagens': PASTA_IMAGENS, 'videos_base': PASTA_VIDEOS_BASE,
        'video_sem_trilha': PASTA_VIDEO_SEM_TRILHA, 'trilha_sonora': PASTA_TRILHA_SONORA,
        'video_final': PASTA_VIDEO_FINAL
    }
    pasta_alvo = pastas.get(etapa)
    if not (pasta_alvo and os.path.exists(pasta_alvo)): return False
    
    arquivos = arquivos_especificos if arquivos_especificos else os.listdir(pasta_alvo)
    for nome_ficheiro in arquivos:
        caminho_ficheiro = os.path.join(pasta_alvo, nome_ficheiro)
        if os.path.exists(caminho_ficheiro): os.remove(caminho_ficheiro)
    return True

# --- Funções das Etapas ---

def gerar_transcricao(video_id, idioma='es'):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[idioma])
        full_transcript = " ".join([segment['text'] for segment in transcript_list])
        os.makedirs(PASTA_TRANSCRICAO, exist_ok=True)
        excluir_arquivo('transcricao')
        output_filename = f"transcricao_{idioma}_{video_id}.txt"
        with open(os.path.join(PASTA_TRANSCRICAO, output_filename), "w", encoding="utf-8") as f: f.write(full_transcript)
        return True, f"Transcrição '{output_filename}' criada!"
    except Exception as e:
        print(f"Erro ao gerar transcrição: {e}")
        return False, f"Erro ao gerar transcrição: {e}"

def gerar_roteiro():
    try:
        status = verificar_status()
        with open(os.path.join(PASTA_TRANSCRICAO, status['transcricao']), "r", encoding="utf-8") as f:
            conteudo_transcricao = f.read()
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        prompt = f"Você é uma fã da novela Gabriela. Reescreva o seguinte resumo em espanhol de forma informal, cativante e com humor leve, adicionando detalhes e um call to action para redes sociais. O texto deve ter cerca de 2500 palavras e ser narrado por uma mulher. Não inclua títulos. Resumo: {conteudo_transcricao}"
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        os.makedirs(PASTA_ROTEIRO, exist_ok=True)
        excluir_arquivo('roteiro')
        nome_ficheiro = f"roteiro_{status['transcricao']}"
        with open(os.path.join(PASTA_ROTEIRO, nome_ficheiro), "w", encoding="utf-8") as f: f.write(response.text)
        return True, f"Roteiro '{nome_ficheiro}' criado!"
    except Exception as e:
        print(f"Erro ao gerar roteiro: {e}")
        return False, f"Erro ao gerar roteiro: {e}"

def gerar_narracao():
    try:
        status = verificar_status()
        with open(os.path.join(PASTA_ROTEIRO, status['roteiro']), "r", encoding="utf-8") as f:
            texto = f.read()
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=texto)
        voice = texttospeech.VoiceSelectionParams(language_code="es-US", name="es-US-Studio-B")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        os.makedirs(PASTA_NARRACAO, exist_ok=True)
        excluir_arquivo('narracao')
        nome_ficheiro = f"narracao_{os.path.splitext(status['roteiro'])[0]}.mp3"
        with open(os.path.join(PASTA_NARRACAO, nome_ficheiro), "wb") as out: out.write(response.audio_content)
        return True, f"Narração '{nome_ficheiro}' criada!"
    except Exception as e:
        print(f"Erro ao gerar narração: {e}")
        return False, f"Erro ao gerar narração: {e}"

def salvar_imagens_upload(arquivos):
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    for arquivo in arquivos:
        if arquivo and arquivo.filename != '':
            arquivo.save(os.path.join(PASTA_IMAGENS, secure_filename(arquivo.filename)))
    return True

def renomear_imagens_em_ordem():
    try:
        imagens = verificar_status()['imagens']
        caminhos_temp = [os.path.join(PASTA_IMAGENS, f) + ".tmp" for f in imagens]
        for i, f in enumerate(imagens): os.rename(os.path.join(PASTA_IMAGENS, f), caminhos_temp[i])
        for i, temp_path in enumerate(caminhos_temp):
            ext = os.path.splitext(temp_path.replace(".tmp", ""))[1]
            os.rename(temp_path, os.path.join(PASTA_IMAGENS, f"{i+1}{ext}"))
        return True, "Imagens renomeadas."
    except Exception as e:
        return False, f"Erro ao renomear: {e}"

def redimensionar_imagens():
    try:
        imagens = verificar_status()['imagens']
        tamanho_alvo = (1280, 720)
        redimensionadas = 0
        for nome in imagens:
            caminho = os.path.join(PASTA_IMAGENS, nome)
            with Image.open(caminho) as img:
                if img.size != tamanho_alvo:
                    img.resize(tamanho_alvo, Image.Resampling.LANCZOS).save(caminho)
                    redimensionadas += 1
        return True, f"{redimensionadas} imagens redimensionadas."
    except Exception as e:
        return False, f"Erro ao redimensionar: {e}"

def criar_clipe_zoom_para_imagem(caminho_imagem, tipo_zoom, duracao=10):
    LARGURA, ALTURA = 1280, 720
    img_clip = mp.ImageClip(caminho_imagem).set_duration(duracao)
    def efeito(get_frame, t):
        frame = get_frame(t)
        pil_img = Image.fromarray(frame)
        escala = 1.0 + (t / duracao) * 0.35
        img_redimensionada = pil_img.resize((int(pil_img.width * escala), int(pil_img.height * escala)), resample=Image.Resampling.LANCZOS)
        excesso_w, excesso_h = img_redimensionada.width - LARGURA, img_redimensionada.height - ALTURA
        fator_t = t / duracao
        if tipo_zoom == 'direita': left, upper = fator_t * excesso_w, fator_t * excesso_h
        elif tipo_zoom == 'esquerda': left, upper = (1 - fator_t) * excesso_w, (1 - fator_t) * excesso_h
        else: left, upper = excesso_w / 2, excesso_h / 2
        return np.array(img_redimensionada.crop((left, upper, left + LARGURA, upper + ALTURA)))
    return img_clip.fl(efeito)

def gerar_videos_base():
    try:
        imagens = verificar_status()['imagens']
        os.makedirs(PASTA_VIDEOS_BASE, exist_ok=True)
        tipos_zoom = ['direita', 'esquerda', 'centro']
        criados = 0
        for i, nome_img in enumerate(imagens):
            nome_video = f"{os.path.splitext(nome_img)[0]}.mp4"
            if not os.path.exists(os.path.join(PASTA_VIDEOS_BASE, nome_video)):
                tipo = tipos_zoom[i % len(tipos_zoom)]
                clipe = criar_clipe_zoom_para_imagem(os.path.join(PASTA_IMAGENS, nome_img), tipo)
                clipe.write_videofile(os.path.join(PASTA_VIDEOS_BASE, nome_video), fps=30)
                criados += 1
        return True, f"{criados} vídeos base gerados."
    except Exception as e:
        return False, f"Erro ao gerar vídeos base: {e}"

def montar_video_final():
    try:
        status = verificar_status()
        audio_clip = mp.AudioFileClip(os.path.join(PASTA_NARRACAO, status['narracao']))
        clips_video = [mp.VideoFileClip(os.path.join(PASTA_VIDEOS_BASE, v)) for v in status['videos_base']]
        video_loop = mp.vfx.loop(mp.concatenate_videoclips(clips_video, method="compose"), duration=audio_clip.duration)
        video_com_audio = video_loop.set_audio(audio_clip)
        os.makedirs(PASTA_VIDEO_SEM_TRILHA, exist_ok=True)
        excluir_arquivo('video_sem_trilha')
        caminho_saida = os.path.join(PASTA_VIDEO_SEM_TRILHA, "video_sem_trilha.mp4")
        video_com_audio.write_videofile(caminho_saida, fps=30, codec="libx264")
        return True, "Vídeo (sem trilha) montado!"
    except Exception as e:
        return False, f"Erro ao montar vídeo: {e}"

def salvar_trilhas_upload(arquivos):
    os.makedirs(PASTA_TRILHA_SONORA, exist_ok=True)
    for arquivo in arquivos:
        if arquivo and arquivo.filename != '':
            arquivo.save(os.path.join(PASTA_TRILHA_SONORA, secure_filename(arquivo.filename)))
    return True

def adicionar_trilha_sonora(nomes_trilhas, volume=0.15):
    try:
        status = verificar_status()
        video_clip = mp.VideoFileClip(os.path.join(PASTA_VIDEO_SEM_TRILHA, status['video_sem_trilha']))
        clips_trilha = [mp.AudioFileClip(os.path.join(PASTA_TRILHA_SONORA, n)) for n in nomes_trilhas]
        trilha_loop = afx.audio_loop(mp.concatenate_audioclips(clips_trilha), duration=video_clip.duration)
        audio_mixado = mp.CompositeAudioClip([video_clip.audio, trilha_loop.volumex(volume)])
        video_final = video_clip.set_audio(audio_mixado)
        os.makedirs(PASTA_VIDEO_FINAL, exist_ok=True)
        excluir_arquivo('video_final')
        caminho_saida = os.path.join(PASTA_VIDEO_FINAL, "video_final_com_trilha.mp4")
        video_final.write_videofile(caminho_saida, fps=30, codec="libx264")
        return True, "Vídeo final com trilha sonora está pronto!"
    except Exception as e:
        return False, f"Erro ao adicionar trilha: {e}"
