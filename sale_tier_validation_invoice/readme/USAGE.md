# Utilização

## Fluxo sugerido

1. Criar o pedido de venda em **cotação**.
2. Ao tentar confirmar com tiers aplicáveis pendentes, o sistema impede a confirmação e solicita validação.
3. Usuários do grupo configurado na definição (`reviewer_group_id`) aprovam via ação **Validate**.
4. Após aprovação de todas as revisões pendentes, o pedido pode ser confirmado.
5. Depois de confirmado, a faturação segue o fluxo padrão do `sale` (sem bloqueio extra deste módulo).
