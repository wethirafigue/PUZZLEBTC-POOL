import gspread
from google.oauth2.service_account import Credentials
import hashlib
import logging
import os
import time
from datetime import datetime
from bit import Key
from collections import deque
import random  # Importa a biblioteca random para escolha aleatória de linhas

# Configuração do logging
log_path = os.path.join(os.path.dirname(__file__), 'puzzledb.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Autenticação do Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
client = gspread.authorize(creds)

# Abrir a nova planilha pelo ID
spreadsheet = client.open_by_key("1b_4xb--nH3ZnAmLNPS8BQn5mbMFKcOOKgUWjmDALjnI")
worksheet = spreadsheet.sheet1

# Variáveis globais
contador_tentativas = 0
ultima_chave_tentada = ""  # Agora uma variável global
tentativas_por_segundo = 0
nome_usuario = ""
numero_usuario = ""
linha_usuario = 2  # Linha padrão para o usuário (começando na linha 2)

# Limite de 67 bits
MIN_67_BITS = 0
MAX_67_BITS = 147573952589676412928  # 2^67 - 1, o limite máximo de uma chave de 67 bits

# Fila para armazenar as chaves tentadas nos últimos 10 segundos (em segundos)
tentativas_ultimo_segundo = deque(maxlen=1)  # Agora só vai armazenar a última chave tentada

# Função para validar o formato e o intervalo da chave hexadecimal
def validar_hex(valor):
    try:
        int_valor = int(valor, 16)
        if MIN_67_BITS <= int_valor <= MAX_67_BITS:
            return True
        else:
            logging.warning(f"Valor {valor} está fora do intervalo de 67 bits.")
            return False
    except ValueError:
        logging.warning(f"Valor {valor} não é um hexadecimal válido.")
        return False

# Função para atualizar o status na planilha
def atualizar_status(linha, status, chave_privada=None, wif=None):
    try:
        worksheet.update_cell(linha, 3, status)  # Atualiza o status na coluna C
        if chave_privada:
            worksheet.update_cell(linha, 4, chave_privada)  # Atualiza a última chave tentada na coluna D
        if wif:
            worksheet.update_cell(linha, 5, wif)  # Atualiza o WIF na coluna F
        logging.info(f"Linha {linha} atualizada com status: {status}")
    except Exception as e:
        logging.error(f"Erro ao atualizar o status na linha {linha}: {e}")

# Função para calcular tentativas por segundo
def monitorar_tentativas():
    global contador_tentativas, tentativas_por_segundo
    tentativas_previas = 0
    while True:
        tentativas_por_segundo = contador_tentativas - tentativas_previas
        tentativas_previas = contador_tentativas
        time.sleep(1)

# Função para gerar WIF a partir da chave privada
def gerar_wif(chave_privada_hex):
    try:
        key = Key.from_hex(chave_privada_hex)
        return key.to_wif()
    except Exception as e:
        logging.error(f"Erro ao gerar WIF: {e}")
        return None

# Função para verificar uma chave privada
def verificar_chave_privada(linha, inicio_hex, fim_hex, target_btc, ultima_chave_tentada=None):
    global contador_tentativas
    try:
        # Validar se os intervalos estão corretos
        if not validar_hex(inicio_hex) or not validar_hex(fim_hex):
            logging.warning(f"Linha {linha} ignorada: intervalo inválido {inicio_hex} - {fim_hex}")
            atualizar_status(linha, "Erro")
            return

        inicio_int = int(inicio_hex, 16)
        fim_int = int(fim_hex, 16)

        logging.debug(f"Linha {linha} - Intervalo convertido: {inicio_int} a {fim_int}")

        # Se a coluna D (última chave tentada) tiver valor, começa da chave registrada na coluna D
        if ultima_chave_tentada:
            inicio_int = max(inicio_int, int(ultima_chave_tentada, 16))  # Iniciar da última chave tentada
            logging.info(f"Linha {linha} - Iniciando da última chave tentada registrada em D: {ultima_chave_tentada}")
        else:
            logging.info(f"Linha {linha} - Iniciando a partir da chave em A ({inicio_hex})")

        tentativas_na_linha = 0  # Contador local para as tentativas na linha

        for chave_int in range(inicio_int, fim_int + 1):
            chave_privada_hex = hex(chave_int)[2:].zfill(64)

            contador_tentativas += 1
            ultima_chave_tentada = chave_privada_hex
            tentativas_na_linha += 1  # Incrementa as tentativas da linha

            wif = gerar_wif(chave_privada_hex)
            chave = Key.from_hex(chave_privada_hex)
            endereco = chave.address

            # Adiciona a chave tentada à fila de tentativas nos últimos 10 segundos
            tentativas_ultimo_segundo.append(chave_privada_hex)

            # Exibir a última chave tentada nos últimos 10 segundos
            print(f"Última chave tentada nos últimos 10 segundos: {tentativas_ultimo_segundo[-1]}")

            # Verifica se o endereço gerado é o target
            if endereco == target_btc:
                atualizar_status(linha, "OK", chave_privada_hex, wif)
                logging.info(f"Chave privada encontrada na linha {linha}: {chave_privada_hex}")
                return

            # Atualizar o log da última chave tentada a cada 10.000 tentativas
            if contador_tentativas % 50000 == 0:
                worksheet.update_cell(linha, 4, ultima_chave_tentada)

            # Se atingiu 10.000 tentativas, marcar a linha como "Incompleto" e passar para a próxima linha
            if tentativas_na_linha >= 100000:
                logging.info(f"Linha {linha} - Atingido 10.000 tentativas, passando para a próxima linha.")
                atualizar_status(linha, "INCOMPLETO")
                return

        # Se o processo terminou sem sucesso, atualiza o status como "FEITO"
        atualizar_status(linha, "FEITO")

    except Exception as e:
        logging.error(f"Erro ao verificar chave privada na linha {linha}: {e}")
        atualizar_status(linha, "INCOMPLETO")

# Função para processar intervalos
def processar_intervalos():
    try:
        linhas = worksheet.get_all_values()
        i = random.randint(2, len(linhas) - 1)  # Escolhe uma linha aleatória para começar

        while i < len(linhas):  # Enquanto existirem linhas
            linha = linhas[i]
            
            try:
                # Verifica se o status da linha é 'Procurando'
                if linha[2] == "Procurando":
                    logging.info(f"Linha {i} com status 'Procurando', passando para a próxima linha.")
                    i += 1  # Passa para a próxima linha
                    continue  # Ignora o restante do processamento para esta linha
                
                inicio_hex = linha[0]
                fim_hex = linha[1]
                status = linha[2] if len(linha) > 2 else ""

                if len(linha) > 3 and validar_hex(linha[3]):
                    inicio_hex = linha[3]  # Se houver uma chave específica na coluna D, usa ela como ponto de partida

                if not inicio_hex or not fim_hex:
                    logging.warning(f"Linha {i} ignorada: dados incompletos {linha}")
                    i += 1  # Avança para a próxima linha
                    continue

                # Pega a última chave tentada na coluna D (log), se presente
                ultima_chave = linha[3] if len(linha) > 3 and linha[3] else None

                if status not in ["", "Procurando"]:
                    logging.info(f"Linha {i} já processada com status: {status}")
                    i += 1  # Avança para a próxima linha
                    continue

                # Atualizar status para "Procurando" e salvar o nome e número do usuário
                atualizar_status(i + 1, "Procurando")  # Corrige a linha da atualização do status
                if nome_usuario and numero_usuario:
                    worksheet.update_cell(i + 1, 6, nome_usuario)  # Coluna F para o nome
                    worksheet.update_cell(i + 1, 7, numero_usuario)  # Coluna G para o número

                target_btc = "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so"  # Endereço alvo

                # Processar intervalos sequencialmente
                verificar_chave_privada(i + 1, inicio_hex, fim_hex, target_btc, ultima_chave)

                # Mudar de linha a cada 50.000 tentativas
                if contador_tentativas % 50000 == 0:
                    i = random.randint(2, len(linhas) - 1)  # Escolhe uma nova linha aleatória

            except IndexError:
                logging.warning(f"Linha {i} ignorada: dados insuficientes {linha}")
                i += 1  # Avança para a próxima linha

    except Exception as e:
        logging.error(f"Erro ao processar intervalos: {e}")

# Função para pedir nome e número do usuário e salvar na planilha
def pedir_dados_usuario():
    global nome_usuario, numero_usuario
    nome_usuario = input("Digite seu nome: ")
    numero_usuario = input("Digite seu número: ")

    logging.info(f"Nome e número do usuário: {nome_usuario}, {numero_usuario}")

# Função principal
def main():
    pedir_dados_usuario()
    
    processar_intervalos()

# Executa o script
if __name__ == "__main__":
    main()
