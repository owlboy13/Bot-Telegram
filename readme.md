# Bot Telegram - Disparador de Mensagens

Script Python para envio automatizado de mensagens via Telegram utilizando a biblioteca Telethon. O bot lê os contatos de uma planilha Excel e envia mensagens personalizadas para cada destinatário.

---

## Requisitos

- Python 3.10+
- Conta no Telegram com `api_id` e `api_hash` gerados em [my.telegram.org](https://my.telegram.org)
- Planilha Excel com os contatos no formato esperado

---

## Instalação

Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/bot-telegram.git
cd bot-telegram
pip install -r requirements.txt
```

### Dependências

```txt
telethon
pandas
openpyxl
python-dotenv
cryptg
```

---

## Configuração

### 1. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
API_ID_FINANCEIRO=123456
API_HASH_FINANCEIRO=sua_api_hash_aqui
SENDERPHONE_FINANCEIRO=+5511999999999
FILE_TEXT=mensagem.txt
```

| Variável | Descrição |
|---|---|
| `API_ID_FINANCEIRO` | ID da aplicação obtido em my.telegram.org |
| `API_HASH_FINANCEIRO` | Hash da aplicação obtido em my.telegram.org |
| `SENDERPHONE_FINANCEIRO` | Numero de telefone da conta no formato internacional |
| `FILE_TEXT` | Caminho para o arquivo .txt com a mensagem a ser enviada |

### 2. Arquivo de mensagem

Crie um arquivo `.txt` com o conteudo da mensagem. O campo `parse_mode` esta configurado como `html`, entao voce pode usar tags HTML na mensagem:

```html
Ola <b>cliente</b>,

Segue seu boleto referente ao mes de marco.

Atenciosamente,
Financeiro
```

### 3. Planilha de contatos

Crie o arquivo `dados_contacts.xlsx` na raiz do projeto com as seguintes colunas:

| NOME | TELEFONE |
|---|---|
| Joao Silva | 5511999999999 |
| Maria Souza | 5585988887777 |

- A coluna `TELEFONE` deve conter apenas numeros, com o codigo do pais e DDD. O `+` e adicionado automaticamente pelo script.
- Linhas duplicadas sao removidas automaticamente.

---

## Estrutura do projeto

```
bot-telegram/
├── send_telegram.py       # Script principal
├── dados_contacts.xlsx    # Planilha com os contatos
├── mensagem.txt           # Arquivo com o texto da mensagem
├── .env                   # Variaveis de ambiente (nao subir no git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Primeiro uso

Na primeira execucao o Telethon vai solicitar o codigo de verificacao que chegara no aplicativo do Telegram da conta configurada:

```bash
python send_telegram.py

# O terminal vai exibir:
Please enter the code you received: 
```

Apos inserir o codigo corretamente, um arquivo `session.session` sera criado na raiz do projeto. Esse arquivo mantem a sessao autenticada e nao sera necessario inserir o codigo novamente nas proximas execucoes.

> Guarde o arquivo `session.session` em local seguro. Se ele for deletado, o processo de autenticacao precisara ser feito novamente.

---

## Gitignore recomendado

```gitignore
.env
*.session
dados_contacts.xlsx
mensagem.txt
__pycache__/
```

---

## Comportamento do script

- Importa cada contato na lista do Telegram antes de enviar, evitando o erro `Cannot find any entity`
- Aguarda entre 5 e 15 segundos entre cada mensagem para reduzir o risco de bloqueio
- A cada 20 mensagens enviadas, faz uma pausa de 5 minutos
- Trata os erros `PeerFloodError` e `UserPrivacyRestrictedError` sem interromper o envio

---

## Limitacoes

O Telegram possui limites nao oficiais para envio de mensagens. Envios em grande volume podem resultar em bloqueio temporario ou permanente da conta. Recomenda-se enviar no maximo 50 mensagens por dia para contas com menos de 3 meses de uso.

---

## Obtendo as credenciais da API

1. Acesse [my.telegram.org](https://my.telegram.org) e faca login com o numero da conta
2. Va em "API Development Tools"
3. Crie uma nova aplicacao
4. Copie o `api_id` e o `api_hash` gerados para o arquivo `.env`