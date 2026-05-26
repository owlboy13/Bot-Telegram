import asyncio
import random
import os
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError

load_dotenv()

API_ID = os.getenv('API_ID_FINANCEIRO')
API_HASH = os.getenv('API_HASH_FINANCEIRO')
MESSAGE = os.getenv('FILE_TEXT_GENERAL')
SENDERPHONE = os.getenv('SENDERPHONE_FINANCEIRO')

BASE_DIR = Path(__file__).parent
CAMINHO_PLANILHA = os.path.join(BASE_DIR, "dados_contacts.xlsx")


def load_txt(file_txt):
    if not file_txt:
        raise FileNotFoundError("Arquivo de texto não existe")
    with open(file_txt, "r", encoding="utf-8") as file:
        content = file.read()
        print("\nMensagem carregada:")
        print(content)
        return content


class BotTelegram:
    def __init__(self, api_id, api_hash, message):
        self._api_id = api_id
        self._api_hash = api_hash
        self._message = message

    def config_data_contacts(self, sheets=CAMINHO_PLANILHA):
        if not os.path.exists(sheets):
            raise FileNotFoundError("Planilha com contatos não existe")

        df = pd.read_excel(sheets)
        df = df.drop_duplicates()
        df['TELEFONE'] = df['TELEFONE'].astype(str).apply(
            lambda x: "+" + re.sub(r'[^0-9]', '', x)
        )
        if 'status' not in df.columns:
            df['status'] = ''

        print("\nContatos carregados:")
        for _, row in df.iterrows():
            print(f"{row['NOME']} - {row['TELEFONE']}")

        return df

    async def import_contacts_batch(self, client, df):
        """
        Importa TODOS os contatos de uma vez antes de iniciar os envios.
        Isso evita chamar ImportContactsRequest a cada mensagem.
        """
        print("\nImportando todos os contatos em batch...")
        contacts = [
            InputPhoneContact(
                client_id=i,
                phone=row['TELEFONE'],
                first_name=str(row['NOME']),
                last_name=""
            )
            for i, (_, row) in enumerate(df.iterrows())
        ]

        # Importa em lotes de 25 para não sobrecarregar
        batch_size = 25
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            try:
                await client(ImportContactsRequest(batch))
                print(f"  Lote {i // batch_size + 1} importado ({len(batch)} contatos)")
                await asyncio.sleep(5)  # Pausa entre lotes de importação
            except FloodWaitError as e:
                print(f"  FloodWait na importação! Aguardando {e.seconds}s...")
                await asyncio.sleep(e.seconds + 5)
                await client(ImportContactsRequest(batch))  # Tenta novamente

        print("Todos os contatos importados!\n")

    async def connection_telegram(self):
        client = TelegramClient('session_empresa', self._api_id, self._api_hash)

        await client.connect()
        print("Conectado ao servidor Telegram!")

        if not await client.is_user_authorized():
            print("Não autenticado. Solicitando código...")
            sent = await client.send_code_request(SENDERPHONE)
            print(f"Código enviado! Tipo: {sent.type}")

            code = input("Digite o código recebido no Telegram: ")
            try:
                await client.sign_in(SENDERPHONE, code)
                print("Autenticado com sucesso!")
            except Exception:
                senha = input("Digite sua senha 2FA (se tiver): ")
                await client.sign_in(password=senha)
        else:
            print("Sessão já válida, sem necessidade de novo código.")

        df = self.config_data_contacts()

        await self.import_contacts_batch(client, df)

        status_list = []

        for index, (_, row) in enumerate(df.iterrows()):
            phone = row['TELEFONE']
            name = row['NOME']
            status = ''

            try:
                # get_entity agora funciona pois o contato já foi importado
                entity = await client.get_entity(phone)
                await client.send_message(entity, self._message, parse_mode='html')
                print(f"[{index + 1}] Mensagem enviada para: {name} ({phone})")
                status = 'enviado'

            except FloodWaitError as e:
                wait = e.seconds + 10
                print(f"[{index + 1}] FloodWait! Aguardando {wait}s antes de continuar...")
                await asyncio.sleep(wait)
                try:
                    entity = await client.get_entity(phone)
                    await client.send_message(entity, self._message, parse_mode='html')
                    print(f"[{index + 1}] Enviado após FloodWait: {name} ({phone})")
                    status = 'enviado'
                except Exception as e2:
                    print(f"[{index + 1}] Falhou após FloodWait para {name}: {e2}")
                    status = f'erro: {e2}'

            except PeerFloodError:
                print(f"[{index + 1}] PeerFlood! Pausa de 5 minutos...")
                await asyncio.sleep(300)
                status = 'erro: peer flood'

            except UserPrivacyRestrictedError:
                print(f"[{index + 1}] {name} bloqueou mensagens de desconhecidos")
                status = 'bloqueado por privacidade'

            except Exception as e:
                print(f"[{index + 1}] Erro ao enviar para {name}: {e}")
                status = f'erro: {e}'

            status_list.append(status)

            # Delay entre mensagens (mais humano)
            delay = random.randint(10, 20)
            print(f"  Aguardando {delay}s até o próximo envio...")
            await asyncio.sleep(delay)

            # Pausa a cada 40 Mensagens
            if (index + 1) % 40 == 0:
                print(f"\nPausa de 5 minutos após {index + 1} envios...\n")
                await asyncio.sleep(120)

        df['status'] = status_list
        df.to_excel('resultado.xlsx', index=False)

        print("\nEnvio finalizado! Resultado salvo em resultado.xlsx")
        await client.disconnect()


async def start():
    telebot = BotTelegram(API_ID, API_HASH, load_txt(MESSAGE))
    await telebot.connection_telegram()


if __name__ == '__main__':
    asyncio.run(start())