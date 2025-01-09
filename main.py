import requests
import gspread
import urllib.parse

from credentials import credentials
from dataclasses import dataclass, asdict


AUTH_URL = "https://api.amazon.com/auth/o2/token"
BASE_URL = "https://sandbox.sellingpartnerapi-na.amazon.com"


# 1ª Parte ------------------------


data = {
    "grant_type": "refresh_token",
    "refresh_token": credentials["refresh_token"],
    "client_id": credentials["client_id"],
    "client_secret": credentials["client_secret"],
}

response = requests.post(AUTH_URL, data=data)

access_token = response.json()["access_token"]


# 2ª Parte ------------------------


request_params = {
    "CreatedAfter": "TEST_CASE_200",
    "MarketplaceIds": "ATVPDKIKX0DER",
}

url = f"{BASE_URL}/orders/v0/orders?{urllib.parse.urlencode(request_params)}"

headers = {
    "x-amz-access-token": access_token,
}

api_pedidos = requests.get(url, headers=headers)


# 3ª Parte ------------------------


gc = gspread.service_account(filename="keys.json")
sh = gc.open("SPAPI-SHEETS")
# print(sh.sheet1.get("A1"))


# 4ª Parte ------------------------


@dataclass
class Pedido:
    id_pedido: str
    data_compra: str
    status_pedido: str
    canal_fulfillment: str
    canal_vendas: str
    total_pedido: str
    metodo_pagamento: str
    id_marketplace: str
    categoria_nivel_servico_entrega: str
    tipo_pedido: str


CABECALHO = [
    "ID Pedido",
    "Data Compra",
    "Status Pedido",
    "Canal Fulfillment",
    "Canal Vendas",
    "Total Pedido",
    "Método Pagamento",
    "ID Marketplace",
    "Categoria Nível Serviço de Entrega",
    "Tipo Pedido",
]

worksheet = sh.get_worksheet(0)
worksheet.append_row(CABECALHO)

payload_pedidos = api_pedidos.json().get("payload", {}).get("Orders", [])

lista_pedidos_amazon = []

for item in payload_pedidos:
    lista_pedidos_amazon.append(
        Pedido(
            id_pedido=item.get("AmazonOrderId", ""),
            data_compra=item.get("PurchaseDate", ""),
            status_pedido=item.get("OrderStatus", ""),
            canal_fulfillment=item.get("FulfillmentChannel", ""),
            canal_vendas=item.get("SalesChannel", ""),
            total_pedido=item.get("OrderTotal").get("Amount", ""),
            metodo_pagamento=item.get("PaymentMethod", ""),
            id_marketplace=item.get("MarketplaceId", ""),
            categoria_nivel_servico_entrega=item.get("ShipmentServiceLevelCategory", ""),
            tipo_pedido=item.get("OrderType", ""),
        )
    )

lista_dados_pedido = [list(asdict(pedido).values()) for pedido in lista_pedidos_amazon]

ultima_linha = len(worksheet.col_values(1)) + 1
worksheet.insert_rows(lista_dados_pedido, ultima_linha)