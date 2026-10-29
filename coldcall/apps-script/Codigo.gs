// ═══════════════════════════════════════════════════════════════
// Simulador de Cold Call — planilha de controle
// • Serve desafios e bots para a página e o ranking (app da web: doGet)
// • A cada minuto: busca ligações novas na ElevenLabs, salva áudio e
//   transcrição no Drive, pontua com o Claude e registra na planilha
// • Copia as ligações marcadas como "exemplo" para a pasta de exemplos
// ═══════════════════════════════════════════════════════════════

// ─── CONFIGURAÇÃO ────────────────────────────────────────────
const CONFIG = {
  ABA_DESAFIOS:     'Desafios',
  ABA_BOTS:         'Bots',
  ABA_LIGACOES:     'Ligacoes',
  ABA_RANKING:      'Ranking',
  FUSO:             'America/Sao_Paulo',
  NOME_PASTA:       'Simulador Cold Call',
  MODELO:           'claude-opus-5-5',
  ESFORCO:          'low',     // avaliação é quase classificação; "low" responde rápido
  MAX_POR_EXECUCAO: 5,         // ligações processadas por minuto (limite de 6 min do GAS)
  CACHE_SEG:        60,        // cache das respostas do app da web
  MAX_OBJ:          6,         // colunas O1..O6 (objetivos)
  MAX_SEC:          3,         // colunas S1..S3 (objetivos secretos)
  VERDE:            '#c8e6c9',
  VERMELHO:         '#ffcdd2',
};

const COLS_DESAFIOS = ['numero', 'ativo', 'titulo', 'descricao', 'objetivo', 'contexto'];
const COLS_BOTS     = ['id', 'ativo', 'desafio', 'nome', 'ficha', 'saudacao', 'voz_id',
                       'roteiro', 'objetivos', 'objetivos_secretos', 'gabarito'];
// Campos que a página recebe. Objetivos e pontos NÃO saem da planilha.
const PUBLICOS_DESAFIOS = ['numero', 'titulo', 'descricao', 'objetivo', 'contexto'];
const PUBLICOS_BOTS     = ['id', 'desafio', 'nome', 'ficha', 'saudacao', 'voz_id', 'roteiro', 'gabarito'];

const COLS_O = Array.from({ length: CONFIG.MAX_OBJ }, (_, i) => 'O' + (i + 1));
const COLS_S = Array.from({ length: CONFIG.MAX_SEC }, (_, i) => 'S' + (i + 1));
const COLS_LIG = ['conversation_id', 'data', 'vendedor', 'desafio', 'bot', 'duracao_s',
                  'objetivos', 'secretos', 'pts_objetivos', 'pts_secretos', 'total',
                  ...COLS_O, ...COLS_S,
                  'feedback', 'detalhe', 'audio', 'transcricao', 'exemplo', 'copiado', 'status'];
const COL = Object.fromEntries(COLS_LIG.map((c, i) => [c, i]));   // índice 0-based por nome

// ─── MENU ────────────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📞 Cold Call')
    .addItem('1. Configurar planilha e pastas', 'configurar')
    .addItem('2. Configurar chaves e agente', 'configurarChaves')
    .addSeparator()
    .addItem('🔄 Processar ligações agora', 'processarAgora')
    .addItem('♻️ Reprocessar ligações com erro', 'reprocessarErros')
    .addToUi();
}

// ─── ENTRADAS PRINCIPAIS ─────────────────────────────────────

// Cria abas, cabeçalhos, pastas no Drive e o gatilho de 1 minuto
function configurar() {
  const ui = SpreadsheetApp.getUi();
  try {
    const ss    = SpreadsheetApp.getActiveSpreadsheet();
    const props = PropertiesService.getScriptProperties();
    props.setProperty('PLANILHA_ID', ss.getId());

    criarAbaDesafios_(ss);
    criarAbaBots_(ss);
    criarAbaLigacoes_(ss);
    criarAbaRanking_(ss);
    criarPastas_(props);

    ScriptApp.getProjectTriggers()
      .filter(t => t.getHandlerFunction() === 'sincronizar')
      .forEach(t => ScriptApp.deleteTrigger(t));
    ScriptApp.newTrigger('sincronizar').timeBased().everyMinutes(1).create();

    ui.alert('✅ Planilha, pastas e gatilho configurados.\nPróximo passo: menu "2. Configurar chaves e agente".');
  } catch (e) {
    ui.alert('❌ Erro: ' + e.message);
  }
}

// Guarda as chaves nas propriedades do script (nunca na planilha)
function configurarChaves() {
  const ui    = SpreadsheetApp.getUi();
  const props = PropertiesService.getScriptProperties();
  try {
    const campos = [
      ['ELEVENLABS_API_KEY', 'Chave da API da ElevenLabs'],
      ['ANTHROPIC_API_KEY',  'Chave da API da Anthropic (Claude)'],
      ['AGENT_ID',           'ID do agente da ElevenLabs (agent_...)'],
    ];
    campos.forEach(([chave, rotulo]) => {
      const atual = props.getProperty(chave) ? ' (já configurado — deixe vazio para manter)' : '';
      const r = ui.prompt(rotulo + atual, ui.ButtonSet.OK_CANCEL);
      if (r.getSelectedButton() !== ui.Button.OK) return;
      const valor = r.getResponseText().trim();
      if (valor) props.setProperty(chave, valor);
    });
    ui.alert('✅ Chaves salvas.');
  } catch (e) {
    ui.alert('❌ Erro: ' + e.message);
  }
}

// Gatilho de 1 minuto (sem UI)
function sincronizar() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;            // execução anterior ainda rodando
  try {
    const props = PropertiesService.getScriptProperties().getProperties();
    if (!props.ELEVENLABS_API_KEY || !props.ANTHROPIC_API_KEY || !props.AGENT_ID) return;
    const ss = SpreadsheetApp.openById(props.PLANILHA_ID);
    processarNovas_(ss, props);
    copiarExemplos_(ss, props);
  } catch (e) {
    console.error('sincronizar: ' + e.message);
  } finally {
    lock.releaseLock();
  }
}

function processarAgora() {
  try {
    sincronizar();
    SpreadsheetApp.getUi().alert('✅ Processamento concluído.');
  } catch (e) {
    SpreadsheetApp.getUi().alert('❌ Erro: ' + e.message);
  }
}

// Apaga as linhas com status de erro; o próximo ciclo processa essas ligações de novo
function reprocessarErros() {
  try {
    const aba    = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.ABA_LIGACOES);
    const linhas = aba.getDataRange().getValues();
    let apagadas = 0;
    for (let i = linhas.length - 1; i >= 1; i--) {   // de baixo para cima para não deslocar índices
      if (String(linhas[i][COL.status]).startsWith('erro')) { aba.deleteRow(i + 1); apagadas++; }
    }
    SpreadsheetApp.getUi().alert(`✅ ${apagadas} linha(s) removida(s). Serão reprocessadas no próximo minuto.`);
  } catch (e) {
    SpreadsheetApp.getUi().alert('❌ Erro: ' + e.message);
  }
}

// App da web:
//   ?acao=ranking → ranking por vendedor (página do pódio)
//   sem parâmetro → desafios e bots ativos, só campos públicos (página do simulador)
function doGet(e) {
  const acao  = (e && e.parameter && e.parameter.acao) || 'bots';
  const cache = CacheService.getScriptCache();
  let json = cache.get(acao);
  if (!json) {
    const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('PLANILHA_ID'));
    const dados = acao === 'ranking' ? { ranking: calcularRanking_(ss) } : {
      desafios: lerTabela_(ss, CONFIG.ABA_DESAFIOS).filter(d => d.ativo === true).map(d => publico_(d, PUBLICOS_DESAFIOS)),
      bots:     lerTabela_(ss, CONFIG.ABA_BOTS).filter(b => b.ativo === true).map(b => publico_(b, PUBLICOS_BOTS)),
    };
    json = JSON.stringify(dados);
    cache.put(acao, json, CONFIG.CACHE_SEG);
  }
  return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
}

// ─── PROCESSAMENTO DAS LIGAÇÕES ──────────────────────────────

function processarNovas_(ss, props) {
  const aba        = ss.getSheetByName(CONFIG.ABA_LIGACOES);
  const existentes = new Set(aba.getRange('A:A').getValues().flat().filter(String));

  const lista = elevenJSON_(`/v1/convai/conversations?agent_id=${encodeURIComponent(props.AGENT_ID)}&page_size=50`, props);
  const novas = (lista.conversations || [])
    .filter(c => !existentes.has(c.conversation_id) && (c.status === 'done' || c.status === 'failed'))
    .reverse()                                   // mais antigas primeiro
    .slice(0, CONFIG.MAX_POR_EXECUCAO);
  if (!novas.length) return;

  const bots   = Object.fromEntries(lerTabela_(ss, CONFIG.ABA_BOTS).map(b => [String(b.id), b]));
  const pastas = { gravacoes: DriveApp.getFolderById(props.PASTA_GRAVACOES_ID) };

  const res = novas.map(c => {
    try {
      return processarConversa_(c.conversation_id, bots, pastas, props);
    } catch (e) {
      // Linha de erro evita loop infinito; "Reprocessar ligações com erro" tenta de novo
      const l = linhaVazia_();
      l[COL.conversation_id] = c.conversation_id;
      l[COL.data]            = new Date(c.start_time_unix_secs * 1000);
      l[COL.status]          = 'erro: ' + e.message.slice(0, 300);
      return { linha: l, notas: notasVazias_() };
    }
  });

  // Escrita em lote: valores, notas dos ✔/✘ e caixinha de exemplo
  const inicio = aba.getLastRow() + 1;
  const n      = res.length;
  aba.getRange(inicio, 1, n, COLS_LIG.length).setValues(res.map(r => r.linha));
  aba.getRange(inicio, COL.O1 + 1, n, COLS_O.length + COLS_S.length).setNotes(res.map(r => r.notas));
  aba.getRange(inicio, COL.exemplo + 1, n, 1).insertCheckboxes();
}

function processarConversa_(id, bots, pastas, props) {
  const d     = elevenJSON_(`/v1/convai/conversations/${id}`, props);
  const init  = d.conversation_initiation_client_data || {};
  const dyn   = init.dynamic_variables || {};
  const meta  = d.metadata || {};
  const data  = new Date(meta.start_time_unix_secs * 1000);
  const vend  = d.user_id || init.user_id || '(sem nome)';
  const botId = String(dyn.bot_id || '');
  const bot   = bots[botId];

  // Transcrição legível: [mm:ss] Vendedor/Lead: fala
  const falas = (d.transcript || []).filter(t => t.message);
  const transcricao = falas
    .map(t => `[${mmss_(t.time_in_call_secs)}] ${t.role === 'agent' ? 'Lead' : 'Vendedor'}: ${t.message}`)
    .join('\n');

  // Arquivos no Drive
  const base = limparNome_(`${Utilities.formatDate(data, CONFIG.FUSO, 'yyyy-MM-dd HH.mm')} - ${vend} - ${botId || 'sem-bot'} - ${id}`);
  const linkTxt = pastas.gravacoes.createFile(base + '.txt', transcricao || '(sem falas)', MimeType.PLAIN_TEXT).getUrl();
  let linkAudio = '';
  if (d.has_audio) {
    const blob = elevenBlob_(`/v1/convai/conversations/${id}/audio`, props).setName(base + '.mp3');
    linkAudio = pastas.gravacoes.createFile(blob).getUrl();
  }

  const l = linhaVazia_();
  l[COL.conversation_id] = id;
  l[COL.data]            = data;
  l[COL.vendedor]        = vend;
  l[COL.desafio]         = dyn.desafio || (bot ? bot.desafio : '');
  l[COL.bot]             = bot ? `${botId} · ${bot.nome}` : botId;
  l[COL.duracao_s]       = meta.call_duration_secs || 0;
  l[COL.audio]           = linkAudio;
  l[COL.transcricao]     = linkTxt;
  const vazio = { linha: l, notas: notasVazias_() };

  // Casos sem avaliação
  if (d.status === 'failed')               { l[COL.status] = 'falhou'; return vazio; }
  if (!bot)                                { l[COL.status] = 'erro: bot "' + botId + '" não encontrado na aba Bots'; return vazio; }
  const objetivos = parseObjetivos_(bot.objetivos);
  const secretos  = parseObjetivos_(bot.objetivos_secretos);
  if (!falas.some(t => t.role === 'user')) {
    l[COL.status]    = 'ok';
    l[COL.feedback]  = 'Ligação sem fala do vendedor.';
    l[COL.objetivos] = `0 de ${objetivos.length}`;
    l[COL.secretos]  = `0 de ${secretos.length}`;
    return vazio;
  }

  // Avaliação pelo Claude
  const aval   = avaliar_(bot.roteiro, objetivos, secretos, transcricao, props);
  const resObj = indexar_(aval.objetivos);
  const resSec = indexar_(aval.secretos);
  const ok     = (res, i) => !!(res[i] && res[i].cumprido);

  l[COL.pts_objetivos] = objetivos.reduce((s, o, i) => s + (ok(resObj, i) ? o.pts : 0), 0);
  l[COL.pts_secretos]  = secretos.reduce((s, o, i) => s + (ok(resSec, i) ? o.pts : 0), 0);
  l[COL.total]         = l[COL.pts_objetivos] + l[COL.pts_secretos];
  l[COL.objetivos]     = `${objetivos.filter((_, i) => ok(resObj, i)).length} de ${objetivos.length}`;
  l[COL.secretos]      = `${secretos.filter((_, i) => ok(resSec, i)).length} de ${secretos.length}`;

  // Células ✔/✘ por objetivo, com nota (descrição + evidência) para passar o mouse
  const notas = notasVazias_();
  const marcar = (lista, res, cols, prefixo) => lista.slice(0, cols.length).forEach((o, i) => {
    l[COL[cols[i]]] = ok(res, i) ? '✔' : '✘';
    notas[COL[cols[i]] - COL.O1] = `${prefixo}${o.desc} (${o.pts} pts)` + (res[i] ? `\n— ${res[i].evidencia}` : '');
  });
  marcar(objetivos, resObj, COLS_O, '');
  marcar(secretos,  resSec, COLS_S, '★ ');

  l[COL.detalhe] = [
    ...objetivos.map((o, i) => linhaDetalhe_(o, resObj[i], '')),
    ...secretos.map((o, i)  => linhaDetalhe_(o, resSec[i], '★ ')),
  ].join('\n');
  l[COL.feedback] = aval.feedback || '';
  l[COL.status]   = 'ok';
  return { linha: l, notas };
}

// ─── AVALIAÇÃO (Claude) ──────────────────────────────────────

function avaliar_(roteiro, objetivos, secretos, transcricao, props) {
  const lista = arr => arr.length ? arr.map((o, i) => `${i + 1}. ${o.desc}`).join('\n') : '(nenhum)';

  const system =
    'Você avalia um treinamento de prospecção por telefone no mercado livre de energia. ' +
    'Um vendedor ligou para um personagem simulado. Decida, com base SOMENTE na transcrição, ' +
    'se cada objetivo foi cumprido. Marque cumprido apenas com evidência clara na transcrição. ' +
    'A transcrição vem de reconhecimento de voz e pode ter erros de grafia: não penalize isso. ' +
    'Em "evidencia", cite em poucas palavras o trecho que comprova (ou por que não foi cumprido). ' +
    'Em "feedback", escreva 2 a 3 frases diretas ao vendedor: o que fez bem e o que melhorar.';

  const user =
    `<personagem>\n${roteiro}\n</personagem>\n\n` +
    `<objetivos>\n${lista(objetivos)}\n</objetivos>\n\n` +
    `<objetivos_secretos>\n${lista(secretos)}\n</objetivos_secretos>\n\n` +
    `<transcricao>\n${transcricao}\n</transcricao>\n\n` +
    'Avalie todos os objetivos e objetivos secretos pelo número (indice).';

  const item = {
    type: 'object',
    properties: {
      indice:    { type: 'integer' },
      cumprido:  { type: 'boolean' },
      evidencia: { type: 'string' },
    },
    required: ['indice', 'cumprido', 'evidencia'],
    additionalProperties: false,
  };
  const schema = {
    type: 'object',
    properties: {
      objetivos: { type: 'array', items: item },
      secretos:  { type: 'array', items: item },
      feedback:  { type: 'string' },
    },
    required: ['objetivos', 'secretos', 'feedback'],
    additionalProperties: false,
  };

  const resp = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    headers: {
      'x-api-key':         props.ANTHROPIC_API_KEY,
      'anthropic-version': '2026-10-21',
      'anthropic-beta':    'server-side-fallback-2026-07-01',   // refaz em outro modelo se houver recusa
    },
    payload: JSON.stringify({
      model:         CONFIG.MODELO,
      max_tokens:    16000,
      fallbacks:     'default',
      output_config: { effort: CONFIG.ESFORCO, format: { type: 'json_schema', schema } },
      system,
      messages: [{ role: 'user', content: user }],
    }),
  });

  if (resp.getResponseCode() >= 400) throw new Error(`Claude HTTP ${resp.getResponseCode()}: ${resp.getContentText().slice(0, 200)}`);
  const msg = JSON.parse(resp.getContentText());
  if (msg.stop_reason === 'refusal')    throw new Error('Claude recusou a avaliação');
  if (msg.stop_reason === 'max_tokens') throw new Error('Resposta do Claude cortada (max_tokens)');
  const texto = (msg.content || []).find(b => b.type === 'text');
  if (!texto) throw new Error('Resposta do Claude sem texto');
  return JSON.parse(texto.text);
}

// ─── RANKING ─────────────────────────────────────────────────

// Soma por vendedor das ligações avaliadas (status "ok")
function calcularRanking_(ss) {
  const aba = ss.getSheetByName(CONFIG.ABA_LIGACOES);
  const n   = aba.getLastRow() - 1;
  if (n < 1) return [];
  const dados = aba.getRange(2, 1, n, COLS_LIG.length).getValues();
  const por   = {};
  dados.filter(r => r[COL.status] === 'ok' && r[COL.vendedor]).forEach(r => {
    const v = String(r[COL.vendedor]).trim();
    const p = por[v] = por[v] || { vendedor: v, pontos: 0, ligacoes: 0, objetivos: 0, secretos: 0 };
    p.pontos    += Number(r[COL.total]) || 0;
    p.ligacoes  += 1;
    p.objetivos += COLS_O.filter(c => r[COL[c]] === '✔').length;
    p.secretos  += COLS_S.filter(c => r[COL[c]] === '✔').length;
  });
  // Desempate: mais secretos, depois mais objetivos
  return Object.values(por).sort((a, b) => b.pontos - a.pontos || b.secretos - a.secretos || b.objetivos - a.objetivos);
}

// ─── EXEMPLOS ────────────────────────────────────────────────

// Linhas com "exemplo" marcado e ainda não copiadas → cópia do áudio e da transcrição
function copiarExemplos_(ss, props) {
  const aba   = ss.getSheetByName(CONFIG.ABA_LIGACOES);
  const n     = aba.getLastRow() - 1;
  if (n < 1) return;
  const dados = aba.getRange(2, 1, n, COLS_LIG.length).getValues();
  const pasta = DriveApp.getFolderById(props.PASTA_EXEMPLOS_ID);
  let mudou   = false;

  const copiado = dados.map(r => {
    if (r[COL.exemplo] !== true || r[COL.copiado]) return [r[COL.copiado]];
    [r[COL.audio], r[COL.transcricao]].filter(String).forEach(url => {
      const f = DriveApp.getFileById(idDoLink_(url));
      f.makeCopy(f.getName(), pasta);
    });
    mudou = true;
    return ['sim'];
  });
  if (mudou) aba.getRange(2, COL.copiado + 1, n, 1).setValues(copiado);
}

// ─── ESTRUTURA DA PLANILHA ───────────────────────────────────

function criarAbaDesafios_(ss) {
  if (ss.getSheetByName(CONFIG.ABA_DESAFIOS)) return;
  const aba = ss.insertSheet(CONFIG.ABA_DESAFIOS);
  const ex  = [
    [1, true, 'Desafio 1 · Lead frio',
      'Você liga para a empresa sem conhecer ninguém. Quem atende raramente é quem decide.',
      'Descobrir quem é o responsável pela energia elétrica (nome e cargo) e conseguir um contato direto. Não é para vender nada.',
      'Você atende o telefone da empresa. Quem liga é um vendedor de uma empresa de gestão de energia / mercado livre. O objetivo dele é descobrir quem é o responsável pela energia elétrica e conseguir um contato direto. Você não decide nada sobre energia.'],
    [2, true, 'Desafio 2 · Primeiro contato',
      'Você já tem o nome do responsável e liga direto para ele. É o primeiro contato.',
      'Descobrir a situação energética (cativo ou livre, contrato, vencimento, quem faz a gestão, tamanho da conta) e sair com um próximo passo concreto (reunião ou envio de fatura).',
      'Você é o responsável pela energia na empresa e está recebendo a PRIMEIRA ligação deste vendedor de gestão de energia / mercado livre. Você não conhece a empresa dele. O objetivo dele é entender sua situação energética e sair com um próximo passo (reunião ou envio de fatura).'],
  ];
  aba.getRange(1, 1, 1, COLS_DESAFIOS.length).setValues([COLS_DESAFIOS]);
  aba.getRange(2, 1, ex.length, COLS_DESAFIOS.length).setValues(ex);
  formatarCabecalho_(aba.getRange(1, 1, 1, COLS_DESAFIOS.length));
  aba.getRange(2, 2, 50, 1).insertCheckboxes();
  aba.getRange(2, 2, ex.length, 1).setValue(true);
  aba.getRange('A:F').setWrap(true).setVerticalAlignment('top');
  aba.setColumnWidths(3, 4, 300);
  aba.setFrozenRows(1);
}

function criarAbaBots_(ss) {
  if (ss.getSheetByName(CONFIG.ABA_BOTS)) return;
  const aba = ss.insertSheet(CONFIG.ABA_BOTS);
  aba.getRange(1, 1, 1, COLS_BOTS.length).setValues([COLS_BOTS]);
  formatarCabecalho_(aba.getRange(1, 1, 1, COLS_BOTS.length));
  const ex = botsExemplo_();
  aba.getRange(2, 1, ex.length, COLS_BOTS.length).setValues(ex);
  aba.getRange(2, 2, 200, 1).insertCheckboxes();                         // coluna "ativo"
  aba.getRange(2, 2, ex.length, 1).setValue(true);
  aba.getRange('A:K').setWrap(true).setVerticalAlignment('top');
  aba.setColumnWidths(5, 7, 320);
  aba.setFrozenRows(1);
}

function criarAbaLigacoes_(ss) {
  if (ss.getSheetByName(CONFIG.ABA_LIGACOES)) return;
  const aba = ss.insertSheet(CONFIG.ABA_LIGACOES);
  aba.getRange(1, 1, 1, COLS_LIG.length).setValues([COLS_LIG]);
  formatarCabecalho_(aba.getRange(1, 1, 1, COLS_LIG.length));
  aba.getRange(1, COL.S1 + 1, 1, COLS_S.length).setBackground('#7b1fa2');   // secretos em roxo

  const letra = c => colLetra_(COL[c] + 1);
  aba.getRange(`${letra('data')}:${letra('data')}`).setNumberFormat('dd/mm/yyyy HH:mm');

  // Colunas ✔/✘ estreitas, centralizadas, verde/vermelho
  const marcas = aba.getRange(`${letra('O1')}2:${colLetra_(COL.O1 + COLS_O.length + COLS_S.length)}`);
  marcas.setHorizontalAlignment('center').setFontWeight('bold');
  aba.setColumnWidths(COL.O1 + 1, COLS_O.length + COLS_S.length, 40);
  aba.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('✔').setBackground(CONFIG.VERDE).setFontColor('#1b5e20').setRanges([marcas]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('✘').setBackground(CONFIG.VERMELHO).setFontColor('#b71c1c').setRanges([marcas]).build(),
  ]);

  aba.getRange(`${letra('feedback')}:${letra('detalhe')}`).setWrap(true).setVerticalAlignment('top');
  aba.setColumnWidths(COL.feedback + 1, 2, 360);
  aba.setFrozenRows(1);
  aba.setFrozenColumns(3);
}

function criarAbaRanking_(ss) {
  if (ss.getSheetByName(CONFIG.ABA_RANKING)) return;
  const aba   = ss.insertSheet(CONFIG.ABA_RANKING);
  const letra = c => colLetra_(COL[c] + 1);
  const L     = { v: letra('vendedor'), t: letra('total'), s: letra('status'), id: letra('conversation_id') };
  // Planilha em pt-BR exige ";" entre argumentos (com "," dá erro de análise)
  const sep = ss.getSpreadsheetLocale().startsWith('en') ? ',' : ';';
  // Soma só ligações avaliadas (status "ok"). IFERROR cobre a aba Ligacoes ainda vazia
  aba.getRange('A1').setFormula(
    `=IFERROR(QUERY(${CONFIG.ABA_LIGACOES}!A:${colLetra_(COLS_LIG.length)}${sep}"select ${L.v}, sum(${L.t}), count(${L.id}), max(${L.t}) ` +
    `where ${L.v} is not null and ${L.s} = 'ok' group by ${L.v} order by sum(${L.t}) desc ` +
    `label ${L.v} 'Vendedor', sum(${L.t}) 'Pontos', count(${L.id}) 'Ligações', max(${L.t}) 'Melhor ligação'"${sep}1)${sep}"Aguardando ligações avaliadas")`
  );
  aba.setColumnWidth(1, 220);
}

function criarPastas_(props) {
  if (props.getProperty('PASTA_GRAVACOES_ID')) return;
  const raiz = DriveApp.createFolder(CONFIG.NOME_PASTA);
  props.setProperty('PASTA_RAIZ_ID',      raiz.getId());
  props.setProperty('PASTA_GRAVACOES_ID', raiz.createFolder('Gravações').getId());
  props.setProperty('PASTA_EXEMPLOS_ID',  raiz.createFolder('Exemplos').getId());
}

// Dois bots de exemplo (um por desafio) para mostrar o formato e permitir teste
function botsExemplo_() {
  return [
    [
      'juliana', true, 1, 'Metalúrgica Serrana · Recepção',
      'Empresa: Metalúrgica Serrana\nSegmento: Metalurgia (peças automotivas)\nCidade: Caxias do Sul/RS\nTelefone: central da empresa',
      'Metalúrgica Serrana, {periodo}!', '',
      'Você é Juliana, recepcionista da Metalúrgica Serrana (Caxias do Sul/RS) há 6 anos. Simpática, mas tem ordem expressa de não passar ligação de vendedor. Costuma mandar "enviar e-mail para o comercial@".\n' +
      'O responsável pela energia é Ricardo Bassani, gerente industrial. Ramal 230, e-mail ricardo.bassani@metalserrana.com.br. Ele fica na fábrica de manhã; à tarde é mais fácil de achar na sala.\n' +
      'Primeiro diga só a área ("isso é com a parte industrial"), depois o nome, e o ramal/e-mail só se pedirem com educação e motivo claro. Se o vendedor for gentil e direto, você ajuda; se enrolar ou fizer pitch, você corta.',
      'Disse nome, empresa e motivo da ligação nos primeiros 20 segundos | 10\nDescobriu o nome do responsável pela energia | 20\nDescobriu o cargo ou área do responsável | 10\nConseguiu um contato direto (ramal ou e-mail) | 20',
      'Descobriu o melhor horário para encontrar o responsável (à tarde) | 10\nConseguiu o contato sem fazer nenhum pitch de produto para a recepcionista | 10',
      'Responsável: Ricardo Bassani, gerente industrial. Ramal 230 · ricardo.bassani@metalserrana.com.br. Melhor horário: à tarde.',
    ],
    [
      'ricardo', true, 2, 'Ricardo Bassani · Metalúrgica Serrana',
      'Empresa: Metalúrgica Serrana\nSegmento: Metalurgia (peças automotivas)\nCidade: Caxias do Sul/RS\nContato: Ricardo Bassani, gerente industrial',
      'Ricardo falando.', '',
      'Você é Ricardo Bassani, 51 anos, gerente industrial e engenheiro da Metalúrgica Serrana. Cordial, mas acha que energia "já está resolvido".\n' +
      'Situação (revele só quando perguntado, aos poucos): está no mercado livre desde 2022, com contrato com uma comercializadora até dezembro de 2027. A própria comercializadora "faz a gestão"; não há gestora independente. Ano passado tomou uma cobrança inesperada de uns R$ 40 mil de ajuste na CCEE e ninguém explicou direito — só conte isso se o vendedor perguntar sobre surpresas ou custos inesperados.\n' +
      'Você se interessa se o vendedor perguntar antes de apresentar, entender a diferença entre comprar energia e ter alguém do seu lado fazendo gestão, e não atacar a comercializadora. Aceita reunião de 30 minutos se o vendedor propuser dia e horário.\n' +
      'Objeções: "já estamos no mercado livre", "meu contrato vai até 2027", "a comercializadora já cuida disso".',
      'Abertura: se apresentou, disse a empresa e o motivo, e pediu poucos minutos | 10\nFez perguntas antes de apresentar o serviço | 10\nDescobriu que a empresa já está no mercado livre | 10\nDescobriu o vencimento do contrato | 15\nDescobriu quem faz a gestão hoje | 15\nSaiu com reunião marcada com dia e horário | 25',
      'Descobriu a cobrança inesperada de cerca de R$ 40 mil na CCEE | 20\nNão criticou a comercializadora atual | 10',
      'Mercado livre desde 2022, contrato até dez/2027, gestão feita pela própria comercializadora. Dor escondida: cobrança inesperada de ~R$ 40 mil na CCEE. Próximo passo ideal: reunião para diagnóstico da gestão.',
    ],
  ];
}

// ─── FUNÇÕES INTERNAS ────────────────────────────────────────

function lerTabela_(ss, nomeAba) {
  const linhas = ss.getSheetByName(nomeAba).getDataRange().getValues();
  const header = linhas[0];
  return linhas.slice(1)
    .filter(r => r[0] !== '')
    .map(r => Object.fromEntries(header.map((h, i) => [h, r[i]])));
}

const publico_ = (obj, campos) => Object.fromEntries(campos.map(c => [c, String(obj[c] ?? '')]));

// "descrição | pontos" por linha → [{desc, pts}]
function parseObjetivos_(texto) {
  return String(texto || '').split('\n').map(s => s.trim()).filter(String).map(s => {
    const [desc, pts] = s.split('|').map(x => x.trim());
    return { desc, pts: Number(pts) || 0 };
  });
}

// Resultado do Claude (indice 1-based) → array 0-based
function indexar_(lista) {
  const out = [];
  (lista || []).forEach(r => { out[r.indice - 1] = r; });
  return out;
}

function linhaDetalhe_(obj, res, prefixo) {
  const ok = res && res.cumprido;
  return `${ok ? '✔' : '✘'} ${prefixo}${obj.desc} (${ok ? obj.pts : 0}/${obj.pts})` + (res ? ` — ${res.evidencia}` : '');
}

// Linha nova com zeros e caixinha desmarcada
function linhaVazia_() {
  const l = new Array(COLS_LIG.length).fill('');
  l[COL.pts_objetivos] = 0; l[COL.pts_secretos] = 0; l[COL.total] = 0;
  l[COL.exemplo] = false;
  return l;
}
const notasVazias_ = () => new Array(COLS_O.length + COLS_S.length).fill('');

function elevenJSON_(caminho, props) {
  const resp = UrlFetchApp.fetch('https://api.elevenlabs.io' + caminho, {
    headers: { 'xi-api-key': props.ELEVENLABS_API_KEY }, muteHttpExceptions: true,
  });
  if (resp.getResponseCode() >= 400) throw new Error(`ElevenLabs HTTP ${resp.getResponseCode()}: ${resp.getContentText().slice(0, 200)}`);
  return JSON.parse(resp.getContentText());
}

function elevenBlob_(caminho, props) {
  const resp = UrlFetchApp.fetch('https://api.elevenlabs.io' + caminho, {
    headers: { 'xi-api-key': props.ELEVENLABS_API_KEY }, muteHttpExceptions: true,
  });
  if (resp.getResponseCode() >= 400) throw new Error(`ElevenLabs áudio HTTP ${resp.getResponseCode()}`);
  return resp.getBlob();
}

function formatarCabecalho_(range) {
  range.setBackground('#1a73e8').setFontColor('#fff').setFontWeight('bold');
}

// Número da coluna (1-based) → letra (1 → A, 27 → AA)
function colLetra_(n) {
  let s = '';
  while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

const mmss_       = s => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
const limparNome_ = s => String(s).replace(/[\\/:*?"<>|]/g, '-');
const idDoLink_   = url => (String(url).match(/[-\w]{25,}/) || [])[0];
