# Simulador de Cold Call: documento do projeto

> Documento de passagem para retomar o projeto em outro ambiente. Atualizado em 29/10/2026.
> **Para o Claude que for continuar:** leia este arquivo inteiro antes de agir. O estado atual está na seção 9 e a lista de pendências na seção 10.

---

## 1. Objetivo

Workshop de **abordagem de clientes por telefone (cold call)** para vendedores ("fronts") de clientes do Davi. Os fronts ligam para uma **IA de voz que interpreta um lead** e treinam a abertura da ligação.

- **Contexto de negócio:** mercado livre de energia (ACL). O Davi atua na área comercial e tem ligação com a Ludfor, gestora e comercializadora de energia do RS. Os leads simulados são empresas fictícias do Sul: indústrias, varejo e hospital, com consumidores Grupo A no cativo ou no livre.
- **O foco é a boca do funil.** A ligação não fecha venda: leva o lead de frio a "um pouco menos que morno". As ligações são curtas, de 2 a 7 minutos.
- **O exercício é gamificado:**
  - cada objetivo cumprido dá pontos;
  - cada bot tem objetivos secretos que dão pontos extras;
  - o ranking final é mostrado num pódio.
- **Tudo é gravado** (áudio e transcrição). As melhores ligações viram material de estudo numa pasta do Google Drive.
- **Escala:** no máximo 6 ou 7 vendedores ligando ao mesmo tempo.

## 2. Os dois desafios

| | Desafio 1 · Lead frio | Desafio 2 · Primeiro contato |
|---|---|---|
| Quem atende | Recepção, sócio, telefonista ou auxiliar (gatekeeper) | O responsável pela energia |
| Objetivo do front | Descobrir **quem é o responsável pela energia elétrica** (nome e cargo) e um **contato direto** | Descobrir a **situação energética** (cativo ou livre, contrato, vencimento, quem faz a gestão, tamanho da fatura) e **gerar interesse** num próximo passo concreto (reunião com data ou envio de fatura) |

O front escolhe o desafio que quiser, em qualquer ordem. Novos desafios (3, 4…) podem ser criados só pela planilha.

## 3. Decisões tomadas (e por quê)

| Decisão | Motivo |
|---|---|
| **ElevenLabs Agents** como motor de voz | Melhor voz em PT-BR, custo baixo e pouca configuração. O Davi já tem conta e créditos |
| **Conversa pelo navegador**, sem telefone de verdade | Dispensa número brasileiro e Twilio, e não tem custo de telefonia. O front fala pelo computador, de fone |
| **Um único agente** na ElevenLabs | O personagem vem inteiro em variáveis a cada ligação, e a pontuação é feita fora da ElevenLabs. Antes eram 2 agentes por causa dos critérios de avaliação nativos, que foram abandonados |
| **A planilha Google é a fonte de verdade** de desafios e bots | O Davi edita roteiros sem mexer em código nem republicar a página |
| **Pontuação pelo Claude (API da Anthropic) via Apps Script** | Os objetivos variam por bot, e a avaliação nativa da ElevenLabs tem critérios fixos por agente |
| **Apps Script verifica a ElevenLabs a cada 1 min**, em vez de receber webhook | O Apps Script não lê cabeçalhos HTTP, então não conseguiria validar a assinatura de um webhook |
| **Gravações no Google Drive** | Ouvir áudio no GitHub é ruim |
| **Ranking só no fim**, num pódio com revelação | Pedido do Davi, pelo efeito de encerramento |
| **Hospedagem no GitHub Pages** deste repositório, pasta `/coldcall/` | Grátis e já existente. Domínio próprio descartado: trocaria as URLs do Jorne e do Grifo, que estão cadastradas na App Store |
| **Voz V3 Conversacional** + Claude Haiku 5.5 como LLM do agente | Testado pelo Davi: "a pausa é perceptível mas pequena, ficou bem bom" |

## 4. Arquitetura

```
┌─────────────────────────┐      ┌──────────────────────────────┐
│ coldcall/index.html     │─────►│ ElevenLabs (agente único)    │
│ (tela do front)         │ voz  │ grava áudio + transcrição    │
└───────────┬─────────────┘      └───────────────┬──────────────┘
            │ GET desafios+bots                  │ a cada 1 min (API)
            ▼                                    ▼
┌──────────────────────────────────────────────────────────────┐
│ Google Sheets + Apps Script (coldcall/apps-script/Codigo.gs) │
│  abas: Desafios · Bots · Ligacoes · Ranking                  │
│  • doGet: serve desafios/bots (só campos públicos) e ranking │
│  • sincronizar(): busca ligações → Drive → Claude → planilha │
└───────────┬──────────────────────────────────────────────────┘
            │ GET ?acao=ranking
            ▼
┌─────────────────────────┐      Google Drive: "Simulador Cold Call"
│ coldcall/ranking.html   │        ├─ Gravações (mp3 + txt de todas)
│ (pódio no telão)        │        └─ Exemplos (cópia das marcadas)
└─────────────────────────┘
```

### Fluxo de uma ligação
1. A página carrega os desafios e bots ativos do app da web do Apps Script.
2. Cada card de desafio mostra um bot sorteado (a ficha do lead). O front clica em **Ligar**.
3. Toca o sinal de chamada brasileiro (425 Hz) 2 ou 3 vezes. A página abre a sessão WebRTC com a ElevenLabs e envia as variáveis dinâmicas e o override de voz do bot.
4. O lead atende com `{{saudacao}}`. Conversa. Quem encerra é o front, ou o bot, pela ferramenta `end_call`.
5. A tela final mostra a duração, quem desligou, o gabarito e a transcrição.
6. Em até 1 a 2 min, o Apps Script:
   - pega a ligação na ElevenLabs;
   - salva o mp3 e o txt no Drive;
   - manda a transcrição e os objetivos do bot para o Claude;
   - grava ✔/✘ e os pontos na aba Ligacoes.

## 5. Arquivos do repositório (branch `coldcall-simulador`)

| Arquivo | O que é |
|---|---|
| `coldcall/index.html` | Tela do front: nome, aceite de gravação, um card por desafio, ligação, tela final |
| `coldcall/ranking.html` | Pódio com revelação: 4º em diante → 3º → 2º → 1º. Botão ou barra de espaço. Rufar de tambor e confete |
| `coldcall/apps-script/Codigo.gs` | Código para colar no Apps Script da planilha |
| `coldcall/PROJETO.md` | Este documento |

- **URLs depois de publicadas** (merge no `main`):
  - `https://davimorgado-arch.github.io/coldcall/`
  - `https://davimorgado-arch.github.io/coldcall/ranking.html`
- **Parâmetros de URL para teste:**
  - `index.html?agent=...&api=...` sobrescreve o agente e a URL do Apps Script;
  - `ranking.html?api=...` sobrescreve a URL do Apps Script.
- **Constantes no topo de cada HTML:**
  - `AGENT_ID` (já preenchido) e `API_URL` (**vazio: falta a URL do app da web**) em `index.html`;
  - `API_URL` em `ranking.html` (**vazio**).

**Atenção:** o GitHub Pages serve todos os arquivos do repositório, este `.md` e o `Codigo.gs` inclusive. Não há nenhum segredo neles. Os únicos dados sensíveis são os bots de exemplo do `Codigo.gs`, que mostram objetivos secretos. Se isso incomodar, mova os dois arquivos para um repositório privado antes do merge no `main`.

### Detalhes técnicos da página do front
- **SDK:** `@elevenlabs/client@1.27.0` (build IIFE via jsDelivr, global `ElevenLabsClient`).
- **Sessão:**
  - `Conversation.startSession({ agentId, connectionType: "webrtc", userId: <nome do front>, dynamicVariables, overrides: { tts: { voiceId } } })`;
  - o `overrides` só é enviado se o bot tiver `voz_id`.
- **Variáveis enviadas:** `bot_id`, `desafio`, `contexto_desafio`, `roteiro`, `saudacao`. Na `saudacao`, `{periodo}` é trocado por "bom dia" ou "boa tarde".
- **Comportamentos cobertos:**
  - o microfone é pedido antes do toque, para o pop-up não surgir no meio da ligação;
  - se o front desliga enquanto a conexão abre, a sessão é encerrada (corrida tratada);
  - o selo "✓ feito" do card é guardado no `localStorage`, por nome do front;
  - um bug foi corrigido: redesenhar os cards no `change` do campo de nome engolia o clique em Ligar. Agora o redesenho acontece no `input`.

## 6. Configuração da ElevenLabs (feita e verificada via API em 29/10/2026)

- **Conta:** Davi, plano **Free**.
  - Saldo após o teste: ~64.600 créditos (10.000 grátis + ~54.945 comprados por US$ 20).
  - Recarga automática: o Davi deve ter desligado. Vale conferir.
- **Agente:** `Cold Call – Simulador`, ID **`agent_1301m6210yfwfrcb95egc9w0jvfr`**.

| Item | Valor |
|---|---|
| Idioma | `pt-br` |
| Primeira mensagem | `{{saudacao}}` (interrompível) |
| LLM | `claude-haiku-5-5` |
| Voz padrão | `GOkMqfyKMLVUcYfO2WbB` (Jenifer), modelo `eleven_v3_conversational`, modo expressivo ligado (padrão) |
| Ferramenta de sistema | `end_call` ✅ |
| Duração máxima | 480 s |
| Override de voz (`tts.voice_id`) | liberado ✅ |
| Allowlist | `davimorgado-arch.github.io` ✅. **Uma página aberta de outro domínio (localhost, por exemplo) é recusada.** Para testar localmente, adicione o domínio na allowlist |
| Autenticação | desligada (a página não usa login) |
| Placeholders das variáveis | preenchidos com o bot de teste "Érica" (desafio 2), usados na pré-visualização do painel |

### System prompt do agente (cópia do que está publicado)
```
Você é um personagem numa ligação telefônica real. Isto é uma conversa por voz.

CONTEXTO
{{contexto_desafio}}

SEU PERSONAGEM E ROTEIRO
{{roteiro}}

COMO FALAR (vale para qualquer personagem)
- Fale como gente de verdade ao telefone: frases curtas, informais, às vezes incompletas.
- Use hesitações naturais de vez em quando ("é…", "hum", "olha…", "deixa eu ver"), sem exagerar.
- Nunca use listas, tópicos, emojis ou linguagem escrita.
- Responda só o que foi perguntado. Não ofereça informação espontaneamente.
- Pergunta vaga recebe resposta vaga; pergunta boa e específica recebe resposta específica.
- Você não tem obrigação de ajudar: abrir-se é uma recompensa que o vendedor precisa merecer.

QUANDO DESLIGAR (ferramenta end_call)
- Quando a conversa terminar naturalmente (despedida).
- Se o vendedor insistir duas vezes depois de um "não" claro, ou fizer pitch longo depois de você pedir para ser breve.
Antes de desligar, diga uma frase curta de encerramento.

REGRAS FIXAS
- Nunca saia do personagem. Nunca diga que é uma IA, um robô ou um treinamento.
- Não invente fatos que contradigam o roteiro. Se perguntarem algo que não está nele, responda de forma vaga e plausível ("isso eu teria que ver").

(ref. interna, ignore: {{bot_id}} / {{desafio}})
```
A última linha existe para declarar `bot_id` e `desafio` no agente. O Apps Script lê essas duas variáveis em `conversation_initiation_client_data.dynamic_variables` para saber qual bot pontuar.

### Custos medidos
- **Ligação de teste:** ~3 min, 327 créditos, ou seja, **~110 créditos/min**. Foi feita no painel; a ligação real pode custar diferente.
- **Necessidade estimada:** workshop (7 fronts × ~3 ligações × ~4 min ≈ 85 min) + testes ≈ 120 min ≈ **13 mil créditos**. O saldo atual sobra.
- **Ligações simultâneas** (gargalo real):
  - **Free: 4.**
  - **Starter: 6.** A 7ª ligação vai para fila ou é cobrada em dobro (burst).
  - **Creator: 10.**
  - Havia uma promoção do Starter por **US$ 1 no 1º mês**, terminando por volta de 01/11/2026. Decisão pendente, que depende da data do workshop. Cancelar a renovação depois.
- **Claude (avaliação):** centavos de dólar por ligação.

## 7. Planilha Google (criada pelo `Codigo.gs`)

Menu **📞 Cold Call**:
1. **Configurar planilha e pastas:** cria as abas e as pastas no Drive e instala o gatilho de 1 min.
2. **Configurar chaves e agente:** grava `ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY` e `AGENT_ID` nas Script Properties.
3. **🔄 Processar ligações agora:** roda o ciclo manualmente.
4. **♻️ Reprocessar ligações com erro:** apaga as linhas com status `erro: …`, que voltam no próximo ciclo.

Depois: **Implantar → Nova implantação → App da Web** (executar como **Eu**, acesso **Qualquer pessoa**). A URL gerada vai em `API_URL` nas duas páginas. Ao alterar o código, use **Gerenciar implantações → Nova versão** para manter a mesma URL.

### Aba Desafios
| Coluna | Uso |
|---|---|
| `numero` | 1, 2, 3… Os bots apontam para ele |
| `ativo` | caixinha. Marcada = card aparece (se houver bot ativo no desafio) |
| `titulo`, `descricao`, `objetivo` | textos do card |
| `contexto` | vai para `{{contexto_desafio}}`: quem o bot é nesse desafio e o que o vendedor quer |

### Aba Bots (um personagem por linha)
| Coluna | Uso | O front vê? |
|---|---|---|
| `id` | curto, sem espaço (ex.: `juliana`) | não |
| `ativo` | caixinha | não |
| `desafio` | número do desafio | não |
| `nome` | aparece na tela durante a ligação | sim |
| `ficha` | o que o front sabe antes de ligar, uma informação por linha | sim |
| `saudacao` | primeira fala; `{periodo}` → bom dia/boa tarde | ouve |
| `voz_id` | Voice ID da ElevenLabs. Vazio = Jenifer | não |
| `roteiro` | personalidade, situação, o que revela e sob qual condição | não* |
| `objetivos` | um por linha: `descrição \| pontos` | não |
| `objetivos_secretos` | um por linha: `descrição \| pontos` (bônus) | não |
| `gabarito` | mostrado ao front ao desligar | sim (no fim) |

\* O roteiro passa pelo navegador do front para alimentar o agente. Um front curioso conseguiria lê-lo. Objetivos e pontos nunca saem da planilha.

- **Regra para objetivos secretos:** a informação que vale ponto precisa estar escrita no roteiro, junto com a condição para o bot revelá-la. Exemplo: "só conte da cobrança se perguntarem sobre surpresas na conta".
- **Bots de exemplo** (criados pelo `configurar`):
  - `juliana`: desafio 1, recepcionista da Metalúrgica Serrana;
  - `ricardo`: desafio 2, gerente industrial já no ACL, contrato até dez/2027, dor escondida de uma cobrança de ~R$ 40 mil na CCEE.
- O Davi vai escrever os roteiros definitivos.

### Aba Ligacoes (uma linha por ligação, preenchida pelo script)
| Coluna | Conteúdo |
|---|---|
| `conversation_id`, `data`, `vendedor`, `desafio`, `bot`, `duracao_s` | identificação |
| `objetivos`, `secretos` | resumo "4 de 6" / "1 de 2" |
| `pts_objetivos`, `pts_secretos`, `total` | pontos (a soma é feita pelo script, não pela IA) |
| `O1`–`O6`, `S1`–`S3` | ✔ verde / ✘ vermelho por objetivo. Nota na célula com a descrição e a evidência. Os secretos têm cabeçalho roxo. Objetivos além do 6º contam nos pontos, mas não ganham coluna |
| `feedback` | 2–3 frases do Claude para o front |
| `detalhe` | lista completa ✔/✘ com evidências |
| `audio`, `transcricao` | links do Drive |
| `exemplo` | caixinha. Marcada = o script copia mp3 e txt para a pasta Exemplos |
| `copiado`, `status` | controle (`ok`, `falhou`, `erro: …`) |

### Aba Ranking
Fórmula `QUERY` somando o `total` por vendedor (só `status = ok`). A página `ranking.html` usa `doGet?acao=ranking`, que calcula pontos, ligações, ✔ e ★ por vendedor. O desempate é por mais secretos, depois mais objetivos.

### Avaliação pelo Claude (dentro do `Codigo.gs`)
- **Endpoint:** `POST https://api.anthropic.com/v1/messages`, com os cabeçalhos `anthropic-version: 2026-10-21` e `anthropic-beta: server-side-fallback-2026-07-01`.
- **Modelo:** `claude-opus-5-5`, `fallbacks: "default"`, `output_config.effort: "low"`.
- **Formato da resposta:** `output_config.format` com JSON schema `{objetivos[{indice,cumprido,evidencia}], secretos[...], feedback}`.
- Uma recusa ou um `max_tokens` estourado viram status de erro.

### APIs da ElevenLabs usadas pelo script
- **Cabeçalho:** `xi-api-key`.
- `GET /v1/convai/conversations?agent_id=…&page_size=50`: só processa `status` `done` ou `failed`.
- `GET /v1/convai/conversations/{id}`: usa `transcript[]`, `metadata`, `user_id`, `conversation_initiation_client_data.dynamic_variables`, `has_audio`.
- `GET /v1/convai/conversations/{id}/audio`: arquivo de áudio.
- **Permissão da chave:** ElevenAgents = **Escrita**. Ler não basta para editar o agente; para o script, leitura bastaria, mas Escrita também serve.

## 8. Testes já feitos

- **Página do front e ranking:** testados com Playwright/Chromium e API simulada:
  - validação de nome e aceite;
  - cards por desafio;
  - fluxo chamando → erro → tela final → gabarito;
  - revelação do pódio;
  - nenhum erro de JS.
- **Lógica do `Codigo.gs`:** testada em Node com serviços simulados:
  - pontuação, inclusive com índices fora de ordem;
  - ✔/✘ e notas;
  - ranking ignorando erros, com desempate;
  - conversão de número para letra de coluna.
- **Agente:** ligação real de teste no painel (bot "Érica", desafio 2). Voz natural, pausa pequena, resistiu "um pouco" (o Davi achou bom).
- **Ainda não testado de ponta a ponta:**
  - página real + ElevenLabs real + planilha real;
  - a URL do app da web ainda não existe.

## 9. Estado atual (29/10/2026)

- ✅ Páginas `index.html` e `ranking.html` prontas no branch `coldcall-simulador` (não publicado; o `main` não foi tocado).
- ✅ Agente da ElevenLabs configurado e publicado, `AGENT_ID` fixado na página.
- ✅ `Codigo.gs` pronto. ⏳ A planilha ainda **não foi criada**.
- ⏳ `API_URL` vazio nas duas páginas.
- ⚠️ **Segurança:** a chave da ElevenLabs `config-temporaria` (criada para configurar o agente via API) **passou pela conversa e precisa ser apagada** em Desenvolvedores → API Keys. Crie outra só para o Apps Script e cole direto no menu da planilha.

## 10. Próximos passos (em ordem)

1. [ ] **Apagar a chave `config-temporaria`** na ElevenLabs e criar uma nova (ElevenAgents = Escrita) para o Apps Script.
2. [ ] **Pegar uma chave da API da Anthropic** (console.anthropic.com).
3. [ ] **Criar a planilha** e colar `coldcall/apps-script/Codigo.gs` em Extensões → Apps Script.
4. [ ] Rodar **Configurar planilha e pastas** e depois **Configurar chaves e agente** (Agent ID `agent_1301m6210yfwfrcb95egc9w0jvfr`).
5. [ ] **Implantar como App da Web** e colar a URL em `API_URL` de `index.html` e `ranking.html`. Commit no branch.
6. [ ] **Liberar o merge** do branch `coldcall-simulador` no `main` (com ok do Davi) para publicar no GitHub Pages.
7. [ ] **Teste de ponta a ponta:**
   - uma ligação real pela página;
   - conferir a linha na aba Ligacoes (✔/✘, pontos, feedback, links do Drive);
   - conferir o consumo real de créditos;
   - marcar `exemplo` e ver a cópia na pasta Exemplos;
   - abrir o `ranking.html`.
8. [ ] **Montar o elenco de vozes:**
   - em Vozes, filtrar Portuguese/Brazilian;
   - adicionar às vozes da conta;
   - copiar o Voice ID para a coluna `voz_id` de cada bot;
   - 2 vozes femininas e 2 masculinas bastam.
9. [ ] **Davi escreve os roteiros definitivos** na aba Bots: personagem, objetivos e secretos com pontos.
10. [ ] **Decidir o plano** pelas ligações simultâneas (Free 4 / Starter 6 / Creator 10), de acordo com a data do workshop.
11. [ ] **Ensaiar** com 2 ou 3 pessoas ligando ao mesmo tempo.
12. [ ] **Depois do workshop:**
    - desativar ou apagar o agente;
    - cancelar a assinatura, se houver;
    - remover os gatilhos do Apps Script.

## 11. Pontos de atenção

- **LGPD:** a gravação é avisada na página por uma caixinha obrigatória. Avise também verbalmente no início do workshop.
- **Fone de ouvido com microfone é obrigatório:** vários fronts na mesma sala captam uns aos outros.
- **Allowlist:** a ElevenLabs aceita só `davimorgado-arch.github.io`. Testar de outro domínio exige adicioná-lo.
- **Bot condescendente:** LLM tende a ceder fácil. Se os bots ficarem "bonzinhos", reforce a resistência no roteiro, e não no prompt geral.
- **Modo expressivo (tags de áudio)** está ligado por padrão no V3. Ainda não foi explorado no prompt; é uma opção para dar mais realismo depois.
- **Limite do Apps Script:** processa até 5 ligações por minuto (`MAX_POR_EXECUCAO`). Com 7 fronts, a fila se resolve em 1 ou 2 minutos.
- **Não alterar o `main`** sem ok do Davi: o mesmo site hospeda páginas de apps na App Store (Jorne, Grifo, Edge Deck).

## 12. Preferências do Davi (para quem continuar)

- Português brasileiro, direto, sem bajulação. Pode discordar quando tiver motivo.
- Respostas curtas. Mostrar a linha de raciocínio.
- Planejar antes de executar e apresentar o plano brevemente.
- Dúvidas simples: resolver e informar. Dúvidas de alto impacto: trazer opções antes de agir.
- Código comentado de forma objetiva. Preferir o simples e manutenível.
- Formação em engenharia elétrica, área comercial: não explicar o básico de energia.

## 13. Como retomar no ambiente local

```bash
git clone https://github.com/davimorgado-arch/davimorgado-arch.github.io.git
cd davimorgado-arch.github.io
git checkout coldcall-simulador
```
Abra o Claude Code nessa pasta e peça para ele ler `coldcall/PROJETO.md`.

Com o **Claude in Chrome** disponível, as tarefas de navegador são:
- criar a planilha e colar o código;
- rodar os menus;
- implantar o app da web;
- montar o elenco de vozes na ElevenLabs.
