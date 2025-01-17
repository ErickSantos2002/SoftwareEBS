import csv
import os
import sys
import time
import serial
import configparser
from threading import Thread
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from src.backend.db import conectar

executando_automatico = False
executando_manual = False

if getattr(sys, 'frozen', False):
    # Diretório do executável (PyInstaller)
    BASE_DIR = os.path.join(sys._MEIPASS)
else:
    # Diretório base para execução no modo script
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Diretório resources no local correto
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")

# Caminhos dos arquivos específicos
ARQUIVO_RESULTADOS = os.path.join(RESOURCES_DIR, "Resultados.csv")
CONFIG_FILE = os.path.join(RESOURCES_DIR, "config.ini")

print("Diretorio base: " + BASE_DIR)
print("Diretorios resources: " + RESOURCES_DIR)

class SignalManager(QObject):
    resultado_atualizado = pyqtSignal()

sinal_global = SignalManager()  # Instância global do gerenciador de sinais

# Função para verificar a existência dos arquivos e criar caso necessário
def inicializar_arquivos():
    """Verifica a existência dos arquivos necessários e cria-os, se necessário."""
    if not os.path.exists(RESOURCES_DIR):
        os.makedirs(RESOURCES_DIR)  # Cria o diretório resources, se não existir

    if not os.path.exists(ARQUIVO_RESULTADOS):
        with open(ARQUIVO_RESULTADOS, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "ID do teste", "ID do usuário", "Nome", "Matrícula", "Setor", "Data e hora", "Quantidade de Álcool", "Status"
            ])
            writer.writeheader()
        print(f"Arquivo criado: {ARQUIVO_RESULTADOS}")

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, mode="w", encoding="utf-8") as file:
            file.write("[Serial]\nporta=\n")
        print(f"Arquivo criado: {CONFIG_FILE}")

# Função para carregar a porta configurada
def carregar_porta_configurada():
    """Carrega a porta configurada do arquivo config.ini."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE) or not config.read(CONFIG_FILE):
        raise Exception("Arquivo de configuração não encontrado ou inválido.")
    porta = config.get("Serial", "porta", fallback=None)
    if not porta:
        raise Exception("Nenhuma porta configurada no arquivo.")
    return porta

def inicializar_serial():
    """Inicializa a conexão serial com a porta configurada."""
    tentativa = 0
    max_tentativas = 3
    while tentativa < max_tentativas:
        try:
            porta = carregar_porta_configurada()
            ser = serial.Serial(
                port=porta,
                baudrate=4800,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            return ser
        except serial.SerialException as e:
            print(f"Tentativa {tentativa + 1}/{max_tentativas}: Erro ao abrir a porta {porta} - {e}")
            tentativa += 1
            time.sleep(1)  # Aguarda 1 segundo antes de tentar novamente
        except Exception as e:
            raise Exception(f"Erro ao inicializar a porta serial: {e}")
    raise Exception("Falha ao inicializar a porta serial após múltiplas tentativas.")

# Função para enviar comandos ao dispositivo
def enviar_comando(comando):
    """Envia um comando ao dispositivo conectado via porta serial."""
    try:
        with inicializar_serial() as ser:
            comando_completo = f"{comando}\r\n"
            ser.write(comando_completo.encode('ascii'))
            print(f"Comando enviado: {comando_completo}")
    except Exception as e:
        print(f"Erro ao enviar comando: {e}")
        raise Exception("Porta serial não está configurada ou aberta.")

# Função para ler resposta do dispositivo
def ler_resposta():
    """Lê a resposta do dispositivo conectado via porta serial."""
    try:
        with inicializar_serial() as ser:
            resposta = ser.readline().decode('ascii').strip()
            print(f"Resposta recebida: {resposta}")
            return resposta
    except Exception as e:
        print(f"Erro ao ler resposta: {e}")
        return None

# Função para obter o próximo ID de teste
def proximo_id_teste():
    """Calcula o próximo ID de teste com base no arquivo CSV."""
    if not os.path.exists(ARQUIVO_RESULTADOS):
        with open(ARQUIVO_RESULTADOS, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "ID do teste", "ID do usuário", "Nome", "Matrícula", "Setor", "Data e hora", "Quantidade de Álcool", "Status"
            ])
            writer.writeheader()
        return 1  # Primeiro ID

    with open(ARQUIVO_RESULTADOS, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        ids = [int(row["ID do teste"]) for row in reader if row["ID do teste"].isdigit()]
        return max(ids) + 1 if ids else 1

from datetime import datetime

# Função para salvar resultados
def salvar_resultado(id_usuario, nome, matricula, setor, data_hora, resultado):
    """Salva o resultado do teste no banco de dados SQLite."""
    quantidade, status = resultado.split("-")  # Exemplo: "0.000-OK" ou "1.125-HIGH"

    # Ajusta o status para "Aprovado" ou "Rejeitado"
    if status == "OK":
        status = "Aprovado"
    elif status == "HIGH":
        status = "Rejeitado"

    # Garante que a data está no formato correto
    if isinstance(data_hora, datetime):
        data_hora = data_hora.strftime("%Y-%m-%d %H:%M:%S")

    # Insere os dados no banco de dados
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO resultados (id_usuario, nome, matricula, setor, data_hora, quantidade_alcool, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_usuario, nome, matricula, setor, data_hora, float(quantidade), status))
        conn.commit()

    # Emite o sinal para notificar que o banco foi atualizado
    sinal_global.resultado_atualizado.emit()

def executar_teste(id_usuario, nome, matricula, setor, automatico=False, callback=None):
    """Executa um teste (manual ou automático) em uma thread separada."""
    def executar():
        global executando_automatico, executando_manual

        if automatico:
            executando_automatico = True
        else:
            executando_manual = True

        respostas_vazias = 0  # Contador para respostas vazias
        max_respostas_vazias = 10  # Limite de respostas vazias antes de falhar

        try:
            while (executando_automatico if automatico else executando_manual):
                try:
                    enviar_comando("$START")
                    print(f"Comando $START enviado para {'teste automático' if automatico else 'teste manual'}.")
                except Exception as e:
                    if callback:
                        # Emite erro para a thread principal
                        callback(f"ERRO-Falha ao enviar comando $START: {e}")
                    return

                while (executando_automatico if automatico else executando_manual):
                    try:
                        resposta = ler_resposta()
                        if not resposta:  # Incrementa o contador para respostas vazias
                            respostas_vazias += 1
                            if respostas_vazias >= max_respostas_vazias:
                                if callback:
                                    # Emite erro para a thread principal
                                    callback("ERRO-Não foi possível conectar ao dispositivo (respostas vazias).")
                                return
                            continue  # Continua aguardando respostas

                        respostas_vazias = 0  # Reseta o contador ao receber uma resposta válida

                        # Chama o callback para todas as respostas relevantes
                        if resposta.startswith("$"):
                            if callback:
                                callback(resposta)
                                
                    except Exception as e:
                        if callback:
                            # Emite erro para a thread principal
                            callback(f"ERRO-Falha ao ler resposta: {e}")
                        return

                    if resposta.startswith("$RESULT"):
                        id_teste = proximo_id_teste()
                        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        resultado = resposta.split(",")[1]
                        quantidade, status = resultado.split("-")

                        salvar_resultado(
                            id_usuario if not automatico else 0,
                            nome if not automatico else "Automático",
                            matricula if not automatico else "Automático",
                            setor if not automatico else "Automático",
                            data_hora,
                            resultado,
                        )
                        print(f"Teste {'automático' if automatico else 'manual'} realizado: {resultado}")

                        if callback:
                            # Envia o resultado final para a thread principal
                            callback(resultado)

                        if automatico and status == "HIGH":
                            print("Resultado HIGH encontrado. Parando testes automáticos.")
                            enviar_comando("$RESET")
                            executando_automatico = False
                            return  

                        if automatico and status == "OK":
                            break

                        if not automatico:
                            enviar_comando("$RESET")
                            executando_manual = False
                            return

                if automatico:
                    time.sleep(1)

        except Exception as e:
            print(f"Erro durante o teste {'automático' if automatico else 'manual'}: {e}")
            if callback:
                # Emite erro para a thread principal
                callback(f"ERRO-{str(e)}")
        finally:
            try:
                enviar_comando("$RESET")
            except Exception as e:
                print(f"Erro ao enviar comando $RESET: {e}")
            executando_automatico = False
            executando_manual = False
            print(f"Teste {'automático' if automatico else 'manual'} interrompido.")

    thread = Thread(target=executar, daemon=True)
    thread.start()
    print(f"Teste {'automático' if automatico else 'manual'} iniciado em thread separada.")


# Funções para iniciar e parar os testes
def iniciar_teste_manual(id_usuario, nome, matricula, setor):
    """Inicia o teste manual."""
    if executando_manual:
        print("Teste manual já está em execução.")
        return
    executar_teste(id_usuario, nome, matricula, setor, automatico=False)

def iniciar_teste_automatico():
    """Inicia o teste automático."""
    if executando_automatico:
        print("Teste automático já está em execução.")
        return
    executar_teste(None, None, None, None, automatico=True)

def parar_testes():
    """Para quaisquer testes em execução (manual ou automático)."""
    global executando_automatico, executando_manual
    executando_automatico = False
    executando_manual = False
    enviar_comando("$RESET")
    print("Todos os testes foram interrompidos.")