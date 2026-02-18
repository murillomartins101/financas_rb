# Documentação de Cálculos do Dashboard

Este documento descreve como cada métrica do dashboard é calculada e como ela se relaciona com os dados da planilha.

## Métricas Principais

### 1. TOTAL RECEITAS (Total Revenue)

**Fórmula:**
```python
SUM(transactions[tipo == 'ENTRADA' AND payment_status == 'PAGO'].valor)
```

**Descrição:**
- Soma todas as transações do tipo `ENTRADA` que possuem status `PAGO`
- **Não inclui**:
  - Transações com status `NÃO RECEBIDO` (vão para "A Receber")
  - Transações com status `ESTORNADO` (são ignoradas)

**Exemplo:**
```
Transação 1: R$ 1.000,00 (ENTRADA, PAGO) → ✅ incluído
Transação 2: R$ 500,00 (ENTRADA, NÃO RECEBIDO) → ❌ não incluído
Transação 3: R$ 200,00 (ENTRADA, ESTORNADO) → ❌ não incluído
Total: R$ 1.000,00
```

---

### 2. TOTAL DESPESAS (Total Expenses)

**Fórmula:**
```python
SUM(transactions[tipo == 'SAIDA' AND payment_status == 'PAGO'].valor)
```

**Descrição:**
- Soma todas as transações do tipo `SAIDA` que possuem status `PAGO`
- Inclui todas as categorias de despesas:
  - Cachês de músicos (`PAYOUT_MUSICOS` ou `CACHÊS-MÚSICOS`)
  - Despesas operacionais (produção, logística, marketing, etc.)
  - Outras despesas

**Regra de Negócio:**
> "Só entra em caixa: payment_status == PAGO"

---

### 3. CAIXA ATUAL (Current Cash)

**Fórmula:**
```python
SUM(transactions[tipo == 'ENTRADA' AND payment_status == 'PAGO'].valor) -
SUM(transactions[tipo == 'SAIDA' AND payment_status == 'PAGO'].valor)
```

**Descrição:**
- Calcula o saldo atual de caixa
- Subtrai todas as despesas pagas das receitas pagas
- Representa o dinheiro efetivamente disponível

**Exemplo:**
```
Receitas Pagas: R$ 45.209,86
Despesas Pagas: R$ 40.502,35
Caixa Atual: R$ 4.707,51
```

---

### 4. MARGEM DE LUCRO (Profit Margin)

**Fórmula:**
```python
((Total Receitas - Total Despesas) / Total Receitas) * 100
```

**Descrição:**
- Calcula a margem de lucro percentual
- Indica quanto da receita é retido como lucro
- Valores negativos indicam prejuízo

**Proteções:**
- Retorna `N/A` se receita total for menor que R$ 1,00
- Usa `calculate_margin_safely()` para evitar divisões por zero

**Exemplo:**
```
Receitas: R$ 45.209,86
Despesas: R$ 40.502,35
Lucro: R$ 4.707,51
Margem: (4.707,51 / 45.209,86) * 100 = 10,41%
```

---

## Métricas Secundárias

### 5. VALOR BRUTO (Gross Value)

**Fórmula:**
```python
SUM(transactions[tipo == 'ENTRADA' AND payment_status == 'PAGO'].valor)
```

**Descrição:**
- Idêntico ao Total Receitas
- Representa o valor bruto de receitas antes de descontar custos

---

### 6. CUSTOS OPERACIONAIS (Operational Costs)

**Fórmula:**
```python
SUM(transactions[tipo == 'SAIDA' AND payment_status == 'PAGO'].valor)
```

**Descrição:**
- Idêntico ao Total Despesas
- Representa todos os custos operacionais pagos
- Inclui:
  - Equipe técnica
  - Equipamentos
  - Posts patrocinados
  - Produção
  - Logística
  - Marketing
  - Cachês de músicos

---

### 7. SALDO LÍQUIDO (Net Balance)

**Fórmula:**
```python
Valor Bruto - Custos Operacionais
```

**Descrição:**
- Idêntico ao Caixa Atual
- Representa o lucro líquido
- Mostra também o percentual retido: `(Saldo Líquido / Valor Bruto) * 100`

---

## Indicadores de Mudança Percentual

### Delta Month-over-Month (Comparação Mensal)

**Fórmula:**
```python
safe_percentage_change(valor_mes_atual, valor_mes_anterior)
```

**Descrição:**
- Calcula a mudança percentual em relação ao mês anterior
- Usa função segura que implementa:
  - Limite mínimo: -100%
  - Limite máximo: +1000%
  - Retorna `None` se:
    - Valor anterior < R$ 1,00 (não confiável)
    - Ambos valores próximos de zero
    - Mudança extrema com valores pequenos

**Exemplo:**
```
Mês Anterior: R$ 3.180,00
Mês Atual: R$ 1.200,00
Delta: ((1.200 - 3.180) / 3.180) * 100 = -62,3%
```

**Casos Especiais:**
```
Mês Anterior: R$ 3.180,00
Mês Atual: R$ 0,07 (quase zero)
Delta: -100,0% (limitado, na verdade -99,99%)

Mês Anterior: R$ 0,07 (muito pequeno)
Mês Atual: R$ 1.200,00
Delta: None (não confiável devido ao denominador pequeno)
```

---

## Cálculos de Shows

### Total de Shows Realizados

**Fórmula:**
```python
COUNT(shows[status == 'REALIZADO'])
```

**Descrição:**
- Conta apenas shows com status `REALIZADO`
- Shows `CONFIRMADOS` não são incluídos no histórico

---

### A Receber

**Fórmula:**
```python
SUM(transactions[tipo == 'ENTRADA' AND payment_status == 'NÃO RECEBIDO'].valor)
```

**Descrição:**
- Soma valores de entradas ainda não recebidas
- Representa o valor a receber no futuro

---

### Cachê de Músicos

**Fórmula:**
```python
SUM(transactions[
    tipo == 'SAIDA' AND
    categoria IN ['CACHÊS-MÚSICOS', 'PAYOUT_MUSICOS'] AND
    payment_status == 'PAGO'
].valor)
```

**Descrição:**
- Soma pagamentos para músicos
- Suporta múltiplas convenções de nomenclatura
- Apenas pagamentos efetivamente realizados (`PAGO`)

---

## Gráficos de Evolução

### Evolução das Receitas / Despesas

**Agregação:**
```python
GROUP BY month(data)
SUM(valor) WHERE tipo == 'ENTRADA' AND payment_status == 'PAGO'
```

**Descrição:**
- Agrupa transações por mês
- Calcula total de receitas/despesas por mês
- Exibe evolução temporal

---

## Casos Extremos e Validações

### Validação de Dados

A função `validate_data_integrity()` verifica:
1. ✅ Colunas obrigatórias presentes
2. ✅ Status válidos (`REALIZADO`, `CONFIRMADO`)
3. ✅ Tipos de transação válidos (`ENTRADA`, `SAIDA`)
4. ✅ Status de pagamento válidos
5. ✅ Valores não nulos

### Tratamento de Valores Extremos

**Percentuais de Mudança:**
- Limitados entre -100% e +1000%
- Retornam `None` quando não confiáveis
- Mostram "Dados insuficientes" na UI

**Divisões por Zero:**
- Todas as divisões usam `safe_division()`
- Retornam valor padrão (geralmente 0.0) quando denominador < 0.01

**Margens de Lucro:**
- Retornam `None` se receita < R$ 1,00
- Suportam valores negativos (prejuízo)

---

## Comparação com Planilha

Para garantir que os valores do dashboard correspondem à planilha:

1. **Mesmo filtro de período**: Use "Todo período" no dashboard para comparar com totais da planilha

2. **Mesmos critérios de filtro**:
   - Apenas `payment_status == 'PAGO'` para receitas e despesas efetivas
   - Apenas `status == 'REALIZADO'` para shows no histórico

3. **Valores esperados** (dados de teste):
   ```
   Total Receitas:  R$ 45.209,86
   Total Despesas:  R$ 40.502,35
   Caixa Atual:     R$  4.707,51
   Shows Realizados: 18
   A Receber:       R$  0,00
   ```

4. **Tolerância**: ± R$ 0,01 (arredondamento)

---

## Testes Automatizados

### Testes de Métricas (`tests/test_metrics_accuracy.py`)

Valida:
- ✅ Integridade dos dados
- ✅ Precisão dos cálculos
- ✅ Filtros de payment_status
- ✅ Reconhecimento de categorias

### Testes de Cálculos (`tests/test_calculation_utils.py`)

Valida:
- ✅ Cálculo seguro de percentuais
- ✅ Divisões seguras
- ✅ Validação de tendências
- ✅ Tratamento de casos extremos

---

## Troubleshooting

### Dashboard mostra valores diferentes da planilha

1. **Verifique o filtro de período**: Certifique-se de usar o mesmo período em ambos
2. **Confira payment_status**: Apenas transações `PAGO` são contabilizadas
3. **Verifique data dos registros**: Transações fora do período não aparecem
4. **Execute os testes**: `python tests/test_metrics_accuracy.py`

### Percentual mostra "N/A" ou "Dados insuficientes"

Isso ocorre quando:
- Valores anteriores são muito pequenos (< R$ 1,00)
- Não há dados suficientes para comparação confiável
- É esperado e previne exibição de percentuais enganosos como -287.2%

### Margem de Lucro mostra "N/A"

Isso ocorre quando:
- Receita total é menor que R$ 1,00
- Previne cálculos de margem não confiáveis

---

## Referências

- **README.md**: Especificação completa do sistema
- **core/metrics.py**: Implementação dos cálculos
- **utils/calculation_utils.py**: Funções auxiliares seguras
- **pages/home.py**: Exibição do dashboard
