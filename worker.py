import os
import helpers
import time
from dotenv import load_dotenv

# Carrega as variáveis de ambiente para o worker também
load_dotenv() 

JOB_FOLDER = 'jobs'

def process_jobs():
    print(f"[{time.ctime()}] WORKER: Verificando por jobs...")
    
    # Processa um job de cada vez, na ordem do fluxo
    job_path = os.path.join(JOB_FOLDER, 'job_transcricao.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de transcrição encontrado!")
        with open(job_path, 'r') as f: video_id = f.read().strip()
        helpers.gerar_transcricao(video_id)
        os.remove(job_path)
        print("--> WORKER: Job de transcrição concluído.")
        return

    job_path = os.path.join(JOB_FOLDER, 'job_roteiro.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de roteiro encontrado!")
        helpers.gerar_roteiro()
        os.remove(job_path)
        print("--> WORKER: Job de roteiro concluído.")
        return

    job_path = os.path.join(JOB_FOLDER, 'job_narracao.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de narração encontrado!")
        helpers.gerar_narracao()
        os.remove(job_path)
        print("--> WORKER: Job de narração concluído.")
        return

    job_path = os.path.join(JOB_FOLDER, 'job_gerar_videos.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de geração de vídeos base encontrado!")
        helpers.gerar_videos_base()
        os.remove(job_path)
        print("--> WORKER: Job de geração de vídeos base concluído.")
        return

    job_path = os.path.join(JOB_FOLDER, 'job_montagem_final.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de montagem final encontrado!")
        helpers.montar_video_final()
        os.remove(job_path)
        print("--> WORKER: Job de montagem final concluído.")
        return

    job_path = os.path.join(JOB_FOLDER, 'job_adicionar_trilha.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de adição de trilha encontrado!")
        with open(job_path, 'r') as f: trilhas = f.read().strip().split(',')
        helpers.adicionar_trilha_sonora(trilhas)
        os.remove(job_path)
        print("--> WORKER: Job de adição de trilha concluído.")
        return

    print(f"[{time.ctime()}] WORKER: Nenhum job encontrado.")

if __name__ == '__main__':
    process_jobs()