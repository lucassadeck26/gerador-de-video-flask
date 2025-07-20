# 1_criar_videos_base.py
import moviepy.editor as mp
import os
import subprocess # Módulo importado para chamar o segundo script

# --- CONFIGURAÇÃO (sem alterações) ---
PASTA_IMAGENS = "imagens"
PASTA_VIDEOS_BASE = "videos"
DURACAO_POR_IMAGEM = 10
LARGURA_VIDEO = 1280
ALTURA_VIDEO = 720
TAMANHO_VIDEO = (LARGURA_VIDEO, ALTURA_VIDEO)

# --- FUNÇÃO AUXILIAR (sem alterações) ---
def criar_clipe_zoom(caminho_imagem, duracao):
    try:
        img_clip_original = mp.ImageClip(caminho_imagem)
        img_clip_cortada = img_clip_original.crop(y_center=img_clip_original.h / 2, height=ALTURA_VIDEO)
        img_clip = img_clip_cortada.set_duration(duracao)

        def calcular_escala(t):
            return 1 + (t / duracao) * 0.35

        img_com_zoom = img_clip.resize(calcular_escala)
        clipe_composto = mp.CompositeVideoClip([img_com_zoom.set_position(('center', 'center'))], size=TAMANHO_VIDEO)
        return clipe_composto
    except Exception as e:
        print(f"ERRO ao processar a imagem {caminho_imagem}: {e}")
        return None

# --- LÓGICA PRINCIPAL DO SCRIPT 1 (com adição no final) ---

if not os.path.exists(PASTA_VIDEOS_BASE):
    os.makedirs(PASTA_VIDEOS_BASE)
    print(f"Pasta '{PASTA_VIDEOS_BASE}' criada.")

print(f"Procurando imagens em '{PASTA_IMAGENS}'...")
arquivos_na_pasta = sorted(os.listdir(PASTA_IMAGENS))
imagens_a_processar = [f for f in arquivos_na_pasta if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not imagens_a_processar:
    print("Nenhuma imagem encontrada para processar.")
    exit()

print(f"Encontradas {len(imagens_a_processar)} imagens. Iniciando a criação dos vídeos base...")

for nome_arquivo_img in imagens_a_processar:
    caminho_imagem = os.path.join(PASTA_IMAGENS, nome_arquivo_img)
    nome_base, _ = os.path.splitext(nome_arquivo_img)
    nome_arquivo_video = f"{nome_base}.mp4"
    caminho_video_saida = os.path.join(PASTA_VIDEOS_BASE, nome_arquivo_video)

    if os.path.exists(caminho_video_saida):
        print(f"Vídeo '{nome_arquivo_video}' já existe. Pulando.")
        continue

    print(f"Criando clipe para '{nome_arquivo_img}'...")
    clipe_para_salvar = criar_clipe_zoom(caminho_imagem, DURACAO_POR_IMAGEM)

    if clipe_para_salvar:
        clipe_para_salvar.write_videofile(caminho_video_saida, fps=30, codec="libx264", logger='bar')
        print(f"-> Salvo como '{nome_arquivo_video}'")

print("\nCriação dos vídeos base finalizada!")

# --- ADIÇÃO PARA CHAMAR O SEGUNDO SCRIPT ---
print("\n----------------------------------------------------")
print("Iniciando a montagem do vídeo final...")
print("----------------------------------------------------")

# Nome do segundo script
NOME_SEGUNDO_SCRIPT = "montar_video_final.py"

# Executa o segundo script usando o mesmo interpretador Python (python3)
# O argumento 'check=True' fará com que o script pare se houver um erro no segundo script.
try:
    subprocess.run(["python3", NOME_SEGUNDO_SCRIPT], check=True)
except FileNotFoundError:
    print(f"ERRO: O script '{NOME_SEGUNDO_SCRIPT}' não foi encontrado. Verifique o nome do arquivo.")
except Exception as e:
    print(f"Ocorreu um erro ao executar o segundo script: {e}")