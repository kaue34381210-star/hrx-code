# Changelog

Todas as mudanças relevantes do HRX Code serão registradas neste arquivo.

## [Não publicado]

## [0.1.1] - 2026-07-17

### Adicionado

- Modo `/dry-run` para simular ferramentas sensíveis sem aprovação nem
  execução, configurável também pela variável `HRX_DRY_RUN`.
- Ferramenta `aplicar_patch` para edições atômicas por diff unificado, com
  validação de contexto e rejeição de conflitos antes da escrita.
- Undo transacional para mutações de arquivos, disponível pela ferramenta
  `desfazer_ultima` e pelo comando `/undo [caminho]`, com snapshots privados,
  autorização obrigatória de alto risco e detecção de alterações posteriores.
- Seleção de uma ocorrência ou de todas as ocorrências em `editar_arquivo`.
- Contexto configurável antes e depois dos resultados de `buscar_codigo`.
- Suporte ao `.gitignore` da raiz e ao `.hrxignore` privado nas ferramentas de
  listagem e busca, preservando diretórios internos mesmo com o filtro desligado.
- Detecção de arquivos binários por assinatura, byte NUL e controles, sem
  classificar texto UTF-8 acentuado como binário.

### Alterado

- Licença migrada de proprietária de uso gratuito para **MIT** — projeto agora
  é open source (livre para usar, modificar, distribuir e uso comercial).
- Código-fonte migrado para o pacote `src/hrx_code` com imports relativos.
- CLI também pode ser iniciada com `python -m hrx_code`.
- Testes atualizados para validar a API do pacote e o novo ponto de entrada.
- Suíte ampliada para 175 testes, cobrindo comandos customizados, memória,
  ferramentas de arquivo, undo e adaptadores OpenAI/Claude.
- Cobertura medida com `pytest-cov` e protegida por um piso de 40% no CI.
- Classificação de comandos reforçada contra ofuscação shell, execução inline,
  executáveis dinâmicos e comandos perigosos do Windows.
- Prompt de sistema reforçado para autonomia em ações seguras, preservação de
  mudanças existentes e uso defensivo das ferramentas.
- Saídas de leitura, shell e Git agora informam truncamento; shell e Git sempre
  incluem o código de saída, inclusive quando há texto na resposta.
- O modo escolhido por `/memoria modo compacta|completa` agora persiste entre
  execuções.

## [0.1.0] - 2026-07-16

### Adicionado

- CLI instalável pelo comando `hrx`.
- Loop ReAct com ferramentas de código, terminal, Git, web e documentos.
- Suporte a Gemini, OpenAI, DeepSeek, Groq, Claude, Ollama e modelos locais.
- Rotação de chaves Gemini com cooldown e failover automático.
- Memória persistente, perfis e comandos customizados.
- Classificação de risco em três níveis e autorização de uso único.
- Isolamento de caminhos, proteção contra symlinks e validação contra SSRF.
- Suíte com 56 testes executada em quatro versões do Python.

[Não publicado]: https://github.com/kaue34381210-star/hrx-code/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/kaue34381210-star/hrx-code/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/kaue34381210-star/hrx-code/releases/tag/v0.1.0
