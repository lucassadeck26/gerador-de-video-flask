# ----------------------------------------------------
# app.py (O Servidor Web)
# ----------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import helpers
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') 

# Pasta para os "ficheiros de pedido"
JOB_FOLDER = 'jobs'
os.makedirs(JOB_FOLDER, exist_ok=True)

@app.route('/')
def index():
    status = helpers.verificar_status()
    return render_template('index.html', status=status)

@app.route('/status')
def status_check():
    return jsonify(helpers.verificar_status())

@app.route('/etapa1', methods=['GET', 'POST'])
def etapa1_transcricao():
    status = helpers.verificar_status()
    if request.method == 'POST':
        video_id = request.form['video_id']
        if video_id:
            helpers.excluir_arquivo('transcricao')
            with open(os.path.join(JOB_FOLDER, 'job_transcricao.txt'), 'w') as f:
                f.write(video_id)
            flash("Pedido de transcrição enviado! A página irá atualizar quando estiver pronta.")
            return redirect(url_for('etapa2_roteiro'))
    return render_template('etapa1_transcricao.html', status=status)

@app.route('/etapa2', methods=['GET', 'POST'])
def etapa2_roteiro():
    status = helpers.verificar_status()
    if not status['transcricao']:
        flash("Conclua a Etapa 1 primeiro!")
        return redirect(url_for('etapa1_transcricao'))
    if request.method == 'POST':
        with open(os.path.join(JOB_FOLDER, 'job_roteiro.txt'), 'w') as f: f.write('pending')
        flash("Pedido de geração de roteiro enviado! A página irá atualizar.")
    return render_template('etapa2_roteiro.html', status=status)

@app.route('/etapa3', methods=['GET', 'POST'])
def etapa3_narracao():
    status = helpers.verificar_status()
    if not status['roteiro']:
        flash("Conclua a Etapa 2 primeiro!")
        return redirect(url_for('etapa2_roteiro'))
    if request.method == 'POST':
        with open(os.path.join(JOB_FOLDER, 'job_narracao.txt'), 'w') as f: f.write('pending')
        flash("Pedido de geração de narração enviado! A página irá atualizar.")
    return render_template('etapa3_narracao.html', status=status)

@app.route('/etapa4', methods=['GET', 'POST'])
def etapa4_videos_base():
    status = helpers.verificar_status()
    if not status['narracao']:
        flash("Conclua a Etapa 3 primeiro!")
        return redirect(url_for('etapa3_narracao'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'upload':
            helpers.salvar_imagens_upload(request.files.getlist('novas_imagens'))
        elif action == 'renomear':
            helpers.renomear_imagens_em_ordem()
        elif action == 'redimensionar':
            helpers.redimensionar_imagens()
        elif action == 'gerar_videos':
            with open(os.path.join(JOB_FOLDER, 'job_gerar_videos.txt'), 'w') as f: f.write('pending')
            flash("Pedido de geração de vídeos base enviado! A página irá atualizar.")
    return redirect(url_for('etapa4_videos_base'))

@app.route('/etapa5', methods=['GET', 'POST'])
def etapa5_montagem_final():
    status = helpers.verificar_status()
    if not status['videos_base']:
        flash("Conclua a Etapa 4 primeiro!")
        return redirect(url_for('etapa4_videos_base'))
    if request.method == 'POST':
        with open(os.path.join(JOB_FOLDER, 'job_montagem_final.txt'), 'w') as f: f.write('pending')
        flash("Pedido de montagem final enviado! A página irá atualizar.")
    return render_template('etapa5_montagem_final.html', status=status)

@app.route('/etapa6', methods=['GET', 'POST'])
def etapa6_pos_video():
    status = helpers.verificar_status()
    if not status['video_sem_trilha']:
        flash("Conclua a Etapa 5 primeiro!")
        return redirect(url_for('etapa5_montagem_final'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'upload_trilha':
            helpers.salvar_trilhas_upload(request.files.getlist('novas_trilhas'))
        elif action == 'mixar_video':
            trilhas = request.form.getlist('trilhas_selecionadas')
            with open(os.path.join(JOB_FOLDER, 'job_adicionar_trilha.txt'), 'w') as f:
                f.write(','.join(trilhas)) # Salva as trilhas selecionadas
            flash("Pedido de adição de trilha enviado! A página irá atualizar.")
    return redirect(url_for('etapa6_pos_video'))

@app.route('/excluir/<string:etapa>', methods=['POST'])
def excluir(etapa):
    action = request.form.get('action')
    if action == 'delete_all':
        helpers.excluir_arquivo(etapa)
    elif action == 'delete_selected':
        helpers.excluir_arquivo(etapa, arquivos_especificos=request.form.getlist('arquivos_selecionados'))
    return redirect(request.referrer or url_for('index'))

@app.route('/data/<path:filepath>')
def serve_data_file(filepath):
    return send_from_directory('.', filepath)

# ----------------------------------------------------
# worker.py (O Trabalhador de Fundo)
# ----------------------------------------------------
import os
import helpers
import time

JOB_FOLDER = 'jobs'

def process_jobs():
    print(f"[{time.ctime()}] WORKER: Verificando por jobs...")
    
    # Processar Transcrição
    job_path = os.path.join(JOB_FOLDER, 'job_transcricao.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de transcrição encontrado!")
        with open(job_path, 'r') as f: video_id = f.read().strip()
        helpers.gerar_transcricao(video_id)
        os.remove(job_path)
        print("--> WORKER: Job de transcrição concluído.")
        return

    # Processar Roteiro
    job_path = os.path.join(JOB_FOLDER, 'job_roteiro.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de roteiro encontrado!")
        helpers.gerar_roteiro()
        os.remove(job_path)
        print("--> WORKER: Job de roteiro concluído.")
        return

    # Processar Narração
    job_path = os.path.join(JOB_FOLDER, 'job_narracao.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de narração encontrado!")
        helpers.gerar_narracao()
        os.remove(job_path)
        print("--> WORKER: Job de narração concluído.")
        return

    # Processar Geração de Vídeos Base
    job_path = os.path.join(JOB_FOLDER, 'job_gerar_videos.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de geração de vídeos base encontrado!")
        helpers.gerar_videos_base()
        os.remove(job_path)
        print("--> WORKER: Job de geração de vídeos base concluído.")
        return

    # Processar Montagem Final
    job_path = os.path.join(JOB_FOLDER, 'job_montagem_final.txt')
    if os.path.exists(job_path):
        print("--> WORKER: Job de montagem final encontrado!")
        helpers.montar_video_final()
        os.remove(job_path)
        print("--> WORKER: Job de montagem final concluído.")
        return

    # Processar Adição de Trilha
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

# ----------------------------------------------------
# helpers.py (A Lógica Central)
# ----------------------------------------------------
# (O seu ficheiro helpers.py completo e final deve estar aqui.
#  Ele contém todas as funções: verificar_status, gerar_transcricao,
#  gerar_roteiro, gerar_narracao, salvar_imagens_upload, renomear_imagens_em_ordem,
#  redimensionar_imagens, gerar_videos_base, montar_video_final,
#  salvar_trilhas_upload, adicionar_trilha_sonora, e excluir_arquivo.)
# ----------------------------------------------------
