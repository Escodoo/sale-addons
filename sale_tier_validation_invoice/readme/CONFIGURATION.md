# Configuração

## Pré-requisitos

Módulos OCA `base_tier_validation` e `sale_tier_validation` (instalados como dependências deste módulo).

## Passos

1. Ativar o módulo **Sale Tier Validation — Group before confirmation** (`sale_tier_validation_invoice`).
2. Ir a Definições, Técnico, Tier Validations, Tier Definition (ou o menu equivalente na base).
3. Criar ou editar uma definição com modelo **Pedido de venda** (`sale.order`).
4. Definir `review_type = group`.
5. Informar o grupo aprovador em `reviewer_group_id`.
6. Configurar domínio, sequência e notificações como de costume no OCA.

## Dica

Evite deixar `definition_domain` vazio em bases de produção, para não aplicar a regra a todos os pedidos de venda sem distinção.
