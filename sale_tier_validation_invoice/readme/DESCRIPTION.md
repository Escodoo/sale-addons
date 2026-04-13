# O que este módulo faz

**Validação por níveis antes de confirmar o pedido de venda.**

Este módulo ajusta o fluxo de `sale_tier_validation` para uso operacional focado em:

- exigir aprovação do pedido ainda em **cotação** (`draft/sent`);
- permitir aprovação por **grupo de usuários** (`review_type=group`);
- não adicionar bloqueios extras de faturação após confirmação.

## Em uma frase

O pedido só pode ser confirmado quando as revisões pendentes forem aprovadas por usuários do grupo configurado na definição de nível.
