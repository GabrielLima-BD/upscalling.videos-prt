const elementos = {
  formulario: document.getElementById('formulario-lote'),
  listaFormulario: document.getElementById('lista-videos-formulario'),
  listaHistorico: document.getElementById('lista-historico'),
  botaoEnviar: document.getElementById('botao-enviar'),
  botaoRecarregar: document.getElementById('botao-recarregar'),
  quantidadeVideos: document.getElementById('quantidade-videos'),
  grupoAtivo: document.getElementById('grupo-ativo'),
  contadorVideos: document.getElementById('contador-videos'),
  toastContainer: document.getElementById('toast-container'),
  indicadorApi: document.getElementById('indicador-api'),
  textoStatusApi: document.getElementById('texto-status-api'),
  botaoEncerrarApp: document.getElementById('botao-encerrar-app'),
  telaEncerramento: document.getElementById('tela-encerramento'),
  textoEncerramento: document.getElementById('texto-encerramento'),
};

const estado = {
  carregando: false,
  proximoIdLocal: 1,
  historicoEmAndamento: false,
  assinaturaHistorico: '',
  intervaloHistorico: null,
  carregandoAtualizacao: false,
  encerrando: false,
};

const INTERVALO_ATUALIZACAO_HISTORICO = 2000;
const CHAVE_GRUPO_ATIVO = 'upscalling_videos_grupo_ativo';
const TEMPO_RELOAD_GRUPO = 280;

function criarIdentificadorLocal() {
  const identificador = `linha-${estado.proximoIdLocal}`;
  estado.proximoIdLocal += 1;
  return identificador;
}

function obterLinhasFormulario() {
  return Array.from(document.querySelectorAll('[data-linha-video]'));
}

function quantidadeDesejada() {
  const valor = Number(elementos.quantidadeVideos.value);
  if (Number.isNaN(valor)) {
    return obterLinhasFormulario().length || 1;
  }
  return Math.min(50, Math.max(1, valor));
}

function atualizarContadorFormulario() {
  const total = obterLinhasFormulario().length;
  elementos.contadorVideos.textContent = String(total);
  elementos.quantidadeVideos.value = String(total);
}

function definirStatusLinha(elementoLinha, status) {
  const badge = elementoLinha.querySelector('[data-status-linha]');
  badge.textContent = status;
  badge.className = `item-video-formulario__status status-${status}`;
  elementoLinha.dataset.status = status;
  elementoLinha.classList.remove('is-pendente', 'is-processando', 'is-enviado', 'is-erro', 'is-rascunho');
  elementoLinha.classList.add(`is-${status}`);
}

function linhaEstaPreenchida(linha) {
  const video = linha.querySelector('.input-video').value.trim();
  const referencia = linha.querySelector('.input-referencia').value.trim();
  return Boolean(video && referencia);
}

function linhaEUltima(linha) {
  const linhas = obterLinhasFormulario();
  return linhas[linhas.length - 1] === linha;
}

function anotarMudancaRascunho(linha) {
  if (!linha.dataset.videoId) {
    definirStatusLinha(linha, 'rascunho');
  }
}

function criarLinhaFormulario(dados = {}) {
  const linha = document.createElement('article');
  linha.className = 'item-video-formulario is-rascunho';
  linha.dataset.linhaVideo = criarIdentificadorLocal();
  linha.dataset.status = 'rascunho';
  linha.dataset.videoId = dados.videoId ? String(dados.videoId) : '';

  linha.innerHTML = `
    <div class="item-video-formulario__cabecalho">
      <h3 class="item-video-formulario__titulo">Vídeo ${obterLinhasFormulario().length + 1}</h3>
      <span class="item-video-formulario__status status-rascunho" data-status-linha>rascunho</span>
    </div>

    <div class="item-video-formulario__grade">
      <label>
        <span>Link do vídeo (.mp4)</span>
        <input type="url" class="input-video" placeholder="https://.../video.mp4" value="${dados.link_video || ''}" required />
      </label>

      <label>
        <span>Link de referência</span>
        <input type="url" class="input-referencia" placeholder="https://..." value="${dados.link_referencia || ''}" required />
      </label>
    </div>
  `;

  const campos = Array.from(linha.querySelectorAll('input'));

  campos.forEach((campo) => {
    campo.addEventListener('input', () => {
      anotarMudancaRascunho(linha);
    });

    campo.addEventListener('keydown', (evento) => {
      if (evento.key !== 'Enter') {
        return;
      }

      evento.preventDefault();
      if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
        adicionarLinhaSeNecessario();
      }
    });

    campo.addEventListener('blur', () => {
      if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
        adicionarLinhaSeNecessario();
      }
    });
  });

  linha.addEventListener('mouseleave', () => {
    if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
      adicionarLinhaSeNecessario();
    }
  });

  return linha;
}

function atualizarTitulosLinha() {
  obterLinhasFormulario().forEach((linha, indice) => {
    const titulo = linha.querySelector('.item-video-formulario__titulo');
    titulo.textContent = `Vídeo ${indice + 1}`;
  });
}

function garantirLinhaInicial() {
  if (obterLinhasFormulario().length === 0) {
    elementos.listaFormulario.appendChild(criarLinhaFormulario());
  }

  atualizarTitulosLinha();
  atualizarContadorFormulario();
}

function adicionarLinhaSeNecessario() {
  const totalAtual = obterLinhasFormulario().length;
  const desejado = quantidadeDesejada();

  if (totalAtual >= desejado || totalAtual >= 50) {
    return;
  }

  elementos.listaFormulario.appendChild(criarLinhaFormulario());
  atualizarTitulosLinha();
  atualizarContadorFormulario();
}

function sincronizarQuantidadeFormulario() {
  const desejado = quantidadeDesejada();
  const linhasAtuais = obterLinhasFormulario();
  const totalAtual = linhasAtuais.length;

  if (desejado === totalAtual) {
    return;
  }

  if (desejado < totalAtual) {
    const linhasRemovidas = linhasAtuais.slice(desejado);
    const possuiDados = linhasRemovidas.some((linha) => {
      const video = linha.querySelector('.input-video').value.trim();
      const referencia = linha.querySelector('.input-referencia').value.trim();
      return Boolean(video || referencia);
    });

    if (possuiDados && !window.confirm('Algumas linhas preenchidas serão removidas. Continuar?')) {
      elementos.quantidadeVideos.value = String(totalAtual);
      return;
    }

    linhasRemovidas.forEach((linha) => linha.remove());
  }

  while (obterLinhasFormulario().length < desejado) {
    elementos.listaFormulario.appendChild(criarLinhaFormulario());
  }

  atualizarTitulosLinha();
  atualizarContadorFormulario();
}

function mostrarToast(mensagem, tipo = 'sucesso') {
  const toast = document.createElement('div');
  toast.className = `toast toast--${tipo}`;
  toast.textContent = mensagem;
  elementos.toastContainer.appendChild(toast);

  window.setTimeout(() => {
    toast.remove();
  }, 4000);
}

function alternarEstadoAtualizacao(ativo) {
  estado.carregandoAtualizacao = ativo;

  if (!elementos.botaoRecarregar) {
    return;
  }

  elementos.botaoRecarregar.disabled = ativo;
  elementos.botaoRecarregar.classList.toggle('is-loading', ativo);
  elementos.botaoRecarregar.textContent = ativo ? 'Atualizando...' : 'Atualizar';
}

function exibirTelaEncerramento(mensagem) {
  estado.encerrando = true;
  document.body.classList.add('is-saindo');

  if (elementos.telaEncerramento) {
    elementos.telaEncerramento.hidden = false;
  }

  if (elementos.textoEncerramento && mensagem) {
    elementos.textoEncerramento.textContent = mensagem;
  }

  if (estado.intervaloHistorico) {
    window.clearInterval(estado.intervaloHistorico);
    estado.intervaloHistorico = null;
  }
}

async function encerrarAplicacao() {
  if (!window.confirm('Deseja encerrar a aplicação e fechar esta guia?')) {
    return;
  }

  exibirTelaEncerramento('A sessão está sendo encerrada agora.');

  if (elementos.botaoEncerrarApp) {
    elementos.botaoEncerrarApp.disabled = true;
    elementos.botaoEncerrarApp.classList.add('is-loading');
  }

  try {
    await fetch('/api/sistema/encerrar', {
      method: 'POST',
      keepalive: true,
    });
  } catch (erro) {
    // Ignora: o processo pode encerrar antes de responder completamente.
  }

  window.setTimeout(() => {
    window.open('', '_self');
    window.close();
  }, 250);

  window.setTimeout(() => {
    if (elementos.textoEncerramento) {
      elementos.textoEncerramento.textContent = 'Se a guia permanecer aberta, feche-a manualmente para concluir.';
    }
  }, 1200);
}

function obterGrupoPersistido() {
  return window.localStorage.getItem(CHAVE_GRUPO_ATIVO);
}

function salvarGrupoPersistido(valor) {
  window.localStorage.setItem(CHAVE_GRUPO_ATIVO, valor);
}

function aplicarAnimacaoSaida() {
  document.body.classList.add('is-saindo');
}

function recarregarPaginaComAnimacao() {
  aplicarAnimacaoSaida();
  window.setTimeout(() => {
    window.location.reload();
  }, TEMPO_RELOAD_GRUPO);
}

function atualizarIndicadorApi(online) {
  if (online) {
    elementos.indicadorApi.classList.add('status-api__bolinha--online');
    elementos.textoStatusApi.textContent = 'API online';
    return;
  }

  elementos.indicadorApi.classList.remove('status-api__bolinha--online');
  elementos.textoStatusApi.textContent = 'API offline';
}

function formatarData(valor) {
  const data = new Date(valor);
  return data.toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  });
}

function obterClasseStatus(status) {
  const mapa = {
    pendente: 'status-pendente',
    processando: 'status-processando',
    enviado: 'status-enviado',
    erro: 'status-erro',
    rascunho: 'status-rascunho',
  };

  return mapa[status] || 'status-rascunho';
}

function obterTextoErro(video) {
  return video.mensagem_erro ? `<p class="item-historico__erro">${video.mensagem_erro}</p>` : '';
}

function formatarAtualizacao(video) {
  return video.atualizado_em ? formatarData(video.atualizado_em) : formatarData(video.criado_em);
}

function gerarAssinaturaHistorico(videos) {
  return JSON.stringify(
    videos.map((video) => ({
      id: video.id,
      status: video.status,
      erro: video.mensagem_erro || '',
      nome: video.nome_produto || '',
      preco: video.preco_produto || '',
      criado_em: video.criado_em || '',
      atualizado_em: video.atualizado_em || '',
    })),
  );
}

function renderizarHistorico(videos) {
  if (!videos.length) {
    elementos.listaHistorico.innerHTML = '<p class="historico-vazio">Nenhum vídeo processado ainda.</p>';
    return;
  }

  elementos.listaHistorico.innerHTML = videos
    .map((video) => `
      <article class="item-historico" data-video-id="${video.id}">
        <div class="item-historico__topo">
          <div>
            <h3 class="item-historico__titulo">Vídeo ${video.id}${video.nome_produto ? ` - ${video.nome_produto}` : ''}</h3>
            <p class="item-historico__meta">Atualizado em ${formatarAtualizacao(video)}</p>
            <p class="item-historico__meta">Criado em ${formatarData(video.criado_em)}</p>
            <p class="item-historico__meta">${video.preco_produto || 'Informação complementar não identificada'}</p>
          </div>
          <span class="selo-status ${obterClasseStatus(video.status)}" data-status-visual="${video.id}">${video.status}</span>
        </div>

        ${obterTextoErro(video)}

        <div class="item-historico__acoes">
          ${video.status === 'erro' ? `<button type="button" class="botao-icone is-sucesso" data-acao="reprocessar" data-video-id="${video.id}">Tentar novamente</button>` : ''}
          <button type="button" class="botao-icone is-perigo" data-acao="deletar" data-video-id="${video.id}">Deletar</button>
        </div>
      </article>
    `)
    .join('');

  document.querySelectorAll('[data-acao="deletar"]').forEach((botao) => {
    botao.addEventListener('click', () => {
      const videoId = Number(botao.dataset.videoId);
      deletarVideo(videoId);
    });
  });

  document.querySelectorAll('[data-acao="reprocessar"]').forEach((botao) => {
    botao.addEventListener('click', () => {
      const videoId = Number(botao.dataset.videoId);
      reprocessarVideo(videoId);
    });
  });
}

function sincronizarLinhasComHistorico(videos) {
  const mapa = new Map(videos.map((video) => [Number(video.id), video]));

  obterLinhasFormulario().forEach((linha) => {
    const videoId = Number(linha.dataset.videoId || 0);
    if (!videoId || !mapa.has(videoId)) {
      return;
    }

    const video = mapa.get(videoId);
    definirStatusLinha(linha, video.status);
  });
}

async function carregarHistorico(mostrarErro = true, forcar = false) {
  if (estado.encerrando) {
    return;
  }

  if (estado.historicoEmAndamento) {
    return;
  }

  estado.historicoEmAndamento = true;
  if (forcar) {
    alternarEstadoAtualizacao(true);
  }

  try {
    const resposta = await fetch('/api/videos');
    if (!resposta.ok) {
      throw new Error('Falha ao carregar histórico');
    }

    const dados = await resposta.json();

    const videos = dados.itens || [];
    const assinaturaAtual = gerarAssinaturaHistorico(videos);

    if (forcar || assinaturaAtual !== estado.assinaturaHistorico) {
      estado.assinaturaHistorico = assinaturaAtual;
      renderizarHistorico(videos);
      sincronizarLinhasComHistorico(videos);
    }
  } catch (erro) {
    if (mostrarErro) {
      mostrarToast('Não foi possível carregar o histórico.', 'erro');
    }
  } finally {
    estado.historicoEmAndamento = false;
    if (forcar) {
      alternarEstadoAtualizacao(false);
    }
  }
}

async function verificarStatus() {
  if (estado.encerrando) {
    return;
  }

  try {
    const resposta = await fetch('/api/status');
    if (!resposta.ok) {
      throw new Error('Falha no health check');
    }

    atualizarIndicadorApi(true);
  } catch (erro) {
    atualizarIndicadorApi(false);
  }
}

async function enviarFormulario(evento) {
  evento.preventDefault();

  if (estado.encerrando) {
    return;
  }

  if (estado.carregando) {
    return;
  }

  estado.carregando = true;
  elementos.botaoEnviar.disabled = true;
  elementos.botaoEnviar.classList.add('is-loading');

  try {
    sincronizarQuantidadeFormulario();
    const linhas = obterLinhasFormulario();
    const videos = linhas.map((linha, indice) => ({
      indice,
      linha,
      link_video: linha.querySelector('.input-video').value.trim(),
      link_referencia: linha.querySelector('.input-referencia').value.trim(),
    }));

    if (!videos.length) {
      mostrarToast('Adicione ao menos um vídeo para enviar.', 'aviso');
      return;
    }

    const linhasInvalidas = videos.filter((video) => !video.link_video || !video.link_referencia);
    if (linhasInvalidas.length > 0) {
      mostrarToast(`Preencha os campos da linha ${linhasInvalidas[0].indice + 1}.`, 'aviso');
      return;
    }

    const grupoAtivo = Number(elementos.grupoAtivo.value);
    const resposta = await fetch('/api/videos/lote', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        videos: videos.map((video) => ({
          link_video: video.link_video,
          link_shopee: video.link_referencia,
          canal_destino: grupoAtivo,
        })),
      }),
    });

    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.detail || 'Falha ao processar o lote');
    }

    const itens = dados.itens || [];
    itens.forEach((item) => {
      const linha = videos[item.indice]?.linha;
      if (!linha) {
        return;
      }

      linha.dataset.videoId = String(item.id);
      definirStatusLinha(linha, item.status || 'pendente');
    });

    mostrarToast(`${itens.length} vídeo(s) registrado(s) com sucesso.`, 'sucesso');
    await carregarHistorico();
  } catch (erro) {
    mostrarToast(erro.message || 'Erro ao enviar o formulário.', 'erro');
  } finally {
    estado.carregando = false;
    elementos.botaoEnviar.disabled = false;
    elementos.botaoEnviar.classList.remove('is-loading');
  }
}

async function reprocessarVideo(id) {
  if (estado.encerrando) {
    return;
  }

  try {
    const resposta = await fetch(`/api/videos/${id}/reprocessar`, {
      method: 'POST',
    });

    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.detail || 'Falha ao reenviar o vídeo');
    }

    mostrarToast(`Vídeo ${id} reenviado para processamento.`, 'sucesso');
    await carregarHistorico();
  } catch (erro) {
    mostrarToast(erro.message || 'Não foi possível reenviar o vídeo.', 'erro');
  }
}

async function deletarVideo(id) {
  if (estado.encerrando) {
    return;
  }

  const confirmacao = window.confirm('Deseja remover este vídeo e os arquivos locais?');
  if (!confirmacao) {
    return;
  }

  try {
    const resposta = await fetch(`/api/videos/${id}`, {
      method: 'DELETE',
    });

    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.detail || 'Falha ao deletar o vídeo');
    }

    mostrarToast('Vídeo removido com sucesso.', 'sucesso');
    await carregarHistorico();
  } catch (erro) {
    mostrarToast(erro.message || 'Não foi possível excluir o vídeo.', 'erro');
  }
}

function anexarEventosLinha(linha) {
  const campos = Array.from(linha.querySelectorAll('input'));

  campos.forEach((campo) => {
    campo.addEventListener('input', () => anotarMudancaRascunho(linha));
    campo.addEventListener('keydown', (evento) => {
      if (evento.key !== 'Enter') {
        return;
      }

      evento.preventDefault();
      if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
        adicionarLinhaSeNecessario();
      }
    });
    campo.addEventListener('blur', () => {
      if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
        adicionarLinhaSeNecessario();
      }
    });
  });

  linha.addEventListener('mouseleave', () => {
    if (linhaEUltima(linha) && linhaEstaPreenchida(linha)) {
      adicionarLinhaSeNecessario();
    }
  });
}

function inicializarEventos() {
  elementos.formulario.addEventListener('submit', enviarFormulario);
  elementos.botaoRecarregar.addEventListener('click', () => carregarHistorico(true, true));
  if (elementos.botaoEncerrarApp) {
    elementos.botaoEncerrarApp.addEventListener('click', encerrarAplicacao);
  }
  elementos.grupoAtivo.addEventListener('change', () => {
    salvarGrupoPersistido(elementos.grupoAtivo.value);
    recarregarPaginaComAnimacao();
  });
  elementos.quantidadeVideos.addEventListener('blur', sincronizarQuantidadeFormulario);
  elementos.quantidadeVideos.addEventListener('change', sincronizarQuantidadeFormulario);
  elementos.quantidadeVideos.addEventListener('keydown', (evento) => {
    if (evento.key === 'Enter') {
      evento.preventDefault();
      sincronizarQuantidadeFormulario();
    }
  });
  elementos.quantidadeVideos.addEventListener('mouseleave', sincronizarQuantidadeFormulario);
}

function inicializarEfeitosVisuais() {
  document.body.classList.add('is-inicializando');

  const atualizarPosicaoMouse = (evento) => {
    const largura = window.innerWidth || 1;
    const altura = window.innerHeight || 1;
    const x = ((evento.clientX / largura) * 100).toFixed(2);
    const y = ((evento.clientY / altura) * 100).toFixed(2);

    document.documentElement.style.setProperty('--cursor-x', `${x}%`);
    document.documentElement.style.setProperty('--cursor-y', `${y}%`);
  };

  window.addEventListener('pointermove', atualizarPosicaoMouse, { passive: true });
  window.addEventListener('pointerdown', atualizarPosicaoMouse, { passive: true });

  window.requestAnimationFrame(() => {
    document.body.classList.add('is-pronto');
    document.body.classList.remove('is-inicializando');
  });
}

function restaurarPreferenciasUsuario() {
  const grupoPersistido = obterGrupoPersistido();
  if (grupoPersistido && Array.from(elementos.grupoAtivo.options).some((opcao) => opcao.value === grupoPersistido)) {
    elementos.grupoAtivo.value = grupoPersistido;
  }
}

function prepararFormulario() {
  garantirLinhaInicial();
  obterLinhasFormulario().forEach((linha) => anexarEventosLinha(linha));
}

const observadorFormulario = new MutationObserver(() => {
  obterLinhasFormulario().forEach((linha) => {
    if (linha.dataset.anexado === '1') {
      return;
    }

    anexarEventosLinha(linha);
    linha.dataset.anexado = '1';
  });

  atualizarTitulosLinha();
  atualizarContadorFormulario();
});

function inicializarAplicacao() {
  inicializarEventos();
  restaurarPreferenciasUsuario();
  inicializarEfeitosVisuais();
  prepararFormulario();
  observadorFormulario.observe(elementos.listaFormulario, { childList: true });
  verificarStatus();
  carregarHistorico();
  window.setInterval(verificarStatus, 5000);
  estado.intervaloHistorico = window.setInterval(() => {
    carregarHistorico(false);
  }, INTERVALO_ATUALIZACAO_HISTORICO);
}

document.addEventListener('DOMContentLoaded', inicializarAplicacao);
