# Memória do projeto

Este arquivo guarda decisões e mudanças importantes do HRX CODE de terminal.
Ele serve como histórico curto do projeto e deve ser atualizado sempre que o
comportamento, os comandos ou a configuração mudarem.

## Mudanças recentes

- A versão 0.1.1 adiciona undo transacional às mutações de arquivos. A operação
  só entra no histórico depois de a escrita terminar e o estado posterior ser
  confirmado; falhas abortam a transação e preservam ou restauram o original.
- Antes de desfazer, o motor compara o hash SHA-256 e os metadados registrados
  após a mutação (modo, `mtime`, dispositivo e inode). Divergências são tratadas
  como conflito: nada é sobrescrito e a operação permanece disponível.
- Snapshots e o histórico de undo ficam em `~/.config/hrx/dados/undo/` por
  padrão, ou sob o diretório definido por `AGENTE_DADOS`, com diretório `0700`
  e arquivos `0600` quando suportado. Esse caminho é sempre ocultado das
  ferramentas de navegação e documentos; o histórico mantém até 50 operações
  ou 100 MiB de snapshots.
- `/undo [caminho]` e a ferramenta `desfazer_ultima` compartilham o mesmo fluxo
  de autorização de uso único e são sempre risco vermelho, inclusive no modo
  automático. O caminho opcional seleciona a mutação ativa mais recente dele.
- `editar_arquivo` exige trecho literal inequívoco por padrão e agora aceita
  `ocorrencia=N` ou `tudo=True`, opções mutuamente exclusivas validadas antes de
  criar o snapshot da transação.
- `listar_diretorio` e `buscar_codigo` respeitam o `.gitignore` da raiz e o
  `.hrxignore` privado, com cache invalidado por `mtime` e tamanho. Arquivos
  `.gitignore` aninhados não são interpretados; diretórios internos pesados
  permanecem excluídos quando `respeitar_gitignore=False`.
- `buscar_codigo` ganhou linhas de contexto com agrupamento de intervalos;
  arquivos binários são recusados por assinatura, NUL ou controles sem penalizar
  UTF-8 acentuado. Leitura, shell e Git informam truncamento, e os dois últimos
  sempre retornam o código de saída.
- A preferência de `/memoria modo compacta|completa` passou a ser lida da
  configuração persistente, mantendo a precedência da variável de ambiente.
- Adicionada a ferramenta `aplicar_patch`, que aplica hunks de diff unificado a
  um arquivo por vez, valida contexto e contagens antes da escrita, rejeita
  conflitos sem alteração parcial e usa o mesmo trinco de autorização das
  demais ferramentas de escrita.
- Prompt de sistema revisado para tornar o agente mais conciso e autônomo em
  ações seguras, exigir leitura do contexto e respeito às convenções antes de
  editar, validar mudanças com testes e ferramentas do projeto, preservar
  alterações existentes e impedir operações Git mutantes sem pedido explícito.
- Política de segurança do prompt reforçada para aceitar somente atividades
  defensivas, educacionais ou de CTF autorizado, com recusa breve e alternativa
  segura para solicitações ofensivas.
- Código-fonte organizado em `src/hrx_code`, com imports relativos, execução
  por `python -m hrx_code` e comando oficial `hrx` definido no pacote.
- Projeto empacotado via `pyproject.toml`, com dependências declaradas e versão
  única em `src/hrx_code/versao.py`; dados persistentes ficam em
  `~/.config/hrx/` para sobreviver a upgrades do pacote.
- Caminhos agora são canonizados antes do uso: leituras bloqueiam escapes por
  `..` e links simbólicos, enquanto escritas fora do projeto são sempre risco
  vermelho e exigem confirmação explícita, inclusive no modo automático.
- Testes avulsos migrados para uma suíte `pytest`, com execução automática no
  GitHub Actions em Python 3.10 a 3.13 e dependências declaradas em arquivos
  `requirements`.
- Suíte ampliada para 175 testes e cerca de 62% de cobertura com `pytest-cov`;
  comandos, memória, ferramentas e provedores agora têm testes dedicados, e o
  CI rejeita cobertura total abaixo de 40%.
- Classificador de risco agora tokeniza e normaliza comandos shell, bloqueando
  ofuscação, executores dinâmicos, código inline e padrões destrutivos do
  Windows. O modo `/dry-run` simula ferramentas sensíveis sem executá-las e
  pode ser ativado na inicialização por `HRX_DRY_RUN=1`.
- Projeto renomeado de "JARVIS" para **HRX CODE** (evitar direitos autorais da
  Marvel). Trocado tudo: marca, logo ASCII, backronym, config dir
  (`~/.config/hrx/`), prefixo de env vars (`HRX_`) e comandos (`hrx`,
  `hrx-qwen`).
- O `run.sh` executa o pacote com `.venv/bin/python -m hrx_code`; instalações
  usam o ponto de entrada `hrx_code.agente:main`.
- Licença **MIT** (`LICENSE`): livre para usar, modificar, distribuir e uso
  comercial, mantendo o aviso de copyright. Migrado de licença proprietária de
  uso gratuito para OSS em 2026-07-17.
- Adicionado `/perfil` (nome, tom, idioma, projeto) persistido em
  `~/.config/hrx/perfil.json`.
- Adicionado `/config` para escolher e persistir o motor de IA.
- Suporte a Gemini, ChatGPT/OpenAI, DeepSeek, Claude, Ollama e motor local.
- Adicionados `/debug` e `/resumo` no terminal.
- Memória persistente entre sessões com `memoria_salvar`, `memoria_listar` e
  `memoria_esquecer`.
- Memória no prompt agora é carregada em modo compacto por padrão, com limite
  de itens e caracteres para gastar menos tokens e permitir sessões maiores.
- Adicionado `/memoria modo compacta|completa` para alternar a injeção da
  memória no contexto sem editar arquivo.
- Adicionados `/memoria compacta`, `/memoria resumir` e `/memoria limpar`.
- Memória agora gera um resumo persistente quando passa do limite configurado,
  preservando os itens mais recentes e reduzindo o custo de contexto.
- `README.md` atualizado para refletir comandos e organização do projeto.
- Motor local padrao definido como `local` e a dica de inicializacao agora
  aponta para `./iniciar-qwen.sh`.
- Modelo local padronizado como `Qwen2.5-7B-Instruct` nas mensagens e na
  documentacao do projeto.

## Regra prática

- Se mudar um comando, uma configuração ou o fluxo do agente, atualize este
  arquivo.
- Se a alteração for visível para o usuário, atualize também o `README.md`.
- Se a mudança for pequena mas relevante, registre uma linha aqui.
