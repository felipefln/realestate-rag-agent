#!/usr/bin/env bash
# Exemplos de uso da API. Requer o servidor rodando e o banco populado:
#
#   make db-up && make migrate && make seed
#   make dev            # ou: make run
#
# Uso:
#   ./scripts/api_examples.sh            # roda todos os exemplos
#   BASE=http://localhost:8000 ./scripts/api_examples.sh
#
# Precisa de: curl, jq

set -euo pipefail
BASE="${BASE:-http://localhost:8000}"

hr() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }
req() { echo "+ curl $*" >&2; curl -sS "$@"; echo; }

# ---------------------------------------------------------------------------
hr "Health"
req "$BASE/health" | jq .

# ---------------------------------------------------------------------------
hr "Listar (primeiros 3)"
req "$BASE/properties?limit=3" | jq '{total, limit, offset, items: [.items[] | {title, operation, price, neighborhood}]}'

hr "Paginação (limit=5, offset=5)"
req "$BASE/properties?limit=5&offset=5" | jq '{total, count: (.items | length)}'

hr "Filtro: só locação"
req "$BASE/properties?operation=rent&limit=100" | jq '{total, sample: [.items[:3][] | {title, price}]}'

hr "Filtro: apartamentos até R\$ 700.000 com 2+ quartos"
req "$BASE/properties?operation=sale&property_type=apartment&max_price=700000&min_bedrooms=2&limit=100" \
  | jq '{total, items: [.items[] | {title, price, bedrooms}]}'

hr "Filtro: bairro (case-insensitive) + área mínima"
req "$BASE/properties?neighborhood=trindade&min_area=60&limit=100" \
  | jq '{total, items: [.items[] | {title, area_m2, neighborhood}]}'

hr "Filtro: por amenities (piscina E churrasqueira)"
req "$BASE/properties?amenities=piscina&amenities=churrasqueira&limit=100" \
  | jq '{total, items: [.items[] | {title, amenities}]}'

hr "Filtro: faixa de preço (locação entre 2000 e 4000)"
req "$BASE/properties?operation=rent&min_price=2000&max_price=4000&limit=100" \
  | jq '{total, items: [.items[] | {title, price}]}'

# ---------------------------------------------------------------------------
hr "Criar imóvel (POST)"
NEW=$(req -X POST "$BASE/properties" \
  -H 'Content-Type: application/json' \
  -d '{
        "title": "Cobertura duplex na Beira-Mar",
        "description": "Cobertura duplex à venda na Beira-Mar Norte, com vista panorâmica para a baía.",
        "operation": "sale",
        "property_type": "apartment",
        "price": 2650000,
        "condo_fee": 2100,
        "iptu": 9800,
        "bedrooms": 4,
        "bathrooms": 5,
        "parking_spaces": 3,
        "area_m2": 220,
        "neighborhood": "Centro",
        "latitude": -27.5889,
        "longitude": -48.5551,
        "amenities": ["piscina", "academia", "vista para o mar"]
      }')
echo "$NEW" | jq '{id, title, price}'
ID=$(echo "$NEW" | jq -r '.id')

hr "Buscar por id (GET /properties/{id})"
req "$BASE/properties/$ID" | jq '{id, title, price, bedrooms}'

hr "Atualizar preço (PATCH)"
req -X PATCH "$BASE/properties/$ID" \
  -H 'Content-Type: application/json' \
  -d '{"price": 2490000, "amenities": ["piscina", "academia", "vista para o mar", "coworking"]}' \
  | jq '{id, price, amenities}'

hr "Remover (DELETE) -> 204"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X DELETE "$BASE/properties/$ID"

hr "Confirmar remoção -> 404"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/properties/$ID"

# ---------------------------------------------------------------------------
hr "Erros esperados"
echo "-- id inexistente -> 404"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/properties/00000000-0000-0000-0000-000000000000"

echo "-- uuid inválido -> 422"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/properties/nao-e-uuid"

echo "-- preço negativo -> 422"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST "$BASE/properties" \
  -H 'Content-Type: application/json' \
  -d '{"title":"x","description":"descricao curta demais","operation":"sale","property_type":"house","price":-1,"area_m2":50,"neighborhood":"Centro"}'

echo "-- operation inválida -> 422"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/properties?operation=comprar"

echo "-- limit acima do máximo (>100) -> 422"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$BASE/properties?limit=999"

hr "OpenAPI / docs"
echo "Swagger UI:  $BASE/docs"
echo "OpenAPI:     $BASE/openapi.json"
