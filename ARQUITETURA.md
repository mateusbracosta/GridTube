# Arquitetura e operação do GridTube

## Escopo

Aplicação de preservação de vídeos. A aquisição consulta o YouTube quando há rede. O acervo, as imagens de canais já obtidas, os metadados, a busca, as playlists e a reprodução usam o servidor local. Os comandos de instalação e atualização estão no [README](README.md).

## Componentes

| Componente | Responsabilidade |
| --- | --- |
| `app.py` | API Flask no Waitress, SQLite, catálogo, canais, playlists, progresso, fila e entrega HTTP Range |
| `collector.py` | Normalização dos links, extração pelo yt-dlp, seleção de formatos, captura, metadados, imagens e FFmpeg |
| `static/` | Interface PT-BR/EN, biblioteca, catálogo paginado, páginas de canal, player e controles de faixas |
| `Dockerfile` e `compose.yaml` | Imagem Linux com Python, Node, EJS e FFmpeg, configuração do serviço e dos diretórios persistentes |

A SPA e a API usam a mesma origem. A instalação local publica `127.0.0.1:3987` por padrão. A CLI do yt-dlp roda dentro da imagem com as dependências fixadas em `requirements.txt`.

## Catálogo, canais e vídeos

O cadastro consulta as abas de Vídeos, Shorts e Transmissões em segundo plano, com metadados preferidos em português. A interface começa com 60 itens e permite ampliar a lista ou selecionar todo o resultado de uma busca. Os metadados das playlists de origem são consultados separadamente. A lista de uma playlist é obtida ao abri-la e seu vínculo com cada vídeo é cacheado nas tabelas `source_playlist` e `playlist_entry`. A seleção permanece ao trocar de playlist. A regra persistente de título do canal é aplicada ao enfileiramento e conferida na fonte antes de baixar o arquivo. O filtro usa trecho literal e ignora caixa e acentos. As preferências de cada canal sobrepõem os padrões globais. O acompanhamento opcional usa uma primeira consulta como referência e depois examina os uploads recentes em ciclos de 15 minutos.

Nome de exibição e pasta física são independentes. Cada canal remoto cacheia foto de perfil e capa em `data/branding`, além da descrição e do identificador público no SQLite. Canais locais podem ter descrição própria e ser associados a um canal do YouTube em **Editar canal**. Canais já cadastrados com link são preenchidos em segundo plano quando ainda não têm perfil. **Atualizar perfil** solicita nova consulta.

O vídeo mantém título, descrição, canal de origem, data original quando disponível, duração, capítulos e inventário local de faixas. O perfil oficial de origem é cacheado pela URL canônica do identificador do canal e independe da pasta ou do canal local escolhido. O player carrega o avatar pelo próprio servidor em `/source-branding/{video_id}/{asset}`. A atualização hidrata vídeos existentes em segundo plano e preserva rótulos e perfis no acervo. A lista mostra a data quando conhecida. O player mostra os detalhes e indica datas indisponíveis. Pesquisar idiomas do vídeo preservado também atualiza os campos devolvidos pela origem.

## Página de reprodução

O Flask serve a SPA na raiz e em `/watch/{id}`. A engrenagem sobre o vídeo reúne seleção de áudio e legendas, busca por faixas extras, avisos e tentativas. O frontend usa a API de faixas para iniciar a reprodução e sincroniza posição, título, canal, data e descrição com os metadados locais. Voltar e avançar no navegador preservam a navegação e a seção da biblioteca. A página usa o player nativo do navegador, com controles de idioma do app, atalhos e modo cinema. As sugestões vêm da biblioteca. Quando há vídeos salvos no mesmo canal, eles aparecem primeiro. Em telas estreitas, as sugestões ficam abaixo dos controles e detalhes.

## Captura de mídia e faixas

A captura por link aceita opções individuais de modo de download, limite de resolução no modo compacto, áudio e legendas. O app combina padrões globais, preferências do canal e opções do vídeo, nessa ordem. O SQLite guarda as opções individuais em `capture_overrides` e as preferências efetivas da tentativa em `prefs`. Uma nova tentativa reutiliza as opções individuais ou aceita a edição feita na fila. Registros anteriores à versão 0.3.1 começam com opções individuais vazias. Preferências anteriores à versão 0.5 herdam o modo compacto quando o campo está ausente. A captura e a consulta de faixas selecionam os formatos após o processamento do yt-dlp, que atribui identificadores distintos a faixas duplicadas na resposta do YouTube.

Na versão 0.5, o modo **Compacto** aplica o limite de resolução ao lado curto e compara tamanho dos formatos na melhor resolução, taxa de quadros e faixa dinâmica encontrada. Usa tamanho informado ou estimado, incluindo o áudio, e prefere codecs WebM quando os candidatos empatam. **Qualidade original** busca a resolução e taxa de quadros máximas com a faixa de áudio selecionada e usa a preferência do yt-dlp em caso de empate. O coletor baixa as entradas separadamente quando vídeo e áudio vêm em formatos distintos. O FFmpeg monta WebM para a combinação AV1, VP9 ou VP8 com Opus ou Vorbis, e MP4 para as demais combinações, copiando ambas as faixas. Os metadados locais registram o formato escolhido.

Entradas parciais ficam em `archive/work/inputs/<id>` para retomar em caso de reinício ou nova tentativa. A publicação bem-sucedida limpa esse diretório. O arquivo é escrito em uma pasta de trabalho, a pasta final recebe o bundle por renomeação, e o SQLite marca a mídia como pronta. A fila de legendas é criada depois dessa publicação. Uma resposta 429, faixa indisponível ou legenda inválida fica registrada na própria faixa, com nova tentativa manual disponível. As atualizações 0.2 e 0.2.1 recolocam na fila capturas que falharam na etapa antiga de legendas ou na montagem anterior do yt-dlp.

No player, **Buscar mais idiomas** consulta as faixas ainda oferecidas pelo vídeo de origem. As opções mostram idioma e, para legendas, se a faixa veio do canal ou é automática. Novos áudios são guardados como M4A ao lado da mídia principal, e novas legendas como WebVTT. Ao trocar de faixa, uma variante temporária copia a imagem do arquivo, usa o áudio M4A e o recodifica em Opus para WebM quando necessário. A variante é servida por HTTP Range. A interface mantém a posição ao trocar de faixa. O cache derivado fica em `archive/work/playback` e é limitado a cerca de 4 GiB, preservando a variante em uso mesmo que seja maior. Pode ser regenerado a partir do acervo. As legendas baixadas são selecionáveis localmente no mesmo player.

A captura registra o idioma reportado pelo YouTube e a etiqueta do áudio encontrada pelo ffprobe. Quando a seleção usa o áudio original, a etiqueta conhecida do arquivo tem prioridade. Ao escolher explicitamente uma faixa anunciada no idioma desejado, o app preserva essa escolha e indica divergências. Metadados anteriores são revisados a partir do MP4 salvo. O ajuste muda o rótulo do app, preservando o vídeo arquivado.

As legendas da própria faixa têm prioridade sobre traduções automáticas. O coletor mantém a variante `-orig` oferecida pelo yt-dlp, remove o sufixo no idioma exibido e usa a mesma sessão para consultar e baixar a faixa. Em resposta 429, a fila registra a espera pedida pela origem ou dois minutos na ausência de indicação. A interface distingue legendas automáticas originais de traduções.

Cada idioma guarda uma faixa de áudio e uma legenda. Legendas enviadas pelo canal têm prioridade sobre as automáticas da mesma variante. A disponibilidade é determinada pelo que o YouTube entrega ao coletor naquele momento.

[Faixas e dublagem do YouTube](https://support.google.com/youtube/answer/15569972?hl=pt-BR) · [Extrator de perfis do yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/_tab.py)

## Armazenamento e recuperação

O Compose monta `GRIDTUBE_ARCHIVE_PATH` em `/archive`. O valor padrão é `./archive`. `library/` e `work/` permanecem sob a mesma montagem para que a publicação mova o vídeo da área de trabalho para a biblioteca por renomeação. O banco registra pastas relativas à biblioteca, o que permite trocar o caminho no host copiando o conteúdo do acervo.

- `archive/library` é a biblioteca exportável. Cada pasta de vídeo inclui o MP4 ou WebM, eventuais M4As e VTTs, miniatura e `video.json`. Mover um vídeo para outro canal move o bundle. Playlists referenciam o mesmo vídeo.
- `archive/Playlists/<nome> [ID]/playlist.m3u8` reflete a ordem de exibição do app e referencia `library/` por caminho relativo. O ZIP de uma playlist transmite os arquivos em blocos com ZIP64 e `ZIP_STORED`. Mover ou excluir do disco um vídeo incluído aguarda o fim da transmissão para proteger o arquivo em curso.
- `data/library.sqlite` guarda canais, catálogo de origem, fila, associações e progresso. O WAL exige cópia consistente do banco. Pare o serviço antes de copiar os diretórios para backup, ou use a API de backup do SQLite para um snapshot só do banco.
- `channel_style` e `playlist_style` guardam o ícone e a cor das coleções locais. A interface usa a personalização para canais sem origem e playlists do app. As tabelas acompanham o backup e são opcionais ao restaurar candidatos de versões anteriores. A personalização preserva o caminho das pastas.
- `data/branding` guarda as imagens locais dos canais. Copiar só a mídia não leva perfis, playlists, progresso ou fila.
- `archive/work` guarda arquivos de trabalho e variantes derivadas. O app retoma jobs que ficaram em execução após reiniciar. Na publicação e na movimentação, registra o destino pretendido no SQLite antes de renomear a pasta.
- A recuperação valida a mídia e o manifesto antes de confirmar a publicação. Um destino incompleto é preservado e aparece como falha em Downloads quando a mídia original está ausente. Uma nova captura recebe um nome livre se a pasta planejada já existir. Uma falha operacional transitória do SQLite faz a fila revisar publicações pendentes e retomar os trabalhos em execução.
- O cancelamento de captura usa o estado persistente `cancelling` e um sinal de interrupção consultado pelos hooks do yt-dlp e pelo processo FFmpeg. A publicação e o cancelamento são serializados pela trava de arquivos. Depois da interrupção, a limpeza apaga os temporários específicos e retira a tarefa da fila. Se a captura substituía mídia de um registro anterior, o vídeo volta para Removidos com progresso e playlists. Na inicialização, pedidos de cancelamento pendentes são concluídos. Uma falha de permissão fica visível na tarefa para repetir a limpeza.
- Em servidores pequenos, `GRIDTUBE_PLAYBACK_CACHE_MIB` limita o cache de áudios alternativos. A poda ocorre ao gerar uma variante, mantendo a variante atual. Requisições parciais de variantes já existentes não percorrem o cache; a marca de uso de cada arquivo é atualizada no máximo uma vez por minuto.
- A preparação de áudio alternativo libera a trava geral de arquivos enquanto o FFmpeg trabalha. O vídeo de origem fica protegido contra movimentação e exclusão física até a conclusão. A mídia principal e variantes já preparadas continuam disponíveis durante a conversão.
- Remover um vídeo muda seu estado para `removed`, preservando o bundle, as playlists e o progresso. A mídia deixa de ser servida pelo GridTube e pode ser restaurada em **Removidos**. Para exclusão física, o app valida o caminho específico do bundle, move a pasta para `archive/work/deleting`, limpa os caches de reprodução associados e remove o registro do banco após apagar a pasta. Se houver falha após a movimentação, a exclusão pode ser repetida em **Removidos**.
- **Conferir arquivos do acervo** verifica os vídeos publicados sob demanda. Para um caminho ausente, procura candidatos por ID no nome da pasta e no manifesto nos canais existentes e em `Avulsos`. Um destino único atualiza o catálogo e o M3U. Se a mídia continuar ausente, o vídeo vai para **Removidos** com os mesmos vínculos. A conferência detecta mídia devolvida ao acervo e respeita remoções manuais do app. Bibliotecas montadas no Nextcloud devem expor somente `library/`; a conferência atualiza o catálogo sem mover ou excluir a mídia.
- Para restaurar o conjunto, recupere `data/`, `archive/library/`, o Compose e a imagem da mesma arquitetura. Aponte o Jellyfin para `archive/library` em modo somente leitura. O índice do Jellyfin é independente.

## API e verificação

A exclusão em lote usa `POST /api/videos/delete` com `ids` e `disk`. Canais e playlists oferecem `GET /api/{channels|playlists}/{id}/delete-preview` e `DELETE /api/{channels|playlists}/{id}` com os IDs conferidos na prévia e a escolha de disco. A prévia inclui todas as páginas e itens da fila. Se houver novos membros antes da confirmação, a exclusão exige uma nova prévia. Downloads ativos entram em cancelamento e retornam HTTP 202; a interface repete a operação após a interrupção. Requisições repetidas toleram IDs já excluídos.

Arquivos de vídeos são removidos pelo mesmo procedimento de exclusão individual. A trava de arquivos protege o lote de movimentações e publicações simultâneas. Exportações e preparação de áudio impedem a exclusão física antes de alterar o lote. Projeções M3U são atualizadas uma vez ao final, inclusive em falha parcial, e a coleção permanece até terminar a exclusão dos vídeos. Manter arquivos preserva os registros em Removidos; excluir o canal remove os vínculos ao canal sem mover os arquivos e permite restaurá-los em Avulsos. Arquivos não reconhecidos nas pastas das coleções são preservados.

Os testes offline usam acervos descartáveis. No shell POSIX, rode `docker run --rm --network none -v "$PWD/tests:/tests:ro" gridtube:0.7.12 python -m unittest discover -s /tests -v`. No PowerShell, substitua `$PWD/tests` por `${PWD}/tests`.

Para verificar seleção e exclusão na interface, execute `node tests/ui_collections.cjs` na raiz do projeto com Node.js 22 ou superior e Chromium/Chrome instalado. `GRIDTUBE_CHROME` pode indicar o executável. O roteiro abre um navegador sem janela, usa perfil temporário e dados sintéticos e testa seleção entre páginas, Shift + clique, confirmações, espera do cancelamento, criação unificada e layout móvel, sem acessar os dados da instalação.

A suíte cobre publicação e recuperação da fila, cancelamento, remoção de faixas, alterações externas no acervo, exportação, restauração com rollback, personalização de coleções, validação da API e reprodução concorrente à preparação de áudio. Para testar ARM64 em outro host, construa com `docker build --platform linux/arm64 -t gridtube:0.7.12-arm64 .` e use essa plataforma e imagem no comando dos testes. A emulação verifica compatibilidade funcional; medições de desempenho da placa exigem a Orange Pi física.

`GET /api/system/backup` transmite um catálogo JSONL versionado. A prévia importa somente tabelas conhecidas em um SQLite temporário, valida caminhos e informa os arquivos ausentes. A restauração ou a limpeza registra uma operação pendente em `data/maintenance` e o processo do Docker reinicia. Na inicialização seguinte, o catálogo é substituído ou esvaziado em uma transação. As pastas derivadas são recriadas. A exclusão da biblioteca exige confirmação distinta da limpeza de dados e afeta apenas `library/` da montagem de acervo.

Na interface, **Restaurar backup** abre a seleção do arquivo e encadeia a validação, a restauração e a consulta do resultado. Antes do commit, a restauração compara todas as tabelas persistidas com o candidato validado e executa as verificações de integridade e chaves estrangeiras do SQLite. Após o commit, uma nova conexão repete a conferência. O resultado registra o token da operação e `GET /api/system/backup/status/{token}` permite confirmar a restauração correspondente após o reinício. Um resultado anterior de outra operação é ignorado.

Perfis já cacheados no servidor são preservados ao restaurar o catálogo. Uma atualização remota sem imagem também mantém o avatar e a capa locais. A limpeza completa do app remove esse cache.

A biblioteca usa `GET /api/videos?summary=1` para carregar somente os dados dos cartões. `GET /api/videos` e a rota individual de faixas preservam os metadados completos. O catálogo dispensa comparações de texto ao listar sem filtro. Na interface, consultas de fundo são pausadas com a aba oculta e espaçadas quando a biblioteca ou o player estão sem atividade. A captura gera a miniatura com um único thread do FFmpeg.

Na fila, `progress_phase`, `percent` e `progress_estimated` descrevem a fase, sua porcentagem ou `null`, e se a medida é estimada. Transferências usam bytes do yt-dlp ou contagem de fragmentos. Na montagem, o `out_time_us` do FFmpeg é comparado à duração local das faixas ou à duração estimada da origem. Mudanças de fase e conclusões são persistidas imediatamente, com até uma gravação por segundo para valores intermediários.

O painel **Sistema** consulta `GET /api/system`, que mostra as versões de `yt-dlp` em uso, na imagem e pronta para ativar. `POST /api/system/yt-dlp` consulta a versão estável no PyPI e instala apenas os wheels da versão selecionada e dependências em uma pasta temporária sob `data/dependencies/yt-dlp`. Após um teste de importação, promove a pasta e grava um ponteiro para a próxima inicialização. A imagem continua com a versão fixada no `requirements.txt`. Se a versão preparada não carregar, o app registra o erro e usa a versão da imagem. No Compose, `POST /api/system/yt-dlp/restart` reinicia o processo via política do Docker. O registro persistente tem até 100 eventos e exibe os 50 mais recentes.

| Operação | Rotas principais |
| --- | --- |
| Estado e padrões | `GET /api/state`, `PUT /api/settings` |
| Descoberta e organização | `GET/POST /api/scans`, `POST /api/scans/playlists`, `POST /api/channels`, `PUT /api/channels/{id}`, `POST /api/channels/{id}/profile`, `POST /api/channels/{id}/queue` |
| Fila, biblioteca e posição | `POST /api/downloads`, `DELETE /api/downloads/{id}`, `GET /api/videos`, `POST /api/videos/{id}/retry`, `/move` e `/progress` |
| Playlists | `POST /api/playlists`, `PUT/DELETE /api/playlists/{id}/videos/{video_id}` |
| Faixas | `GET/POST /api/videos/{id}/tracks`, `POST /api/videos/{id}/tracks/discover` |
| Arquivos | `/branding/{id}/{asset}`, `/media/{id}/{asset}`, `/playback/{id}/{language}` |
| Exclusão | `DELETE /api/videos/{id}` com `disk` booleano, `POST /api/videos/{id}/restore` |

Antes de atualizar, rode `docker compose config --quiet`. Depois de `docker compose up -d --build --wait`, confira `docker compose ps` e abra o app. Para isolar falhas, use `docker compose logs --tail 80 untube`. Para testar as faixas, baixe um vídeo curto, acrescente uma faixa, troque no meio da reprodução e repita com internet bloqueada após a captura. Teste a indexação no Jellyfin separadamente.
