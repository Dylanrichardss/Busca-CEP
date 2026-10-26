# Parceria Comercial OWN — v1.0

Aplicativo interno que preenche a aba **Transações** dos arquivos de comissão de cada parceiro
com as transações da planilha geral. Versão em Tkinter (sem navegador) do antigo
`Parceria Comercial.py` em Streamlit, com o mesmo visual do Envio de Comissões.

---

## Arquivos do projeto

Mantenha todos juntos, na mesma pasta:

| Arquivo | Para que serve |
|---|---|
| `parceria_comercial.py` | O programa. |
| `Arquivo - Parceiro.xlsx` | Mapeamento: colunas **ARQUIVO** (nome no arquivo) e **PARCEIRO** (nome na planilha de transações). |
| `logo.ico` / `logo.png` | Ícone do programa. |
| `requirements.txt` | Lista de dependências (só `openpyxl` e `pyinstaller`). |
| `build.bat` | Gera o executável (.exe). |

---

## Como usar (no dia a dia)

1. Abra o programa (o `.exe`, ou `python parceria_comercial.py`).
2. Clique em **Carregar transações** e escolha a planilha geral.
   - É lida a aba **tratado**, com cabeçalho na **linha 2** e colunas **A até AJ**.
   - A aba *Transações* mostra os dados; use a caixa de pesquisa para filtrar em qualquer coluna
     (são exibidas no máximo 2.000 linhas por vez; refine a pesquisa para ver outras).
3. Clique em **Buscar pasta** e escolha a pasta com os arquivos de comissão.
4. Confira a aba *Arquivos de comissão*:
   - **Gerar**: desmarque o que não quer processar (clicar no título "Gerar" marca/desmarca todos).
   - **Nome extraído**: 3ª parte do nome do arquivo, separando por `-`.
   - **Parceiro**: encontrado no `Arquivo - Parceiro.xlsx`. Linhas **vermelhas** não têm parceiro e são ignoradas.
   - **Transações**: quantas linhas desse parceiro serão gravadas. Com 0, a linha fica em **negrito** (a aba ficará vazia).
   - Duplo clique numa linha abre o arquivo no Excel.
5. Clique em **Gerar planilhas** e confirme.

Para cadastrar parceiros, use o link **Abrir planilha de parceiros**. Ao salvar e voltar para o app,
a tabela se atualiza sozinha.

---

## O que o app grava

Em cada arquivo marcado:

- Procura a aba **Transações** (sem diferenciar maiúsculas/acentos).
- Apaga os valores das colunas **A:AJ** a partir da **linha 5** (formatação e fórmulas das outras abas ficam).
- Grava as transações do parceiro a partir da linha 5.
- Salva numa cópia temporária e só depois substitui o original. Se o arquivo estiver aberto no Excel,
  o original não é alterado e a linha mostra o erro.

Exemplo de nome: `1026 - PARCERIA - CLINICORP - 1º Q OUTUBRO.xlsx` → nome extraído **CLINICORP**.
