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
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError

load_dotenv()

API_ID = os.getenv('API_ID_FINANCEIRO')
API_HASH = os.getenv('API_HASH_FINANCEIRO')
MESSAGE = os.getenv('FILE_TEXT')
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

        print("\nContatos carregados:")
        for _, row in df.iterrows():
            print(f"{row['NOME']} - {row['TELEFONE']}")

        return df

    async def import_contact(self, client, phone, name):
        """Importa o contato na lista do Telegram antes de enviar"""
        contact = InputPhoneContact(
            client_id=0,
            phone=phone,
            first_name=name,
            last_name=""
        )
        await client(ImportContactsRequest([contact]))

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

        # Resto do envio igual ao original
        df = self.config_data_contacts()

        for index, (_, row) in enumerate(df.iterrows()):
            phone = row['TELEFONE']
            name = row['NOME']

            try:
                await self.import_contact(client, phone, name)
                entity = await client.get_entity(phone)
                await client.send_message(entity, self._message, parse_mode='html')
                print(f"Mensagem enviada para: {name} ({phone})")

            except PeerFloodError:
                print("Flood detectado! Aguardando 60s...")
                await asyncio.sleep(60)

            except UserPrivacyRestrictedError:
                print(f"{name} bloqueou mensagens de desconhecidos")

            except Exception as e:
                print(f"Erro ao enviar para {name}: {e}")

            await asyncio.sleep(random.randint(5, 15))

            if (index + 1) % 20 == 0:
                print("Pausa de 5 minutos")
                await asyncio.sleep(300)

        print("\nEnvio finalizado!")
        await client.disconnect()


async def start():
    telebot = BotTelegram(API_ID, API_HASH, load_txt(MESSAGE))
    await telebot.connection_telegram()


if __name__ == '__main__':
    asyncio.run(start())
