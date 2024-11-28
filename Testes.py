import tkinter as tk
from tkinter import messagebox, ttk
import csv
from datetime import datetime
import serial
import time
import os
from threading import Thread
from Configuracoes import obter_serial_configurada

# Nome do arquivo CSV para resultados
ARQUIVO_RESULTADOS = "Resultados.csv"

# Obtemos a instância da porta serial configurada
try:
    ser = obter_serial_configurada()
except Exception as e:
    print(f"Erro ao configurar a porta serial: {e}")
    exit()

# Função para enviar comandos ao dispositivo
def enviar_comando(comando):
    try:
        ser = obter_serial_configurada()
        comando_completo = f"{comando}\r\n"
        ser.write(comando_completo.encode('ascii'))
        print(f"Comando enviado: {comando_completo}")
    except Exception as e:
        print(f"Erro ao enviar comando: {e}")
        raise Exception("Porta serial não está configurada ou aberta.")
    finally:
        if ser and ser.is_open:
            ser.close()

# Função para ler resposta do dispositivo
def ler_resposta():
    try:
        ser = obter_serial_configurada()
        resposta = ser.readline().decode('ascii').strip()
        print(f"Resposta recebida: {resposta}")
        return resposta
    except Exception as e:
        print(f"Erro ao ler resposta: {e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()

# Função para obter o próximo ID de teste
def proximo_id_teste():
    # Se o arquivo não existir, cria com o cabeçalho inicial
    if not os.path.exists(ARQUIVO_RESULTADOS):
        with open(ARQUIVO_RESULTADOS, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "ID do teste", "ID do usuário", "Nome", "Matrícula", "Setor", "Data e hora", "Quantidade de Álcool", "Status"
            ])
            writer.writeheader()
        return 1  # Primeiro ID

    # Ler o arquivo para obter os IDs existentes
    with open(ARQUIVO_RESULTADOS, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        try:
            # Filtra e converte os IDs existentes
            ids = [int(row["ID do teste"]) for row in reader if row["ID do teste"].isdigit()]
            return max(ids) + 1 if ids else 1  # Retorna o próximo ID
        except KeyError:
            # Caso o arquivo não tenha o cabeçalho correto, recria o arquivo
            with open(ARQUIVO_RESULTADOS, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=[
                    "ID do teste", "ID do usuário", "Nome", "Matrícula", "Setor", "Data e hora", "Quantidade de Álcool", "Status"
                ])
                writer.writeheader()
            return 1
        
def salvar_resultado(id_teste, id_usuario, nome, matricula, setor, data_hora, resultado):
    # Extrai quantidade e status do resultado
    quantidade, status = resultado.split("-")  # Exemplo: "0.000-OK" ou "1.125-HIGH"
    
    # Salva no CSV com as colunas separadas
    with open("Resultados.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([id_teste, id_usuario, nome, matricula, setor, data_hora, quantidade, status])
    print("Resultado salvo com sucesso!")

# Variável global para controle do modo automático
executando_automatico = False

# Lógica para iniciar a janela de testes
def iniciar_testes():
    global executando_automatico

    def iniciar_manual():
        selecionado = tree.selection()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione um usuário para realizar o teste!")
            return

        usuario = tree.item(selecionado)["values"]
        id_usuario, nome, matricula, setor = usuario

        id_teste = proximo_id_teste()
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        enviar_comando("$START")
        while True:
            resposta = ler_resposta()
            if resposta.startswith("$START"):
                resultado = resposta.split(",")[1]  # Exemplo: 0.000-OK
                salvar_resultado(id_teste, id_usuario, nome, matricula, setor, data_hora, resultado)
                messagebox.showinfo("Sucesso", "Teste realizado com sucesso!")
                break

    def iniciar_automatico():
        global executando_automatico
        executando_automatico = True

        def loop_automatico():
            while executando_automatico:
                id_teste = proximo_id_teste()
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                enviar_comando("$START")  # Inicia o teste
                while executando_automatico:
                    resposta = ler_resposta()
                    if resposta.startswith("$START"):
                        resultado = resposta.split(",")[1]  # Exemplo: 0.000-OK ou 1.125-HIGH
                        salvar_resultado(id_teste, "Automático", "Automático", "Automático", "Automático", data_hora, resultado)
                        print("Teste automático realizado com sucesso!")

                        # Se resultado for HIGH, parar automaticamente e exibir mensagem
                        if "HIGH" in resultado:
                            print("Resultado HIGH detectado. Parando testes automáticos.")
                            parar_automatico()  # Para o loop e envia $RESET
                            messagebox.showwarning(
                                "Aviso de Segurança",
                                "Um teste com álcool foi detectado.\n"
                                "Por questões de segurança, recomenda-se aguardar 5 minutos antes de retomar os testes."
                            )
                            return  # Encerra o loop automático

                        break
                    elif not executando_automatico:
                        break
                time.sleep(1)  # Pausa geral entre os testes

        Thread(target=loop_automatico, daemon=True).start()


    def parar_automatico():
        global executando_automatico
        executando_automatico = False
        enviar_comando("$RESET")  # Envia o comando RESET ao dispositivo
        print("Teste automático interrompido.")

    # Interface da janela de testes
    testes_root = tk.Tk()
    testes_root.title("Realizar Testes")
    testes_root.geometry("1000x400")
    testes_root.resizable(False, False)

    # Frame para selecionar o tipo de teste
    frame_tipo = tk.Frame(testes_root)
    frame_tipo.pack(side="top", fill="x", padx=10, pady=10)

    tk.Label(frame_tipo, text="Selecione o tipo de teste:").pack(side="left", padx=5)
    tk.Button(frame_tipo, text="Manual", command=lambda: mostrar_manual()).pack(side="left", padx=5)
    tk.Button(frame_tipo, text="Automático", command=lambda: mostrar_automatico()).pack(side="left", padx=5)

    # Frames para os modos Manual e Automático
    frame_manual = tk.Frame(testes_root)
    frame_automatico = tk.Frame(testes_root)

    # Função para exibir modo Manual
    def mostrar_manual():
        frame_automatico.pack_forget()
        frame_manual.pack(fill="both", expand=True)

    # Função para exibir modo Automático
    def mostrar_automatico():
        frame_manual.pack_forget()
        frame_automatico.pack(fill="both", expand=True)

    # Configurações do modo Manual
    tk.Label(frame_manual, text="Selecione um usuário:").pack(pady=5)
    tree = ttk.Treeview(
        frame_manual, 
        columns=("ID", "Nome", "Matrícula", "Setor"), 
        show="headings", 
        selectmode="browse"  # Permite selecionar apenas um item
    )
    tree.heading("ID", text="ID")
    tree.heading("Nome", text="Nome")
    tree.heading("Matrícula", text="Matrícula")
    tree.heading("Setor", text="Setor")
    tree.pack(fill="both", expand=True)

    def carregar_usuarios():
        if not os.path.exists("registros.csv"):
            return
        with open("registros.csv", mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tree.insert("", "end", values=(row["ID"], row["Nome"], row["Matricula"], row["Setor"]))

    carregar_usuarios()
    tk.Button(frame_manual, text="Iniciar Teste", command=iniciar_manual).pack(pady=10)

    # Configurações do modo Automático
    tk.Button(frame_automatico, text="Iniciar Testes Automáticos", command=iniciar_automatico).pack(pady=10)
    tk.Button(frame_automatico, text="Parar Testes Automáticos", command=parar_automatico).pack(pady=10)

    testes_root.mainloop()

# Para executar como standalone
if __name__ == "__main__":
    iniciar_testes()
