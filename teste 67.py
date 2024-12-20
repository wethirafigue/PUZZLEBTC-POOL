import gspread
from google.oauth2.service_account import Credentials
import hashlib
import logging
import os
import time
from datetime import datetime
from bit import Key
from collections import deque
import random

# Configuração do logging
log_path = os.path.join(os.path.dirname(__file__), 'keyhant.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Credenciais do serviço Google diretamente do JSON
direct_service_account_info = {
    "type": "service_account",
    "project_id": "custom-graph-430902-k4",
    "private_key_id": "0b18e617f08bc423b02760dc383393b57730a940",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDD+9xQ7fdl06jY\nhNKy5EZJ47aqpIel6AArTo3H0d7YpczgEE9kmHhNROoCuRHioQ1k/cuyVTaE7e90\nFqR+dfpf8FEhRqwY80aGSbVLRoUq/+OsJlmvueXGKFEmD5iWl0C0qsE9ZHi3v/O7\nBGackN1o/DsZrBowpHZpOeaomaQ6HbIc/3IHrlJXASb3lw5o1zW5fF/Qor9g+9UJ\nasv9UoWUU+eR5S4aKelkc2zD4nFIl4beyCLGKjzruZfHxLRKEkGR73OBcuofk7+5\nv+OLJj5LUOispzTteEbI3kBa4P8Db2qpVJ5KYdLJ98eM5uENj93TXqpZRu8t0R93\na5C5EX43AgMBAAECggEAFlDrBOIb7iHcU49ISKt6n3ZI+gRTF96jikrfFRY+OFAk\n1Iy25Z8A79d9iALX2QT6t/m4RJ20YA2R2xeq8mVvtZXxPwdDmHG3IZpqBODKUBuk\nKpmRU9OoqNg1aU6UUu11Jj1dVKbIoi++yphVMNXECGzUM/enYcuQWioILEGWdDFz\nTRySCraFryP9M+DACMEVPVXfjXT6hM54bNu4PZeQAQeyscFrT0OSlltM6cKV/Sj+\n+2WJPBmUvTpNIAtd1tOpWJDGRN2t+K4hCIHUlWsV08Ia6IMBsiHp/9jM/XoLW4je\nWBJzjjnlppzAJaeEqb4lbRVWmzx6Bw6jjKlgRmb27QKBgQDxC4XZlJVMiYM/uuqX\n1S0xCclOdoUQBDP4yf+56uQRqE02pPgZD1nDKA5AXUXwTsfvHVO23I5488+DATdz\nWb4/QUUB5bDa34okbbZbo/A/E1jAtGUNjUEcS4bcP0ECb0Ajkmxrc2j+s2BSNBqx\nbFTYd3M2gfJ5W0knuvS7uJse3QKBgQDQJKN+XkFeY7CPTRKx1psluYYh28UlHwhG\n4+eyXi7vH+wmCzsFRdsUn2/rM85OUPaBvFNY3mFDmy/cvnBfewoyOy/TpZr1JiJI\nGmK4azo1QQ/+By8XILI/TcAPjdd/YWxCPMT683a7RLNkCxdn3RlcsPyZMlIZ74e5\nU0m9j+H+IwKBgCs+AvQmmKYTYU1UjfNRFftfIxMFZheaeWxfaJYE0odsZvWvoKZ2\nP4coL25SjVJv/6Qg4bzDUnfWXVrGJBl4dw3H+sY9W33YbmLcn8NO5LGcGebwNdS5\ni320+uuWGWaDaME46mRYXvSaX2Q/3q4Hniz7ONsFcudcfgI3ouHuWz2tAoGAQhhQ\nXpF5uop3h5nW5OgcDkeyg0/xc48+Jpy6d5aW2tJNP+tzC4KaRhs3A/5IdfAZxyrR\nYLgFNN2zviovLvK4UykeT9wXr98zJahTTvKl4kFN3cHUP0jfsWB0K7xEASwjn4kC\nmBn1yxPOz2cCQLYiFqARJminT5sTg1MiaHKnNfcCgYEA5APTsZhMNHQH69EKIVRV\nJ7OysXI6omaujo0k6A8H6tMJfD0lk83Mk4HRt7YPrvWh5PJp5bmwM9xWnhf2NcGs\n6HCvG4V+E340gzJ/oT2/ZyrvV9e37oMyMDMOZkg6NqugelfWGMDxz0pBOWNNecsE\nFawAC/02VxmUGnztTLjrup0=\n-----END PRIVATE KEY-----\n",
    "client_email": "keys67@custom-graph-430902-k4.iam.gserviceaccount.com",
    "client_id": "116465809912493133789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/keys67%40custom-graph-430902-k4.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(direct_service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Abrir a planilha pelo ID
spreadsheet = client.open_by_key("1b_4xb--nH3ZnAmLNPS8BQn5mbMFKcOOKgUWjmDALjnI")
worksheet = spreadsheet.sheet1


# Variáveis globais
contador_tentativas = 0
ultima_chave_tentada = ""
tentativas_por_segundo = 0
nome_usuario = ""
numero_usuario = ""
linha_usuario = 2  # Linha padrão para o usuário (começando na linha 2)

# Limite de 67 bits
MIN_67_BITS = 0
MAX_67_BITS = 147573952589676412928  # 2^67 - 1, o limite máximo de uma chave de 67 bits

# Fila para armazenar as chaves tentadas nos últimos 10 segundos (em segundos)
tentativas_ultimo_segundo = deque(maxlen=1)  # Agora só vai armazenar a última chave tentada

# Variável para calcular o tempo e a taxa de tentativas por segundo
inicio_tempo = time.time()

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
    global contador_tentativas, inicio_tempo
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

            # Verifica se o endereço gerado é o target
            if endereco == target_btc:
                atualizar_status(linha, "OK", chave_privada_hex, wif)
                logging.info(f"Chave privada encontrada na linha {linha}: {chave_privada_hex}")
                
            
             # Exibir mensagem "Ganhamos!" e interromper o processo
                print("Ganhamos! Encontrei o WIF.")
                # Adicionar a mensagem de sucesso ao log
                logging.info("Ganhamos! Encontramos o WIF e o endereço correspondente.")
                return  # Interrompe a execução da função, parando o processo
            
            
            # Atualizar o log da última chave tentada a cada 100.000 tentativas
            if contador_tentativas % 100000 == 0:
                worksheet.update_cell(linha, 4, ultima_chave_tentada)
                print(f"Última chave enviada para o Google Sheets: {ultima_chave_tentada}")

            # Exibir informações a cada 50.000 tentativas
            if contador_tentativas % 50000 == 0:
                # Calcular o tempo e quantidade de tentativas por segundo
                tempo_decorrido = time.time() - inicio_tempo
                tentativas_por_segundo = contador_tentativas / tempo_decorrido
                print(f"Quantidade de chaves tentadas por segundo: {tentativas_por_segundo:.2f}")
                print(f"Intervalo atual: {inicio_hex} a {fim_hex}")
                print(f"Última chave tentada: {ultima_chave_tentada}")
                inicio_tempo = time.time()  # Reiniciar o cronômetro para o próximo cálculo

            # Se atingiu 100.000 tentativas, marcar a linha como "Incompleto" e passar para a próxima linha
            if tentativas_na_linha >= 1000000:
                logging.info(f"Linha {linha} - Atingido 100.000 tentativas, passando para a próxima linha.")
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

                target_btc = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"  # Endereço alvo

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
