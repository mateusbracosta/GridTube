const translations = {
  library: ["Biblioteca","Library"],
  resume: ["Continuar assistindo","Continue watching"],
  inbox: ["Avulsos","Unfiled"],
  downloads: ["Downloads","Downloads"],
  progressPrepare: ["Preparando download","Preparing download"],
  progressVideo: ["Baixando vídeo","Downloading video"],
  progressAudio: ["Baixando áudio","Downloading audio"],
  progressMux: ["Montando o arquivo","Muxing the file"],
  progressThumbnail: ["Gerando miniatura","Generating thumbnail"],
  progressPublish: ["Salvando na biblioteca","Saving to library"],
  progressEstimate: ["estimado","estimated"],
  channels: ["Canais","Channels"],
  playlists: ["Playlists","Playlists"],
  collectionAppearance: ["Ícone e cor","Icon and color"],
  collectionColor: ["Cor do ícone","Icon color"],
  customizeCollection: ["Personalizar","Customize"],
  invalid_appearance: ["Escolha um ícone e uma cor válidos.","Choose a valid icon and color."],
  invalid_channel: ["Selecione um canal válido.","Select a valid channel."],
  iconFolder: ["Pasta","Folder"],
  iconList: ["Lista","List"],
  iconBook: ["Livro","Book"],
  iconFilm: ["Filmes","Movies"],
  iconMusic: ["Música","Music"],
  iconGamepad: ["Jogos","Games"],
  iconStar: ["Favoritos","Favorites"],
  iconCompass: ["Bússola","Compass"],
  iconTools: ["Ferramentas","Tools"],
  settings: ["Configurações","Settings"],
  system: ["Sistema","System"],
  exportPlaylist: ["Exportar playlist em ZIP","Export playlist as ZIP"],
  playlist_export_busy: ["Este vídeo está em uma exportação. Tente novamente quando ela terminar.","This video is part of an export. Try again when it finishes."],
  playback_busy: ["Uma faixa de áudio está sendo preparada. Tente novamente quando ela terminar.","An audio track is being prepared. Try again when it finishes."],
  playlist_media_missing: ["Um arquivo da playlist está ausente no acervo.","A playlist file is missing from the archive."],
  playlist_write_failed: ["Não foi possível salvar uma playlist no HD.","Could not save a playlist to disk."],
  publish_incomplete: ["A gravação no acervo foi interrompida. Tente baixar novamente.","Saving to the archive was interrupted. Try downloading again."],
  libraryCheck: ["Conferir arquivos do acervo","Check archive files"],
  libraryCheckHelp: ["Use depois de mover uma pasta de vídeo ou excluir um vídeo pelo Nextcloud.","Use after moving a video folder or deleting a video in Nextcloud."],
  libraryCheckEmpty: ["Nenhuma mudança detectada.","No changes detected."],
  libraryMoved: ["movidos","moved"],
  libraryMissing: ["em Removidos","moved to Removed"],
  libraryRestored: ["restaurados","restored"],
  libraryAmbiguous: ["com destinos duplicados","with duplicate destinations"],
  library_reconciled: ["Catálogo atualizado após conferência do acervo","Catalog updated after checking archive files"],
  library_check_failed: ["Não foi possível conferir o acervo. Verifique se o HD está acessível.","Could not check the archive. Make sure the drive is accessible."],
  external_media_missing: ["O arquivo sumiu do acervo. Devolva-o à pasta original ou baixe novamente.","The file is missing. Return it to its original folder or download it again."],
  external_media_returned: ["O arquivo está de volta no acervo. Use Restaurar à biblioteca.","The file is back in the archive. Use Restore to library."],
  downloadAgain: ["Baixar novamente","Download again"],
  backupTitle: ["Backup e restauração","Backup and restore"],
  backupHelp: ["Exporta o catálogo, as playlists, o progresso e as configurações. Para levar os vídeos, copie a pasta do acervo.","Exports the catalog, playlists, progress and settings. Copy the archive folder to bring the videos."],
  exportBackup: ["Exportar backup","Export backup"],
  importBackup: ["Arquivo de backup do GridTube","GridTube backup file"],
  backupRestoreHelp: ["Clique em Restaurar backup e escolha o arquivo. O GridTube valida, restaura, reinicia e verifica os dados restaurados.","Click Restore backup and choose a file. GridTube validates, restores, restarts and checks the restored data."],
  backupValidating: ["Validando o arquivo de backup…","Validating the backup file…"],
  backupRestoring: ["Backup validado. Preparando a restauração…","Backup validated. Preparing to restore…"],
  backupVerifying: ["Verificando os dados restaurados…","Checking restored data…"],
  restoreBackup: ["Restaurar backup","Restore backup"],
  restoreWarning: ["Restaurar substitui o catálogo, as playlists, o progresso e as configurações atuais. Os dados são aplicados ao reiniciar o GridTube.","Restoring replaces the current catalog, playlists, progress and settings. Data is applied when GridTube restarts."],
  backupMissingFiles: ["vídeos com arquivo ausente ficarão em Removidos","videos with missing files will go to Removed"],
  backup_invalid: ["O arquivo não é um backup válido do GridTube.","This is not a valid GridTube backup."],
  backup_preview_missing: ["Selecione o arquivo de backup novamente.","Select the backup file again."],
  backup_restored: ["Backup restaurado e verificado.","Backup restored and verified."],
  backup_restore_failed: ["A restauração não foi concluída. Consulte o registro de atividade.","Restore did not complete. Check the activity log."],
  backup_verification_failed: ["Os dados restaurados não passaram na verificação.","Restored data did not pass verification."],
  backup_result_unknown: ["Não foi possível confirmar a restauração. Consulte o registro de atividade e confira se o GridTube reiniciou.","Could not confirm the restore. Check the activity log and whether GridTube restarted."],
  resetTitle: ["Limpar dados do app","Clear app data"],
  resetHelp: ["Limpa catálogo, fila, progresso e preferências. Marque a opção abaixo para apagar também os vídeos do acervo.","Clears the catalog, queue, progress and settings. Select the option below to also delete the archived videos."],
  resetDisk: ["Apagar vídeos e arquivos auxiliares do HD","Delete videos and their sidecar files from disk"],
  resetConfirmInput: ["Digite para confirmar","Type to confirm"],
  reset_confirmation_invalid: ["Confira o texto da confirmação.","Check the confirmation text."],
  maintenance_pending: ["Uma operação aguarda o reinício do GridTube.","An operation is waiting for GridTube to restart."],
  maintenanceManual: ["Reinicie o GridTube para aplicar a operação.","Restart GridTube to apply the operation."],
  maintenance_failed: ["A operação de Sistema não terminou. Veja o registro de atividade.","The system operation did not finish. Check the activity log."],
  data_reset: ["Dados do app limpos.","App data cleared."],
  activeVersion: ["Versão em uso","Active version"],
  bundledVersion: ["Versão da imagem","Bundled version"],
  updateDependency: ["Atualizar yt-dlp","Update yt-dlp"],
  dependencyHelp: ["Consulta a versão estável no PyPI. A atualização fica no volume de dados e entra em uso ao reiniciar o GridTube.","Checks the stable release on PyPI. The update is stored in the data volume and takes effect after GridTube restarts."],
  dependencyChecking: ["Consultando e preparando a atualização…","Checking for and preparing the update…"],
  dependencyReady: ["Versão pronta para ativar","Version ready to activate"],
  dependency_staged: ["Atualização preparada","Update staged"],
  dependency_current: ["O yt-dlp está atualizado.","yt-dlp is up to date."],
  dependency_failed: ["Falha ao atualizar o yt-dlp. A versão em uso foi preservada.","Could not update yt-dlp. The active version was preserved."],
  dependency_load_failed: ["Falha ao carregar a atualização do yt-dlp. O GridTube está usando a versão da imagem.","Could not load the yt-dlp update. GridTube is using the bundled version."],
  dependency_busy: ["Já há uma atualização em andamento.","An update is already running."],
  restartDependency: ["Reiniciar e aplicar","Restart and apply"],
  restartConfirm: ["Reiniciar o GridTube agora? A reprodução será interrompida e a fila volta ao subir.","Restart GridTube now? Playback will stop and the queue will resume when it comes back."],
  restarting: ["Aguardando o GridTube voltar…","Waiting for GridTube to come back…"],
  restartPending: ["Reinicie o serviço para aplicar a atualização.","Restart the service to apply the update."],
  restart_unavailable: ["Não foi possível iniciar o reinício pelo app.","Could not start a restart from the app."],
  systemUnavailable: ["Não foi possível consultar o estado do sistema.","Could not load system status."],
  activityLog: ["Registro de atividade","Activity log"],
  noActivity: ["Nenhum evento registrado.","No events recorded yet."],
  catalog_failed: ["Falha ao consultar o catálogo","Could not check the catalog"],
  download_failed: ["Falha no download","Download failed"],
  download_completed: ["Vídeo salvo","Video saved"],
  removed: ["Removidos","Removed"],
  removeVideo: ["Excluir vídeo","Remove video"],
  deleteChannel: ["Excluir canal e vídeos","Delete channel and videos"],
  deletePlaylist: ["Excluir playlist e vídeos","Delete playlist and videos"],
  selectVideo: ["Selecionar vídeo","Select video"],
  deselectVideo: ["Desmarcar vídeo","Deselect video"],
  moreOptions: ["Mais opções","More options"],
  selectPage: ["Selecionar esta página","Select this page"],
  deleteSelected: ["Excluir selecionados","Delete selected"],
  selectedVideos: ["vídeos selecionados","videos selected"],
  selectedVideoOne: ["vídeo selecionado","video selected"],
  collectionDeleteHelp: ["A coleção e todos os seus vídeos serão removidos da biblioteca, incluindo itens de outras páginas e da fila. Você escolhe abaixo se os arquivos também serão apagados do disco.","The collection and all its videos will be removed from the library, including other pages and queued items. Choose below whether to also erase the files from disk."],
  sharedDeleteHelp: ["A exclusão afeta os vídeos na biblioteca inteira, mesmo quando aparecem em outras playlists. Playlists não possuem cópias separadas.","Deletion affects the videos throughout the library, including other playlists. Playlists do not hold separate copies."],
  sharedVideos: ["Vídeos presentes em outras playlists","Videos present in other playlists"],
  keepCollectionFiles: ["Excluir coleção e manter arquivos","Delete collection and keep files"],
  deleteCollectionFiles: ["Excluir coleção e apagar arquivos","Delete collection and erase files"],
  collectionKeepHelp: ["Mantendo os arquivos, os vídeos ficam em Removidos. Ao excluir um canal, os vídeos restaurados ficam em Avulsos. A coleção excluída não é restaurada junto.","When keeping files, videos stay in Removed. After deleting a channel, restored videos appear in Unfiled. The deleted collection is not restored with them."],
  deletingVideos: ["Excluindo os itens…","Deleting items…"],
  cancellingForDelete: ["Interrompendo os downloads selecionados antes de excluir…","Stopping selected downloads before deleting…"],
  collection_changed: ["O conteúdo da coleção mudou. Feche esta janela e confira a exclusão novamente.","The collection contents changed. Close this window and review deletion again."],
  collection_busy: ["Um vídeo está sendo publicado ou movido. Aguarde a conclusão e tente novamente.","A video is being saved or moved. Wait for it to finish and try again."],
  keepMedia: ["Remover da biblioteca","Remove from library"],
  deleteMedia: ["Excluir também do disco","Also delete from disk"],
  removeVideoNote: ["Remover da biblioteca mantém a pasta e permite restaurar o vídeo em Removidos. Excluir do disco apaga o vídeo e seus arquivos auxiliares.","Removing from the library keeps the folder and lets you restore the video from Removed. Deleting from disk erases the video and its sidecar files."],
  deleteMediaNote: ["Esta ação apaga o vídeo e seus arquivos auxiliares do disco.","This deletes the video and its sidecar files from disk."],
  restoreVideo: ["Restaurar à biblioteca","Restore to library"],
  delete_disk_failed: ["A exclusão no disco não terminou. Confira as permissões da pasta e tente novamente em Removidos.","Disk deletion did not finish. Check folder permissions and try again from Removed."],
  restore_media_missing: ["O arquivo do vídeo não está na pasta original.","The video file is missing from its original folder."],
  restore_removed_first: ["Este vídeo está em Removidos. Restaure-o por lá.","This video is in Removed. Restore it from there."],
  addChannel: ["Adicionar canal","Add channel"],
  localChannel: ["Criar canal local","Create local channel"],
  addLink: ["Baixar por link","Download link"],
  addPlaylist: ["Nova playlist","New playlist"],
  createChannelOption: ["+ Criar novo canal…","+ Create a new channel…"],
  createPlaylistOption: ["+ Criar nova playlist…","+ Create a new playlist…"],
  choosePlaylist: ["Escolha uma playlist","Choose a playlist"],
  search: ["Buscar na biblioteca","Search your library"],
  title: ["Seu acervo de vídeos","Your video archive"],
  intro: ["Guarde vídeos para assistir pela rede local, mesmo sem internet.","Save videos to watch on your local network, even without internet access."],
  recent: ["Adicionados recentemente","Recently added"],
  nothing: ["Ainda não há vídeos nesta seção.","There are no videos in this section yet."],
  noJobs: ["A fila está vazia.","The queue is empty."],
  url: ["Link do YouTube","YouTube link"],
  channelUrl: ["Link do canal no YouTube","YouTube channel link"],
  startScan: ["Ver catálogo","Load catalog"],
  name: ["Nome","Name"],
  browse: ["Selecionar vídeos","Select videos"],
  scanSearch: ["Buscar no catálogo do canal","Search this channel's catalog"],
  all: ["Todos","All"],
  videos: ["Vídeos","Videos"],
  shorts: ["Shorts","Shorts"],
  scanning: ["Buscando catálogo… Já é possível selecionar resultados.","Loading the catalog… Select results as they appear."],
  emptyCatalog: ["Nenhum resultado.","No results."],
  selection: ["selecionados","selected"],
  saved: ["Já na biblioteca ou fila","In library or queue"],
  refresh: ["Atualizar","Refresh"],
  queued: ["Adicionados à fila","Added to queue"],
  save: ["Salvar","Save"],
  saveChannel: ["Salvar canal e baixar seleção","Save channel and download selection"],
  queueSelection: ["Baixar selecionados","Download selection"],
  defaults: ["Preferências globais","Global defaults"],
  overrides: ["Preferências do canal","Channel preferences"],
  inherit: ["Usar padrão global","Use global default"],
  download_mode: ["Modo de download","Download mode"],
  compact: ["Compacto","Compact"],
  originalQuality: ["Qualidade original","Original quality"],
  quality: ["Resolução máxima","Maximum resolution"],
  resolutionHelp: ["O limite de resolução vale para os dois modos. Melhor disponível remove esse limite.","The resolution limit applies to both modes. Best available removes this limit."],
  best: ["Melhor disponível (sem limite)","Best available (no limit)"],
  audio: ["Áudio preferido","Preferred audio"],
  original: ["Original","Original"],
  subtitles: ["Legendas","Subtitles"],
  none: ["Nenhuma","None"],
  both: ["Português e inglês","Portuguese and English"],
  autoSub: ["Legendas automáticas","Automatic subtitles"],
  yes: ["Permitir","Allow"],
  no: ["Desativar","Disable"],
  include: ["Permitir Shorts","Allow Shorts"],
  exclude: ["Não baixar Shorts","Do not download Shorts"],
  only: ["Somente Shorts","Shorts only"],
  auto: ["Baixar novos uploads automaticamente","Automatically download new uploads"],
  autoNote: ["A primeira consulta automática define o ponto de partida.","The first automatic check establishes a starting point."],
  configNote: ["As preferências do canal substituem os padrões globais. As regras de Shorts e Lives também valem para a seleção manual.","Channel preferences override global defaults. Shorts and Live stream rules also apply to manual selections."],
  channel: ["Canal","Channel"],
  playlist: ["Playlist","Playlist"],
  organize: ["Organizar vídeo","Organize video"],
  openOnYouTube: ["Abrir no YouTube","Open on YouTube"],
  move: ["Mover para canal","Move to channel"],
  unfiled: ["Mover para Avulsos","Move to Unfiled"],
  addTo: ["Adicionar à playlist","Add to playlist"],
  createMove: ["Criar e mover","Create and move"],
  newChannelName: ["Nome do novo canal","New channel name"],
  newPlaylistName: ["Nome da nova playlist","New playlist name"],
  removeFrom: ["Remover desta playlist","Remove from this playlist"],
  close: ["Fechar","Close"],
  prev: ["Anterior","Previous"],
  next: ["Próxima","Next"],
  menu: ["Menu","Menu"],
  play: ["Reproduzir","Play"],
  retry: ["Tentar novamente","Retry"],
  queuedState: ["Na fila","Queued"],
  cancelDownload: ["Cancelar","Cancel"],
  removeDownload: ["Remover tentativa","Remove attempt"],
  cancelling: ["Cancelando…","Cancelling…"],
  download_cancelled: ["Download cancelado","Download cancelled"],
  download_finished: ["Este vídeo já foi publicado. Use Organizar vídeo para removê-lo.","This video has already been saved. Use Organize video to remove it."],
  cancel_cleanup_failed: ["Não foi possível limpar os temporários. Confira as permissões e remova a tentativa novamente.","Could not clear temporary files. Check permissions and remove the attempt again."],
  youtubeVideo: ["Vídeo do YouTube","YouTube video"],
  running: ["Baixando / processando","Downloading / processing"],
  failed: ["Falhou","Failed"],
  audioFallback: ["Áudio preferido indisponível. Foi guardada a faixa disponível.","Preferred audio unavailable. The available track was saved."],
  subsMissing: ["Uma ou mais legendas pedidas ficaram indisponíveis.","One or more requested subtitles were unavailable."],
  details: ["Descrição","Description"],
  chapters: ["Capítulos","Chapters"],
  done: ["Salvo","Saved"],
  error: ["Não foi possível concluir.","Could not complete the action."],
  invalid_url: ["Informe um link válido do YouTube.","Enter a valid YouTube link."],
  invalid_name: ["Digite um nome de até 100 caracteres.","Enter a name up to 100 characters."],
  already_exists: ["Este canal ou item já existe.","This channel or item already exists."],
  invalid_selection: ["A seleção mudou. Atualize o catálogo.","The selection changed. Refresh the catalog."],
  interrupted: ["A consulta foi interrompida. Atualize o catálogo.","The scan was interrupted. Refresh the catalog."],
  empty_catalog: ["O canal não apresentou as abas de vídeos ou Shorts.","No Videos or Shorts tab was available for this channel."],
  no_audio_at_quality: ["Não há formato com áudio dentro da qualidade escolhida.","No format with audio meets the selected quality."],
  live_unsupported: ["Tente novamente após o fim da transmissão.","Try again after the livestream ends."],
  language: ["Idioma","Language"],
  edit: ["Editar canal","Edit channel"],
  publication: ["Publicado em","Published on"],
  noDate: ["Data de publicação indisponível","Publication date unavailable"],
  refreshProfile: ["Atualizar perfil","Refresh profile"],
  channelDescription: ["Descrição do canal","Channel description"],
  catalogFilter: ["Tipo de vídeo","Video type"],
  watchAudio: ["Faixa de áudio","Audio track"],
  watchSubtitles: ["Legenda em exibição","Subtitle track"],
  originalSaved: ["Áudio do arquivo","Audio in saved video"],
  loadTracks: ["Buscar mais idiomas","Find more languages"],
  downloadingTracks: ["Consultando idiomas disponíveis…","Checking available languages…"],
  additionalAudio: ["Baixar áudio","Download audio"],
  additionalSubtitle: ["Baixar legenda","Download subtitles"],
  manual: ["enviada pelo canal","uploaded by channel"],
  generated: ["automática","automatic"],
  translated: ["tradução automática","automatically translated"],
  retryAfter: ["Nova tentativa após","Retry after"],
  trackEmpty: ["Nenhuma faixa adicional disponível.","No additional tracks available."],
  track_rate_limited: ["O YouTube limitou temporariamente esta faixa (429). Tente novamente mais tarde.","YouTube temporarily rate-limited this track (429). Try again later."],
  track_unavailable: ["Esta faixa está indisponível.","This track is unavailable."],
  track_invalid: ["A origem não enviou uma legenda legível.","The source did not return a readable subtitle."],
  track_failed: ["Não foi possível obter a faixa.","Could not retrieve the track."],
  deleteTrack: ["Apagar faixa do disco","Delete track from disk"],
  deleteTrackAttempt: ["Apagar tentativa","Delete attempt"],
  track_active: ["Esta faixa está sendo baixada. Aguarde a conclusão.","This track is downloading. Wait for it to finish."],
  track_delete_failed: ["Não foi possível apagar a faixa do disco.","Could not delete the track from disk."],
  playbackError: ["Não foi possível abrir esta faixa. Voltando ao áudio do arquivo.","Could not play this track. Returning to the saved audio."],
  videoPlaybackError: ["O navegador não conseguiu reproduzir o arquivo salvo. Tente outro player compatível com o formato.","The browser could not play the saved file. Try another player that supports its format."],
  invalid_description: ["Use até 5.000 caracteres.","Use up to 5,000 characters."],
  back: ["Voltar","Back"],
  theater: ["Modo cinema","Theater mode"],
  opening: ["Abrindo vídeo…","Opening video…"],
  watchUnavailable: ["Este vídeo não está disponível na biblioteca.","This video is unavailable in the library."],
  upNext: ["A seguir","Up next"],
  moreTracks: ["Mais faixas","More tracks"],
  showDescription: ["Ver descrição completa","Show full description"],
  hideDescription: ["Recolher descrição","Collapse description"],
  videoOptions: ["Opções para este vídeo","Options for this video"],
  videoOptionsNote: ["Estas escolhas valem somente para este download.","These choices apply only to this download."],
  useChannel: ["Usar padrão do canal","Use channel default"],
  editRetry: ["Editar opções e tentar novamente","Edit options and retry"],
  playerSettings: ["Áudio e legendas","Audio and subtitles"],
  sourceConflict: ["Idioma no arquivo","Language in file"],
  sourceReported: ["YouTube informa","YouTube reports"],
  languageReported: ["Idioma informado pelo YouTube.","Language reported by YouTube."],
  subtitleDownload: ["Legenda","Subtitle"],
  trackAttention: ["Faixas com erro","Tracks with errors"],
  streams: ["Lives","Live streams"],
  contentTabs: ["Tipo de conteúdo","Content type"],
  newVideo: ["Novo","New"],
  lives: ["Lives","Live streams"],
  allowCapture: ["Permitir","Allow"],
  disableCapture: ["Não baixar","Do not download"],
  livesHelp: ["Shorts e Lives controlam novos downloads por seleção, link e acompanhamento automático. Desativar não exclui arquivos já baixados.","Shorts and Live streams control new downloads from selections, links and channel monitoring. Disabling keeps existing files."],
  shorts_disabled: ["O download de Shorts está desativado nas preferências globais ou deste canal.","Shorts downloads are disabled in global or channel preferences."],
  lives_disabled: ["O download de lives está desativado nas preferências globais ou deste canal.","Live stream downloads are disabled in global or channel preferences."],
  shorts_only: ["As preferências atuais permitem baixar somente Shorts.","Current preferences allow downloading Shorts only."],
  blockedDownloads: ["Bloqueados pelas preferências de download","Blocked by download preferences"],
  maxDuration: ["Duração máxima para download (minutos)","Maximum download duration (minutes)"],
  autoDeleteDays: ["Excluir automaticamente do disco após (dias)","Automatically delete from disk after (days)"],
  newBadgeDays: ["Duração do selo Novo (dias)","New badge duration (days)"],
  noLimit: ["Sem limite","No limit"],
  never: ["Nunca","Never"],
  untilOpened: ["Até abrir o vídeo","Until the video is opened"],
  durationHelp: ["Vazio ou 0: sem limite. Vale para seleção manual, links e acompanhamento automático.","Empty or 0: no limit. Applies to manual selections, links and channel monitoring."],
  autoDeleteHelp: ["Vazio ou 0: nunca. Um valor em dias apaga os vídeos e arquivos auxiliares do disco após o download. O padrão preserva tudo.","Empty or 0: never. A number of days deletes videos and sidecars from disk after downloading. The default keeps everything."],
  newBadgeHelp: ["Vazio ou 0: só desaparece ao abrir. Com um prazo, desaparece ao abrir ou ao completar os dias, o que vier primeiro.","Empty or 0: disappears only when opened. With a time limit, disappears when opened or when that many days pass, whichever comes first."],
  duration_limit_exceeded: ["O vídeo ultrapassa a duração máxima permitida para download.","The video exceeds the maximum allowed download duration."],
  duration_unavailable: ["Não foi possível confirmar a duração para aplicar o limite. Tente novamente.","The duration could not be confirmed to apply the limit. Try again."],
  retention_deleted: ["Vídeos excluídos pelo prazo automático","Videos deleted by automatic retention"],
  retention_failed: ["Não foi possível excluir um vídeo pelo prazo automático","Automatic deletion could not remove a video"],
  watched: ["Assistidos","Watched"],
  ignored: ["Ignorados","Ignored"],
  ignoreVideo: ["Ignorar vídeo","Ignore video"],
  unignoreVideo: ["Voltar à biblioteca","Return to library"],
  invalid_ignored: ["Opção de ignorar inválida.","Invalid ignored option."],
  markWatched: ["Marcar como assistido","Mark as watched"],
  markUnwatched: ["Marcar como não assistido","Mark as unwatched"],
  hideWatched: ["Ocultar assistidos","Hide watched videos"],
  showWatched: ["Mostrar assistidos","Show watched videos"],
  invalid_watched: ["Opção de assistido inválida.","Invalid watched option."],
  filterNew: ["Novos","New"],
  filterToday: ["Hoje","Today"],
  filterWeek: ["Esta semana","This week"],
  filterUnwatched: ["Não assistidos","Unwatched"],
  filterProgress: ["Em andamento","In progress"],
  combineFilters: ["Os filtros selecionados são combinados para refinar os resultados.","Selected filters are combined to narrow the results."],
  sortOrder: ["Ordem dos vídeos","Video order"],
  newest: ["Mais recentes primeiro","Newest first"],
  oldest: ["Mais antigos primeiro","Oldest first"],
  invalid_sort: ["Ordem inválida.","Invalid sort order."],
  invalid_filter: ["Filtro inválido.","Invalid filter."],
  interface: ["Interface","Interface"],
  hideShorts: ["Nunca exibir Shorts","Never show Shorts"],
  hideLives: ["Nunca exibir lives","Never show live streams"],
  visibilityHelp: ["Salvo neste navegador. Oculta conteúdos e abas na biblioteca, canais, playlists e sugestões. Não exclui arquivos nem cancela downloads; a fila continua visível para gerenciá-los.","Saved in this browser. Hides content and tabs in the library, channels, playlists and suggestions. Files and downloads are unchanged; the queue remains visible for management."],
  invalid_content_kind: ["Tipo de conteúdo inválido.","Invalid content type."],
  playlistFilter: ["Filtrar por playlist","Filter by playlist"],
  allPlaylists: ["Catálogo do canal","Channel catalog"],
  loadingPlaylists: ["Buscando playlists…","Loading playlists…"],
  playlistError: ["Falha ao consultar playlists.","Could not load playlists."],
  loadMore: ["Carregar mais","Load more"],
  loadAll: ["Carregar todos","Load all"],
  clearSelection: ["Limpar seleção","Clear selection"],
  selectResults: ["Selecionar todos os resultados","Select all results"],
  ofCount: ["de","of"],
  titleFilter: ["Título deve conter","Title must contain"],
  titleExample: ["Ex.: Sobrevivendo","E.g. Survival"],
  title_filter_mismatch: ["O título não contém o texto exigido pelo canal.","The title does not contain the channel's required text."],
  invalid_title_filter: ["Use até 120 caracteres.","Use up to 120 characters."]
};

const paths = {
  eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff:'<path d="m3 3 18 18M10 5a12 12 0 0 1 12 7 17 17 0 0 1-3 4M6 6a17 17 0 0 0-4 6s4 7 10 7a14 14 0 0 0 5-1M10 10a3 3 0 0 0 4 4"/>',
  play:'<path d="m8 5 12 7-12 7z" fill="currentColor" stroke="none"/>',
  library:'<rect x="3" y="4" width="7" height="7" rx="1"/><rect x="14" y="4" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>',
  inbox:'<path d="M3 13h5l2 3h4l2-3h5M3 13l3-7h12l3 7v6H3z"/>',
  download:'<path d="M12 3v13m-4-4 4 4 4-4M4 16v4h16v-4"/>',
  folder:'<path d="M3 6h7l2 2h9v11H3z"/>', list:'<path d="M4 6h16M4 12h16M4 18h10"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  link:'<path d="m10 14 4-4m-6 6-1 1a3 3 0 0 1-4-4l4-4a3 3 0 0 1 4 0m2 6a3 3 0 0 0 4 0l4-4a3 3 0 0 0-4-4l-1 1"/>',
  settings:'<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="#222222"/><circle cx="15" cy="12" r="2" fill="#222222"/><circle cx="10" cy="18" r="2" fill="#222222"/>',
  more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  back:'<path d="m11 5-7 7 7 7M4 12h16"/>',
  theater:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M6 17h12"/>',
  gear:'<path d="M10 3h4l.6 2.5 1.5.9 2.5-.7 2 3.4-1.8 1.8v1.8l1.8 1.8-2 3.4-2.5-.7-1.5.9L14 21h-4l-.6-2.5-1.5-.9-2.5.7-2-3.4L5.2 13v-1.8L3.4 9.4l2-3.4 2.5.7 1.5-.9z"/><circle cx="12" cy="12" r="3"/>',
  trash:'<path d="M4 7h16m-14 0 1 14h10l1-14M9 7V3h6v4m-5 4v6m4-6v6"/>',
  book:'<path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1v15"/>',
  film:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 3v18M17 3v18M3 8h4M3 16h4M17 8h4M17 16h4"/>',
  music:'<path d="M9 18V5l11-2v13M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="3"/><ellipse cx="17" cy="16" rx="3" ry="3"/>',
  gamepad:'<path d="M7 7h10c3 0 5 11 3 12-2 1-4-4-5-4H9c-1 0-3 5-5 4C2 18 4 7 7 7zM8 9v5M5.5 11.5h5"/><circle cx="16" cy="11" r=".8"/><circle cx="18" cy="13" r=".8"/>',
  star:'<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9z"/>',
  compass:'<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6z"/>',
  tools:'<path d="M14 5a5 5 0 0 0-6 6L3 16a3 3 0 0 0 5 5l5-5a5 5 0 0 0 6-6l-4 4-4-4z"/>'
};
const collectionIcons = [["folder","iconFolder"],["list","iconList"],["book","iconBook"],
  ["film","iconFilm"],["music","iconMusic"],["gamepad","iconGamepad"],
  ["star","iconStar"],["compass","iconCompass"],["tools","iconTools"]];
const get = id => document.getElementById(id);
const app = get("app"), modal = get("modal"), notice = get("notice");
const appName = "GridTube";
const browserLanguages = navigator.languages?.length ? navigator.languages : [navigator.language];
const preferredLanguage = browserLanguages.find(value=>/^(pt|en)(-|$)/i.test(value)) || "pt-BR";
let locale = (localStorage.getItem("gridtube.locale") ?? localStorage.getItem("untube.locale") ?? preferredLanguage).toLowerCase().startsWith("en") ? "en" : "pt-BR";
let state = {channels:[],playlists:[],counts:{},settings:{}};
let scope = "", search = "", page = 1, lastRequest = 0, prior = "", displayed = [];
let contentKind = "videos";
let hideShorts = localStorage.getItem("gridtube.hideShorts")==="true";
let hideLives = localStorage.getItem("gridtube.hideLives")==="true";
let libraryFilters = new Set();
let sortOrder = localStorage.getItem("gridtube.sort")==="oldest"?"oldest":"newest";
const selectedVideos = new Map();
let selectionContext = "", lastSelectedVideo = null;
let catalog = null, flashTimer;
let watchCleanup = null, watchVideo = null, routeRequest = 0;
let stateRequest = 0, lastRefresh = -Infinity, backgroundRefreshPending = false;
const profileRequestTimes = new Map();
let pendingLocalizedProfile = null;
history.scrollRestoration = "manual";
const t = key => translations[key]?.[Number(locale === "en")] || key;
const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ch]);
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
const asset = (id,name) => `/media/${encodeURIComponent(id)}/${encodeURIComponent(name)}`;
const youtubeLink = video => `<a class="youtube-source" target="_blank" rel="noopener noreferrer"
  href="https://www.youtube.com/watch?v=${encodeURIComponent(video.id)}">${icon("link")} ${t("openOnYouTube")}</a>`;
const channelOf = id => state.channels.find(c => c.id === id);
const duration = seconds => seconds > 0
  ? [Math.floor(seconds/3600), Math.floor(seconds/60)%60, Math.floor(seconds)%60].slice(seconds<3600?1:0).map((n,i)=>i?String(n).padStart(2,"0"):n).join(":") : "";
const btn = (action, text, glyph, css="", value="") => {
  if (["removeVideo","deleteChannel","deletePlaylist","deleteSelected","unplaylist"].includes(action)) {
    css += " danger";
    glyph ||= "trash";
  }
  return `<button type="button" data-action="${action}" data-value="${esc(value)}" class="${css}" aria-label="${esc(text)}" title="${esc(text)}">${glyph?icon(glyph):""}${css.includes("icon-only")?"":` <span>${esc(text)}</span>`}</button>`;
};

async function api(path, method="GET", data) {
  const payload = data instanceof FormData ? {body:data} : data===undefined ? {} :
    {headers:{"Content-Type":"application/json"},body:JSON.stringify(data)};
  const regionalLanguage = browserLanguages.find(value=>/^[a-z]{2,3}(?:-[a-z]{4})?-[a-z]{2}$/i.test(value));
  const region = regionalLanguage?.split("-").at(-1).toUpperCase() || "US";
  const metadataLocale = locale==="pt-BR" ? "pt-BR" : `en-${region}`;
  const headers = {...payload.headers,"X-GridTube-Locale":metadataLocale,"Accept-Language":metadataLocale};
  const res = await fetch(`/api${path}`, {method,cache:"no-store",...payload,headers});
  if (!res.ok) throw new Error((await res.json().catch(()=>({}))).error || "error");
  return res.json();
}
function flash(text) {
  notice.textContent = text;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => { notice.textContent = ""; }, 3700);
}
function debounced(fn) {
  let timer;
  return () => { clearTimeout(timer); timer = setTimeout(fn,250); };
}
function shell() {
  disposeWatch();
  document.documentElement.lang = locale;
  const mark = `<img class="mark" src="/static/icon.svg" alt="">`;
  app.innerHTML = `<div class="shell"><aside class="sidebar"><a class="brand" href="/" data-action="home" aria-label="${t("library")}" title="${t("library")}">${mark}<span class="brand-name">${appName}</span></a>
    <nav id="navigation"></nav><div class="nav-add">${btn("addChannel",t("addChannel"),"plus")}${btn("settings",t("settings"),"settings","flat")}</div></aside>
    <div class="workspace"><header class="top">${btn("menu",t("menu"),"list","mobile-nav icon-only")}
    <a class="mobile-brand" href="/" data-action="home" aria-label="${t("library")}" title="${t("library")}">${mark}</a>
    <input id="search" class="search" type="search" aria-label="${t("search")}" placeholder="${t("search")}" value="${esc(search)}">
    <button class="accent" data-action="link" aria-label="${t("addLink")}" title="${t("addLink")}">${icon("link")} <span class="text-extra">${t("addLink")}</span></button>
    <select id="language" aria-label="${t("language")}"><option value="pt-BR">PT-BR</option><option value="en">EN</option></select>
    </header><main id="library" aria-live="polite"></main></div></div>`;
  get("language").value = locale;
  get("language").onchange = event => {
    locale = event.target.value;
    localStorage.setItem("gridtube.locale", locale);
    notice.textContent = "";
    shell();
    refresh().catch(error=>flash(t(error.message)));
  };
  get("search").oninput = debounced(() => {
    const query = get("search").value;
    if (watchPath()) showLibrary("",query);
    else { search=query;page=1;rememberLibrary();loadLibrary(); }
  });
  showLocation(false,!watchPath());
}
function watchPath() {
  return /^\/watch\/([A-Za-z0-9_-]{11})\/?$/.exec(location.pathname)?.[1];
}
function libraryView() {
  return {scope,search,page,contentKind,filters:[...libraryFilters],scroll:window.scrollY};
}
function rememberLibrary() {
  history.replaceState({library:libraryView()},"","/");
}
function disposeWatch() {
  if (watchCleanup) watchCleanup();
  watchCleanup = null;
  watchVideo = null;
  app.querySelector(".shell")?.classList.remove("cinema");
}
function showLibrary(target, query="") {
  scope=target; search=query; page=1; contentKind="videos";
  libraryFilters.clear();
  get("search").value=search;
  app.querySelector(".shell").classList.remove("menu");
  if (watchPath()) history.pushState({library:libraryView()},"","/");
  else rememberLibrary();
  showLocation();
}
function openWatch(id) {
  if (watchPath()===id) return;
  if (!watchPath()) rememberLibrary();
  history.pushState({watchFromApp:true},"",`/watch/${encodeURIComponent(id)}`);
  showLocation(true);
}
async function showLocation(autoplay=false, restore=false) {
  closeSelectionMenu();
  const request = ++routeRequest;
  const id = watchPath();
  const main = get("library");
  if (modal.open) modal.close();
  disposeWatch();
  prior = "";
  if (!id && main.classList.contains("watch-main")) main.replaceChildren();
  main.classList.toggle("watch-main",Boolean(id));
  main.setAttribute("aria-live",id?"off":"polite");
  if (!id) {
    const previous = restore && history.state?.library;
    if (previous) {
      ({scope,search,page}=previous);
      contentKind=["videos","shorts","streams"].includes(previous.contentKind)?previous.contentKind:"videos";
      libraryFilters=new Set((previous.filters||[]).filter(value=>["new","today","week","unwatched","progress"].includes(value)));
      get("search").value=search;
    }
    document.title=appName;
    nav();
    await loadLibrary();
    if (!watchPath() && request===routeRequest) window.scrollTo(0,previous?.scroll || 0);
    return;
  }
  ++lastRequest;
  app.querySelector(".shell").classList.remove("menu");
  nav();
  main.innerHTML = `<div class="watch-topline">${btn("back",t("back"),"back","flat")}</div><p class="watch-loading note" role="status">${t("opening")}</p>`;
  window.scrollTo(0,0);
  try {
    const result = await api(`/videos/${id}/tracks`);
    if (request === routeRequest) watch(result.video,result.jobs,autoplay);
  } catch (error) {
    if (request === routeRequest) {
      disposeWatch();
      const failure = t(error.message==="error"?"watchUnavailable":error.message);
      main.innerHTML = `<div class="watch-topline">${btn("back",t("back"),"back","flat")}</div><p class="watch-loading note" role="status">${esc(failure)}</p>`;
    }
  }
}

async function loadNext(item, player) {
  const query = new URLSearchParams({summary:"1"});
  applyVisibility(query);
  const {videos} = await api(`/videos?${query}`);
  const available = videos.filter(video=>video.id!==item.id);
  const preferred = item.channel_id ? available.filter(video=>video.channel_id===item.channel_id) : [];
  const next = [...preferred,...available.filter(video=>!preferred.includes(video))].slice(0,7);
  if (get("player")!==player) return;
  const rail = get("watch-next");
  if (!next.length) { rail.replaceChildren();rail.hidden=true;get("watch-layout").classList.remove("has-next");return; }
  rail.innerHTML = `<h2>${t("upNext")}</h2>`+next.map(v=>`<a class="next-card" href="/watch/${v.id}" data-action="watch" data-value="${v.id}">
    <span class="next-poster">${v.thumbnail?`<img src="${asset(v.id,v.thumbnail)}" alt="" loading="lazy">`:icon("play")}
    ${v.duration?`<span class="timed">${duration(v.duration)}</span>`:""}</span>
    <span class="next-text"><strong>${esc(v.title)}</strong><small>${esc(originName(v))}</small>${newBadge(v)}</span>
  </a>`).join("");
  rail.hidden = false;
  get("watch-layout").classList.add("has-next");
}

function branding(channel, filename) {
  return `/branding/${encodeURIComponent(channel.id)}/${encodeURIComponent(filename)}`;
}
function channelAvatar(channel, size="") {
  if (!channel.source) return collectionMark(channel,"folder",size);
  return channel.profile?.avatar
    ? `<img class="channel-avatar ${size}" src="${branding(channel,channel.profile.avatar)}" alt="">`
    : `<span class="channel-avatar placeholder ${size}">${icon("folder")}</span>`;
}
function collectionMark(collection, fallback="list", size="") {
  const style = collection.appearance || {};
  const glyph = collectionIcons.some(([name])=>name===style.icon) ? style.icon : fallback;
  const color = /^#[a-f\d]{6}$/i.test(style.color) ? style.color : "#bebebe";
  return `<span class="channel-avatar placeholder collection-mark ${size}" style="--collection-color:${color}">${icon(glyph)}</span>`;
}
function channelPage(channel, actions) {
  const profile = channel.profile || {};
  const description = channel.custom_description || profile.description;
  const handle = profile.handle?.startsWith("@") ? profile.handle : "";
  return `<section class="channel-page">
    <div class="channel-cover">${profile.banner ? `<img src="${branding(channel,profile.banner)}" alt="">` : ""}</div>
    <div class="channel-identity">${channelAvatar(channel,"large")}
      <div><h1>${esc(channel.name)}</h1>${handle?`<p class="muted">${esc(handle)}</p>`:""}
      ${description?`<details class="channel-description"><summary>${esc(description.split("\n")[0])}</summary><p>${esc(description)}</p></details>`:""}
      <div class="channel-actions">${actions}</div></div>
    </div>
    </section>`;
}
function originName(video) {
  return video.source_profile?.name || video.source_channel || channelOf(video.channel_id)?.name || t("inbox");
}
function published(raw) {
  if (typeof raw !== "string" || !/^\d{8}$/.test(raw)) return "";
  const date = `${raw.slice(0,4)}-${raw.slice(4,6)}-${raw.slice(6)}`;
  const time = new Date(`${date}T00:00:00Z`);
  if (!Number.isFinite(time.valueOf())) return "";
  return `<time datetime="${date}">${new Intl.DateTimeFormat(locale,{dateStyle:"medium",timeZone:"UTC"}).format(time)}</time>`;
}
function nav() {
  const item = (key,title,glyph) => btn("scope",title,glyph,!watchPath()&&scope===key?"active":"",key);
  const pending = (state.counts.queued||0)+(state.counts.running||0)+(state.counts.cancelling||0);
  const html = `<div class="nav">${item("",t("library"),"library")}${item("ignored",t("ignored"),"eyeOff")}${item("watched",t("watched"),"eye")}${item("inbox",t("inbox"),"inbox")}
    ${item("downloads",t("downloads")+(pending?` · ${pending}`:""),"download")}${state.counts.removed||scope==="removed"?item("removed",t("removed"),"inbox"):""}</div>
    <div class="nav-head">${t("channels")}${btn("localChannel",t("localChannel"),"plus","flat icon-only")}</div>
    <div class="nav">${state.channels.map(c=>`<button type="button" class="${!watchPath()&&scope===`channel:${c.id}`?"active":""}" data-action="scope" data-value="channel:${c.id}" title="${esc(c.name)}" aria-label="${esc(c.name)}">${channelAvatar(c)}<span>${esc(c.name)}</span></button>`).join("")}</div>
    <div class="nav-head">${t("playlists")}${btn("addPlaylist",t("addPlaylist"),"plus","flat icon-only")}</div>
    <div class="nav">${state.playlists.map(p=>`<button type="button" class="${!watchPath()&&scope===`playlist:${p.id}`?"active":""}"
      data-action="scope" data-value="playlist:${p.id}" title="${esc(p.name)}" aria-label="${esc(p.name)}">
      ${collectionMark(p)}<span>${esc(p.name)}</span></button>`).join("")}</div>`;
  const navEl = get("navigation");
  if (navEl.dataset.rendered !== html) {
    navEl.innerHTML = html;
    navEl.dataset.rendered = html;
  }
}
async function refresh() {
  const request = ++stateRequest;
  lastRefresh = performance.now();
  const next = await api("/state");
  if (request!==stateRequest) return;
  state = next;
  nav();
  await loadLibrary();
}
async function backgroundRefresh(force=false) {
  if (document.hidden || modal.open || watchPath() || backgroundRefreshPending) return;
  const busy = state.counts.queued || state.counts.running || state.counts.cancelling;
  const profileBusy = pendingLocalizedProfile && pendingLocalizedProfile.until>performance.now();
  const delay = busy && scope==="downloads" ? 1900 : busy || scope==="downloads" || profileBusy ? 3500 : 15000;
  if (!force && performance.now()-lastRefresh<delay) return;
  backgroundRefreshPending = true;
  try { await refresh(); }
  catch { /* The next foreground poll can retry. */ }
  finally { backgroundRefreshPending = false; }
}
function pages(current,total,size,action) {
  const max = Math.ceil(total/size);
  if (max<=1) return "";
  return `<div class="pages"><button type="button" data-action="${action}" data-value="${current-1}" ${current<=1?"disabled":""}>‹ ${t("prev")}</button>
    <span>${current} / ${max}</span><button type="button" data-action="${action}" data-value="${current+1}" ${current>=max?"disabled":""}>${t("next")} ›</button></div>`;
}
function visibleKinds() { return ["videos",...hideShorts?[]:["shorts"],...hideLives?[]:["streams"]]; }
function applyVisibility(query) {
  if (hideShorts) query.append("exclude_kind","shorts");
  if (hideLives) query.append("exclude_kind","streams");
}
async function loadLibrary() {
  if (watchPath()) return;
  const id = ++lastRequest;
  const query = new URLSearchParams({summary:"1",scope,q:search,page,state:({downloads:"jobs",removed:"removed",continue:"ready",watched:"ready",ignored:"ready"})[scope]||"library"});
  const hasTabs = !scope || scope.startsWith("channel:") || ["ignored","watched"].includes(scope);
  if (!visibleKinds().includes(contentKind)) contentKind="videos";
  if (hasTabs) query.set("kind",contentKind);
  if (!["downloads","removed"].includes(scope)) applyVisibility(query);
  query.set("sort",sortOrder);
  if (!["downloads","removed"].includes(scope)) {
    for (const filter of libraryFilters) query.append("filter",filter);
    const now=new Date();query.set("today",`${now.getFullYear()}${String(now.getMonth()+1).padStart(2,"0")}${String(now.getDate()).padStart(2,"0")}`);
  }
  try {
    const {videos,total} = await api(`/videos?${query}`);
    if (id!==lastRequest) return;
    if (page>1 && !videos.length) { page=Math.max(1,Math.ceil(total/60)); return loadLibrary(); }
    const signature = JSON.stringify([scope,search,page,contentKind,hideShorts,hideLives,[...libraryFilters],sortOrder,videos,total,state.channels,state.playlists]);
    if (prior===signature) return;
    prior=signature; displayed=videos;
    const context = `${scope}\n${search}\n${hasTabs?contentKind:"all"}\n${hideShorts}\n${hideLives}\n${[...libraryFilters].sort()}\n${sortOrder}`;
    if (selectionContext!==context) { selectedVideos.clear(); lastSelectedVideo=null; selectionContext=context; }
    const channel = scope.startsWith("channel:") && channelOf(scope.slice(8));
    const playlist = scope.startsWith("playlist:") && state.playlists.find(p => p.id===scope.slice(9));
    const title = channel?.name || playlist?.name || t(({continue:"resume",ignored:"ignored",watched:"watched",inbox:"inbox",downloads:"downloads",removed:"removed"})[scope] || "library");
    const actions = channel ? `${channel.source?btn("browse",t("browse"),"download","accent",channel.id):""}${btn("edit",t("edit"),"settings","",channel.id)}${channel.source?btn("profile",t("refreshProfile"),"","flat",channel.id):""}` : "";
    const home = !scope && !search && page===1 && contentKind==="videos", hero = home && videos.find(video=>video.state==="ready");
    const head = home ? `<section class="hero ${hero?.thumbnail?"":"empty-art"}">
      ${hero?.thumbnail?`<img src="${asset(hero.id,hero.thumbnail)}" alt="">`:'<div class="art" aria-hidden="true"></div>'}
      <div class="hero-content">${hero?newBadge(hero):""}<h1>${esc(hero?.title||t("title"))}</h1><p>${esc(hero?.source_channel||t(hero?"recent":"intro"))}</p>
      ${hero?btn("watch",t("play"),"play","accent",hero.id):btn("addChannel",t("addChannel"),"plus","accent")}
      </div></section><div class="section-head"><h2>${t("recent")}</h2></div>` :
      channel ? channelPage(channel,actions) : `<div class="page-head"><h1 class="${playlist?"collection-title":""}">${playlist?collectionMark(playlist,"list","heading"):""}${esc(title)}</h1>${playlist?
        `${btn("editPlaylist",t("customizeCollection"),"settings","",playlist.id)}
        ${btn("deletePlaylist",t("deletePlaylist"),"trash","flat",playlist.id)}
        <a class="accent" href="/api/playlists/${encodeURIComponent(playlist.id)}/export?sort=${sortOrder}" download>${icon("download")} ${t("exportPlaylist")}</a>`:""}</div>`;
    const isQueue = scope==="downloads", isRemoved = scope==="removed";
    const results = videos.length
      ? `<div class="${isQueue||isRemoved?"jobs":"grid"}">${videos.map(isQueue?job:isRemoved?removedRow:card).join("")}</div>`
      : `<p class="empty">${t(search?"emptyCatalog":isQueue?"noJobs":"nothing")}</p>`;
    closeSelectionMenu();
    const tabs = hasTabs ? `<nav class="content-tabs" aria-label="${t("contentTabs")}">${visibleKinds().map(kind=>
      `<button type="button" data-action="contentKind" data-value="${kind}" aria-pressed="${contentKind===kind}">${t(kind)}</button>`).join("")}</nav>` : "";
    const filters=!["downloads","removed"].includes(scope)?`<div class="feed-filters" role="group" aria-label="${t("combineFilters")}" title="${t("combineFilters")}">
      ${[["all","all"],["new","filterNew"],["today","filterToday"],["week","filterWeek"],["unwatched","filterUnwatched"],["progress","filterProgress"]].map(([value,label])=>
        `<button type="button" data-action="libraryFilter" data-value="${value}" aria-pressed="${value==="all"?!libraryFilters.size:libraryFilters.has(value)}">${t(label)}</button>`).join("")}
      <select id="library-order" aria-label="${t("sortOrder")}">${["newest","oldest"].map(order=>option(order,t(order),sortOrder)).join("")}</select></div>`:"";
    get("library").innerHTML = head + `<div class="library-filters">${tabs}${filters}</div>` + (videos.length||selectedVideos.size?selectionToolbar():"") + results + pages(page,total,60,"page");
    if (get("library-order")) get("library-order").onchange=async event=>{sortOrder=event.target.value;localStorage.setItem("gridtube.sort",sortOrder);page=1;rememberLibrary();await loadLibrary();};
    updateSelection();
    if (channel?.source&&!channel.profile?.locale_available) {
      const key=`${channel.id}:${locale}`;
      if ((profileRequestTimes.get(key)??-Infinity)<performance.now()-600000) {
        profileRequestTimes.set(key,performance.now());
        pendingLocalizedProfile={key,until:performance.now()+45000};
        api(`/channels/${channel.id}/profile`,"POST",{}).catch(()=>{});
      }
    } else pendingLocalizedProfile=null;
  } catch (error) {
    if (id===lastRequest) { prior=""; get("library").textContent=t(error.message); }
  }
}
function selectionCheckbox(v) {
  return `<label class="video-select" ${selectedVideos.size?"":"hidden"} title="${esc(t("selectVideo"))}"><input type="checkbox" data-select-video="${v.id}"
    aria-label="${esc(`${t("selectVideo")}: ${jobTitle(v)}`)}" ${selectedVideos.has(v.id)?"checked":""}></label>`;
}
function selectionToolbar() {
  return `<div class="selection-toolbar" ${selectedVideos.size?"":"hidden"} role="group" aria-label="${t("deleteSelected")}">
    <label class="check"><input type="checkbox" id="select-page">${t("selectPage")}</label>
    <span id="selected-count" aria-live="polite"></span>
    ${btn("clearSelection",t("clearSelection"),"","flat")}${btn("deleteSelected",t("deleteSelected"),"trash","")}</div>`;
}
function selectionCount(count) { return `${count} ${t(count===1?"selectedVideoOne":"selectedVideos")}`; }
function updateSelection() {
  const active=selectedVideos.size>0;
  const toolbar=get("library").querySelector(".selection-toolbar");
  if (toolbar) toolbar.hidden=!active;
  document.querySelectorAll("[data-select-video]").forEach(input=>{
    input.closest(".video-select").hidden=!active;
    input.checked=selectedVideos.has(input.dataset.selectVideo);
    input.closest("article").classList.toggle("selected",input.checked);
  });
  const all=get("select-page"), count=displayed.filter(v=>selectedVideos.has(v.id)).length;
  if (all) { all.checked=displayed.length>0&&count===displayed.length;all.indeterminate=count>0&&count<displayed.length; }
  if (get("selected-count")) get("selected-count").textContent=selectionCount(selectedVideos.size);
  for (const action of ["clearSelection","deleteSelected"]) {
    const button=get("library").querySelector(`[data-action="${action}"]`);
    if (button) button.disabled=!selectedVideos.size;
  }
}
function closeSelectionMenu(restoreFocus=false) {
  const menu=get("video-context-menu");
  if (!menu) return;
  const anchor=menu.returnFocus;
  menu.remove();
  if (restoreFocus&&anchor?.isConnected) anchor.focus({preventScroll:true});
}
function openSelectionMenu(item, anchor, point) {
  closeSelectionMenu();
  if (!item) return;
  const menu=document.createElement("div");
  menu.id="video-context-menu";
  menu.className="video-context-menu";
  menu.setAttribute("role","menu");
  menu.setAttribute("aria-label",t("moreOptions"));
  menu.innerHTML=btn("selectVideo",t(selectedVideos.has(item.id)?"deselectVideo":"selectVideo"),"list","flat",item.id);
  if (item.state==="ready") menu.innerHTML+=btn("markWatched",t(item.watched?"markUnwatched":"markWatched"),"eye","flat",item.id)+
    btn("ignoreVideo",t(item.ignored?"unignoreVideo":"ignoreVideo"),"eyeOff","flat",item.id);
  menu.querySelectorAll("button").forEach(button=>button.setAttribute("role","menuitem"));
  menu.returnFocus=anchor;
  document.body.append(menu);
  const bounds=anchor.getBoundingClientRect(), box=menu.getBoundingClientRect();
  const viewport=document.documentElement;
  const left=point?.x??bounds.left, top=point?.y??bounds.bottom;
  menu.style.left=`${Math.max(8,Math.min(left,viewport.clientWidth-box.width-8))}px`;
  menu.style.top=`${Math.max(8,Math.min(top,viewport.clientHeight-box.height-8))}px`;
  menu.querySelector("button").focus({preventScroll:true});
}
function newBadge(v) { return v.is_new?`<span class="new-badge">${t("newVideo")}</span>`:""; }
function card(v) {
  if (v.state!=="ready") return pendingCard(v);
  const length = duration(v.duration);
  return `<article class="card" data-video-id="${v.id}">${selectionCheckbox(v)}<a href="/watch/${v.id}" class="visual ${v.thumbnail?"":"no-thumb"}" data-action="watch" data-value="${v.id}" aria-label="${esc(`${t("play")} ${v.title}`)}">
    ${v.thumbnail?`<img src="${asset(v.id,v.thumbnail)}" alt="" loading="lazy">`:""}<span class="play">${icon("play")}</span>
    ${length?`<span class="timed">${length}</span>`:""}${v.position&&v.duration?`<progress max="${Number(v.duration)}" value="${Number(v.position)}"></progress>`:""}</a>
    <div class="card-body"><div class="card-text"><h3>${esc(v.title)}</h3><small>${esc(originName(v))}${v.upload_date&&published(v.upload_date)?` · ${published(v.upload_date)}`:""}</small>${newBadge(v)}${v.watched?`<span class="watched-badge">${t("watched")}</span>`:""}</div>
    ${btn("organize",t("organize"),"more","flat icon-only",v.id)}</div></article>`;
}
function pendingCard(v) {
  const label=t(v.state==="queued"?"queuedState":v.state);
  const picture=v.preview_thumbnail;
  return `<article class="card pending-card ${v.state}" data-video-id="${v.id}">${selectionCheckbox(v)}
    <div class="visual pending-visual" aria-label="${esc(`${jobTitle(v)} · ${label}`)}">
      ${picture?`<img src="${esc(picture)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.hidden=true">`:""}
      ${v.duration?`<span class="timed">${duration(v.duration)}</span>`:""}
      <div class="pending-overlay">${v.state==="running"?jobProgress(v):`<span>${esc(label)}</span>`}</div>
    </div><div class="card-body"><div class="card-text"><h3>${esc(jobTitle(v))}</h3>
      <small>${esc(originName(v))}</small><span class="pending-state">${esc(label)}</span></div>
      ${btn("selectionMenu",t("moreOptions"),"more","flat icon-only",v.id)}</div>
    ${v.error?`<p class="pending-error" title="${esc(t(v.error))}">${esc(t(v.error))}</p>`:""}
    <div class="pending-actions">${v.state==="failed"?btn("retry",t("retry"),"download","",v.id):""}
      ${v.state!=="cancelling"?btn("cancelDownload",t(v.state==="failed"?"removeDownload":"cancelDownload"),"trash","danger icon-only",v.id):""}</div>
  </article>`;
}
function jobTitle(v) {
  return v.title && v.title !== v.url && v.title !== v.id ? v.title : `${t("youtubeVideo")} · ${v.id}`;
}
function job(v) {
  return `<article class="job" data-video-id="${v.id}">${selectionCheckbox(v)}<div><strong>${esc(jobTitle(v))}</strong><small>${t(v.state==="queued"?"queuedState":v.state)}</small>
    ${v.state==="running"?jobProgress(v):""}
    ${v.error?`<small>${esc(t(v.error))}</small>`:""}</div><aside class="job-actions">
      ${btn("selectionMenu",t("moreOptions"),"more","flat icon-only",v.id)}
      ${v.state==="failed"?`${btn("editRetry",t("editRetry"),"settings","",v.id)}${btn("retry",t("retry"),"","flat",v.id)}`:""}
      ${v.state!=="cancelling"?btn("cancelDownload",t(v.state==="failed"?"removeDownload":"cancelDownload"),"trash","danger",v.id):""}
    </aside></article>`;
}
function jobProgress(v) {
  const phases={prepare:"progressPrepare",video:"progressVideo",audio:"progressAudio",mux:"progressMux",
    thumbnail:"progressThumbnail",publish:"progressPublish"};
  const phase=t(phases[v.progress_phase]||"progressPrepare");
  const known=Number.isFinite(v.percent);
  const label=known?`${v.percent}%${v.progress_estimated?` (${t("progressEstimate")})`:""}`:"";
  return `<div class="job-progress"><div><small>${phase}</small>${known?`<span>${label}</span>`:""}</div>
    <progress max="100" ${known?`value="${v.percent}"`:""} aria-label="${phase}${label?` · ${label}`:""}"></progress></div>`;
}
function removedRow(v) {
  const missing = v.error === "external_media_missing";
  return `<article class="job" data-video-id="${v.id}">${selectionCheckbox(v)}<div><strong>${esc(v.title)}</strong>${missing?`<small>${t(v.error)}</small>`:""}</div><aside class="job-actions">
    ${btn("selectionMenu",t("moreOptions"),"more","flat icon-only",v.id)}
    ${missing?btn("retry",t("downloadAgain"),"download","",v.id):""}
    ${btn("restoreVideo",t("restoreVideo"),"","",v.id)}${btn("removeVideo",t("deleteMedia"),"","flat",v.id)}</aside></article>`;
}

function openSettings() {
  dialog(t("settings"),`<div class="dialog-body">
    <nav class="settings-tabs" aria-label="${t("settings")}">
      <button type="button" data-action="settingsTab" data-value="downloads" aria-pressed="true">${t("downloads")}</button>
      <button type="button" data-action="settingsTab" data-value="interface" aria-pressed="false">${t("interface")}</button>
      <button type="button" data-action="settingsTab" data-value="system" aria-pressed="false">${t("system")}</button>
    </nav>
    <form id="settings-downloads" class="stack"><h3>${t("defaults")}</h3>${prefs(state.settings,false)}
      <p role="alert"></p><button class="accent" type="submit">${t("save")}</button></form>
    <form id="settings-interface" class="stack" hidden><h3>${t("interface")}</h3>
      ${checked("hideShorts",t("hideShorts"),hideShorts)}${checked("hideLives",t("hideLives"),hideLives)}
      <p class="note">${t("visibilityHelp")}</p><p role="alert"></p><button class="accent" type="submit">${t("save")}</button></form>
    <div id="settings-system" class="stack" hidden>
      <section class="system-card"><h3>${t("backupTitle")}</h3><p class="note">${t("backupHelp")}</p>
        <div class="system-actions"><a class="accent" href="/api/system/backup" download>${t("exportBackup")}</a>
          <button id="restore-backup" type="button">${t("restoreBackup")}</button></div>
        <input id="backup-file" type="file" accept=".jsonl" aria-label="${t("importBackup")}" hidden>
        <p class="note">${t("backupRestoreHelp")}</p><p class="note">${t("restoreWarning")}</p>
        <p id="backup-preview"></p><p id="backup-error" role="alert"></p>
        <p id="system-change-status" role="status"></p></section>
      <section class="system-card"><h3>${t("libraryCheck")}</h3><p class="note">${t("libraryCheckHelp")}</p>
        <form id="library-check-form" class="stack">
          <p id="library-check-result" role="status"></p><p role="alert"></p>
          <button type="submit">${t("libraryCheck")}</button>
        </form></section>
      <details class="system-card"><summary>${t("resetTitle")}</summary><form id="reset-data-form" class="stack">
        <p class="note">${t("resetHelp")}</p>${checked("disk",t("resetDisk"),false)}
        <label>${t("resetConfirmInput")} <code id="reset-word">RESET</code><input name="confirmation" required maxlength="11" autocomplete="off"></label>
        <p role="alert"></p><button type="submit" class="danger danger-solid">${icon("trash")} ${t("resetTitle")}</button>
      </form></details>
      <section class="system-card"><h3>yt-dlp</h3><p class="note">${t("dependencyHelp")}</p>
        <p id="dependency-status" role="status"></p><p id="dependency-error" role="alert"></p>
        <div class="system-actions">${btn("updateDependency",t("updateDependency"),"","accent")}
        ${btn("restartDependency",t("restartDependency"))}</div></section>
      <section class="system-card"><h3>${t("activityLog")}</h3><div id="system-events"></div></section>
    </div></div>`);
  bind("settings-downloads",async data=>{await api("/settings","PUT",readPrefs(data));await finish();});
  bind("settings-interface",async data=>{
    hideShorts=data.has("hideShorts");hideLives=data.has("hideLives");
    localStorage.setItem("gridtube.hideShorts",String(hideShorts));localStorage.setItem("gridtube.hideLives",String(hideLives));
    page=1;prior="";
    if (!visibleKinds().includes(contentKind)) contentKind="videos";
    if (!watchPath()) rememberLibrary();
    await finish();
    if (watchVideo&&get("player")) await loadNext(watchVideo,get("player"));
  });
  bind("library-check-form",async ()=>{
    const output = get("library-check-result");
    output.textContent = "";
    const result = await api("/system/library/check","POST",{});
    const labels = {moved:"libraryMoved",missing:"libraryMissing",restored:"libraryRestored",ambiguous:"libraryAmbiguous"};
    output.textContent = Object.entries(labels).filter(([key])=>result[key])
      .map(([key,label])=>`${result[key]} ${t(label)}`).join(" · ") || t("libraryCheckEmpty");
    await refresh();
  });
  const backupFile = get("backup-file"), restoreButton = get("restore-backup");
  const changeStatus = get("system-change-status"), backupError = get("backup-error");
  const storedRestore = sessionStorage.getItem("gridtube.restoreToken");
  if (storedRestore) {
    get("settings-system").dataset.restoreToken = storedRestore;
    restoreButton.disabled = true;
    changeStatus.textContent = t("backupVerifying");
  }
  restoreButton.onclick = () => backupFile.click();
  backupFile.onchange = async () => {
    const file = backupFile.files[0];
    if (!file) return;
    restoreButton.disabled = backupFile.disabled = true;
    backupError.textContent = "";
    changeStatus.textContent = t("backupValidating");
    get("backup-preview").textContent = "";
    try {
      const data = new FormData();
      data.append("backup",file);
      const preview = await api("/system/backup/preview","POST",data);
      if (get("backup-file") !== backupFile) return;
      const summary = `${preview.channel} ${t("channels").toLowerCase()} · ${preview.playlist} ${t("playlists").toLowerCase()} · ${preview.video} ${t("videos").toLowerCase()}`;
      get("backup-preview").textContent = preview.missing ? `${summary}. ${preview.missing} ${t("backupMissingFiles")}.` : summary;
      changeStatus.textContent = t("backupRestoring");
      await applySystemChange("/system/backup/restore",{token:preview.token});
    } catch (error) {
      changeStatus.textContent = "";
      backupError.textContent = t(error.message);
    } finally {
      backupFile.disabled = false;
      backupFile.value = "";
      restoreButton.disabled = Boolean(sessionStorage.getItem("gridtube.restoreToken"));
    }
  };
  const reset = get("reset-data-form");
  reset.elements.disk.onchange = () => {
    get("reset-word").textContent = reset.elements.disk.checked ? "RESET MEDIA" : "RESET";
    reset.elements.confirmation.value = "";
  };
  bind("reset-data-form",data=>applySystemChange("/system/reset",{disk:data.has("disk"),confirmation:data.get("confirmation")}));
  const panel = get("settings-system");
  panel.querySelector('[data-action="updateDependency"]').disabled = true;
  panel.querySelector('[data-action="restartDependency"]').hidden = true;
}

async function applySystemChange(path, data) {
  const result = await api(path,"POST",data);
  const panel = get("settings-system");
  if (path === "/system/backup/restore") {
    sessionStorage.setItem("gridtube.restoreToken",data.token);
    sessionStorage.setItem("gridtube.restoreDeadline",String(Date.now()+180000));
    if (panel) panel.dataset.restoreToken = data.token;
  }
  if (!panel) return;
  panel.dataset.maintenance = "1";
  get("system-change-status").textContent = t(result.restarting?"restarting":"maintenanceManual");
  get("restore-backup").disabled = true;
  get("reset-data-form").reset();
  get("reset-word").textContent = "RESET";
  get("system-change-status").scrollIntoView({block:"nearest"});
}

function settingsTab(panel) {
  get("settings-downloads").hidden = panel!=="downloads";
  get("settings-interface").hidden = panel!=="interface";
  get("settings-system").hidden = panel!=="system";
  for (const tab of modal.querySelectorAll('[data-action="settingsTab"]')) {
    tab.setAttribute("aria-pressed",String(tab.dataset.value===panel));
  }
  if (panel==="system") pollSystem();
}

async function pollSystem() {
  const panel = get("settings-system");
  if (document.hidden || !modal.open || !panel || panel.hidden || panel.dataset.fetching) return;
  panel.dataset.fetching = "1";
  const status = get("dependency-status"), alert = get("dependency-error"), history = get("system-events");
  const restart = panel.querySelector('[data-action="restartDependency"]');
  const update = panel.querySelector('[data-action="updateDependency"]');
  const restartUntil = Number(panel.dataset.restartUntil || 0);
  try {
    const result = await api("/system");
    if (!panel.isConnected) return;
    const {active,bundled,pending,problem,updating,can_restart} = result.yt_dlp;
    const waiting = restartUntil>Date.now() && pending;
    if (!waiting) delete panel.dataset.restartUntil;
    update.disabled = updating || Boolean(waiting);
    restart.disabled = update.disabled;
    restart.hidden = !(pending && can_restart);
    status.textContent = [t("activeVersion")+" "+active, t("bundledVersion")+" "+bundled,
      pending && t("dependencyReady")+" "+pending, waiting && t("restarting"),
      updating && !waiting && t("dependencyChecking"), pending && !can_restart && t("restartPending")].filter(Boolean).join(" · ");
    const lastUpdate = result.events.find(event=>event.area==="dependency");
    alert.textContent = t(problem || (lastUpdate?.severity==="error" ? lastUpdate.code : "")) || "";
    const restoreToken = panel.dataset.restoreToken;
    if (restoreToken) {
      const restored = await api(`/system/backup/status/${encodeURIComponent(restoreToken)}`);
      if (!panel.isConnected) return;
      const expired = Date.now() > Number(sessionStorage.getItem("gridtube.restoreDeadline") || 0);
      if (["verified","failed"].includes(restored.status) || expired && restored.status === "unknown") {
        get("system-change-status").textContent = t(restored.status === "verified" ? "backup_restored"
          : restored.status === "failed" ? "backup_restore_failed" : "backup_result_unknown");
        sessionStorage.removeItem("gridtube.restoreToken");
        sessionStorage.removeItem("gridtube.restoreDeadline");
        delete panel.dataset.restoreToken;
        delete panel.dataset.maintenance;
        get("restore-backup").disabled = false;
        refresh().catch(()=>{});
      } else {
        get("system-change-status").textContent = t(restored.status === "pending"
          ? can_restart ? "restarting" : "maintenanceManual" : "backupVerifying");
      }
    } else if (panel.dataset.maintenance && !result.maintenance_pending) {
      delete panel.dataset.maintenance;
      const event = result.events.find(entry=>entry.area==="system");
      get("system-change-status").textContent = t(event?.code || "done");
      get("restore-backup").disabled = false;
      refresh().catch(()=>{});
    }
    const signature = JSON.stringify(result.events);
    if (history.dataset.rendered!==signature) {
      const date = new Intl.DateTimeFormat(locale,{dateStyle:"short",timeStyle:"medium"});
      history.innerHTML = result.events.length ? `<ul class="system-events">${result.events.map(event=>
        `<li class="${event.severity==="error"?"system-error":""}"><time>${date.format(event.timestamp*1000)}</time>
        <strong>${esc(t(event.code))}</strong>${event.detail&&!["backup_restored","backup_restore_failed"].includes(event.code)?`<pre>${esc(event.detail)}</pre>`:""}</li>`).join("")}</ul>` :
        `<p class="note">${t("noActivity")}</p>`;
      history.dataset.rendered = signature;
    }
  } catch {
    alert.textContent = t(restartUntil>Date.now()?"restarting":"systemUnavailable");
  } finally {
    delete panel.dataset.fetching;
  }
}

async function runMaintenance(restart) {
  const panel = get("settings-system"), alert = get("dependency-error");
  if (!panel || (restart && !window.confirm(t("restartConfirm")))) return;
  const buttons = [...panel.querySelectorAll("button")];
  buttons.forEach(button=>button.disabled=true);
  try {
    await api(`/system/yt-dlp${restart?"/restart":""}`,"POST",{});
    if (restart) panel.dataset.restartUntil = String(Date.now()+45000);
    await pollSystem();
  } catch (error) {
    alert.textContent=t(error.message);
    buttons.forEach(button=>button.disabled=false);
  }
}
function dialog(title, html, css="") {
  closeSelectionMenu();
  catalog = null;
  if (modal.open) modal.close();
  modal.className = css;
  modal.innerHTML = `<header class="dialog-head"><h2>${esc(title)}</h2>${btn("close",t("close"),"close","flat icon-only")}</header>${html}`;
  modal.showModal();
}
function bind(id, handler) {
  get(id).onsubmit = async event => {
    event.preventDefault();
    const submit = event.submitter, form = event.currentTarget, alert = form.querySelector("[role=alert]");
    if (submit) submit.disabled = true;
    if (alert) alert.textContent = "";
    try { await handler(new FormData(form)); }
    catch (error) { if (alert) alert.textContent = t(error.message); else flash(t(error.message)); }
    finally {
      if (submit) submit.disabled = false;
      if (catalog && form.id==="catalog-form") selection();
    }
  };
}
const field = (key,value="",attrs="") => `<label>${t(key)}<input name="${key}" value="${esc(value)}" ${attrs}></label>`;
const option = (key,name,selected) => `<option value="${esc(key)}" ${key===selected?"selected":""}>${esc(name)}</option>`;
const select = (key,name,items,selected) => `<label>${name}<select name="${key}" aria-label="${esc(name)}">${items.map(([k,n])=>option(k,n,selected)).join("")}</select></label>`;
const checked = (key,name,value) => `<label class="check"><input name="${key}" type="checkbox" ${value?"checked":""}>${name}</label>`;
function simple(title,html,action,handler) {
  dialog(t(title),`<form id="simple" class="dialog-body">${html}<p role="alert"></p><button class="accent" type="submit">${t(action)}</button></form>`);
  bind("simple",handler);
}
function prefs(values,local,{single=false,inherited={},inheritLabel=t("inherit")}={}) {
  const choices = {
    download_mode:[["compact",t("compact")],["original",t("originalQuality")]],
    quality:["360","480","720","1080","1440","2160","best"].map(q=>[q,q==="best"?t(q):`${q}p`]),
    shorts:["include","exclude","only"].map(k=>[k,t(k)]),
    lives:[["include",t("allowCapture")],["exclude",t("disableCapture")]],
    audio:[["original",t("original")],["pt-BR","Português (Brasil)"],["en","English"]],
    subtitles:[["none",t("none")],["pt-BR","Português (Brasil)"],["en","English"],["both",t("both")]],
    auto_subtitles:[["true",t("yes")],["false",t("no")]]
  };
  if (single) { delete choices.shorts;delete choices.lives; }
  const numericField=(key,label,placeholder,help)=>`<label>${t(label)}<input type="number" min="0" max="1000000" step="1"
    name="pref_${key}" value="${esc(local?(values[key]??""):(values[key]||""))}" placeholder="${esc(placeholder)}"><small class="note">${help}</small></label>`;
  const durationDefault=local?`${inheritLabel} · ${inherited.max_duration?`${inherited.max_duration} min`:t("noLimit")}`:t("noLimit");
  const numericFields=single?"":numericField("max_duration","maxDuration",durationDefault,t("durationHelp"))+
    (local?"":numericField("auto_delete_days","autoDeleteDays",t("never"),t("autoDeleteHelp"))+
      numericField("new_badge_days","newBadgeDays",t("untilOpened"),t("newBadgeHelp")));
  return `<div class="cols">${Object.entries(choices).map(([key,items])=>{
    const inheritedChoice = items.find(([value])=>value===String(inherited[key]))?.[1];
    const inheritedOption = inheritedChoice ? `${inheritLabel} · ${inheritedChoice}` : inheritLabel;
    return select(`pref_${key}`,t(key==="auto_subtitles"?"autoSub":key),
      local?[["",inheritedOption],...items]:items,String(values[key]??""));
  }).join("")}${numericFields}</div><small class="note">${t("resolutionHelp")}${single?"":` ${t("livesHelp")}`}</small>`;
}
function readPrefs(data) {
  return Object.fromEntries([...data].filter(([k,v])=>k.startsWith("pref_")&&v!=="")
    .map(([k,v])=>[k.slice(5),k==="pref_auto_subtitles"?v==="true":
      ["pref_max_duration","pref_auto_delete_days","pref_new_badge_days"].includes(k)?Number(v):v]));
}
function channels(inbox=t("inbox")) { return [["",inbox],...state.channels.map(c=>[c.id,c.name])]; }

function videoCaptureFields(channelId, values={}) {
  const channel = channelOf(channelId);
  const inherited = {...state.settings,...channel?.overrides};
  return prefs(values,true,{single:true,inherited,inheritLabel:t(channel?"useChannel":"inherit")});
}
function downloadByLink() {
  const channel = scope.startsWith("channel:") ? scope.slice(8) : "";
  simple("addLink",`${field("url","","type=url required")}
    ${select("channel",t("channel"),channels(),channel)}
    <fieldset class="capture-options"><legend>${t("videoOptions")}</legend>
      <p class="note">${t("videoOptionsNote")}</p>
      <div id="link-options">${videoCaptureFields(channel)}</div>
    </fieldset>`,"addLink",async data=>{
      const {queued} = await api("/downloads","POST",
        {url:data.get("url"),channel:data.get("channel"),overrides:readPrefs(data)});
      await finish(t(queued?"queued":"saved"));
    });
  const form = get("simple");
  form.elements.channel.onchange = event=>{
    const values = readPrefs(new FormData(form));
    get("link-options").innerHTML = videoCaptureFields(event.target.value,values);
  };
}
function editRetry(item) {
  if (!item || item.state!=="failed") return;
  simple("editRetry",`<strong class="wrap">${esc(jobTitle(item))}</strong>
    <fieldset class="capture-options"><legend>${t("videoOptions")}</legend>
      <p class="note">${t("videoOptionsNote")}</p>${videoCaptureFields(item.channel_id,item.capture_overrides)}
    </fieldset>`,"retry",async data=>{
      await api(`/videos/${item.id}/retry`,"POST",{overrides:readPrefs(data)});
      await finish(t("queuedState"));
    });
}
async function finish(message=t("done")) {
  modal.close();
  flash(message);
  await refresh();
}
function editChannel(channel, videoId) {
  let createdId = null;
  const auto = channel ? `${checked("auto",t("auto"),channel.auto)}<small>${t("autoNote")}</small>` : "";
  simple(channel?"edit":"localChannel",`${field("name",channel?.name,"required maxlength=100")}
    ${channel?field("channelUrl",channel.source,"type=url"):""}
    ${channel?.source?field("titleFilter",channel.title_filter,`maxlength="120" placeholder="${t("titleExample")}"`):""}
    ${!channel?.source?collectionFields(channel,"folder"):""}
    <label>${t("channelDescription")}<textarea name="description" maxlength="5000" rows="3">${esc(channel?.custom_description||"")}</textarea></label>
    <p class="note">${t("configNote")}</p>${prefs(channel?.overrides||{},true,{inherited:state.settings})}${auto}`,"save",async data=>{
    const result=createdId?{id:createdId}:await api(channel?`/channels/${channel.id}`:"/channels",channel?"PUT":"POST",
      {name:data.get("name"),overrides:readPrefs(data),auto:data.has("auto"),description:data.get("description"),
        title_filter:data.get("titleFilter") ?? channel?.title_filter ?? "",
        ...(!channel?.source?{appearance:readAppearance(data)}:{}),
        ...(channel?{source:data.get("channelUrl")}:{})});
    if (videoId) {
      createdId=result.id;
      await api(`/videos/${videoId}/move`,"POST",{channel:createdId});
    }
    await finish();
  });
  if (channel) get("simple").insertAdjacentHTML("afterend",`<div class="dialog-body channel-delete-action">
    ${btn("deleteChannel",t("deleteChannel"),"trash","",channel.id)}</div>`);
}
function collectionFields(collection, fallback="list") {
  const style = collection?.appearance || {icon:fallback,color:"#bebebe"};
  const glyph = collectionIcons.some(([name])=>name===style.icon) ? style.icon : fallback;
  const color = /^#[a-f\d]{6}$/i.test(style.color) ? style.color : "#bebebe";
  return `<fieldset class="collection-picker" style="--collection-color:${color}"><legend>${t("collectionAppearance")}</legend>
    <div class="collection-icons">${collectionIcons.map(([name,label])=>`<label title="${t(label)}">
      <input type="radio" name="collectionIcon" value="${name}" aria-label="${t(label)}" ${name===glyph?"checked":""}>
      <span>${icon(name)}</span></label>`).join("")}</div>
    <label class="collection-color">${t("collectionColor")}<input type="color" name="collectionColor" value="${color}"></label>
  </fieldset>`;
}
function readAppearance(data) {
  return {icon:data.get("collectionIcon"),color:data.get("collectionColor")};
}
function editPlaylist(playlist, videoId) {
  simple(playlist?"customizeCollection":"addPlaylist",
    (playlist?`<strong>${esc(playlist.name)}</strong>`:field("name","","required maxlength=100"))+collectionFields(playlist),
    "save",async data=>{
      await api(playlist?`/playlists/${playlist.id}/appearance`:"/playlists",playlist?"PUT":"POST",
        {...(!playlist?{name:data.get("name")}:{}),...(videoId?{video:videoId}:{}),appearance:readAppearance(data)});
      await finish();
    });
}
function scanURL(source) { return `/scans?${new URLSearchParams({source})}`; }
function catalogParams(session, mode={}) {
  return new URLSearchParams({
    q:mode.whole?"":get("catalog-q").value,
    kind:mode.whole?"all":get("catalog-kind").value,
    playlist:mode.whole?"":get("catalog-playlist").value,
    rule:session.channel?.title_filter || get("catalog-rule")?.value || "",
    limit:session.limit,...(mode.ids?{ids:"1"}:{})
  });
}
function openCatalog(source,channel) {
  dialog(channel?.name||t("addChannel"),`<form id="catalog-form"><div class="dialog-body">
    ${channel?`<p class="note">${channel.title_filter?`${t("titleFilter")} · ${esc(channel.title_filter)}`:""}</p>`:
      `${field("name","","maxlength=100")}<label>${t("titleFilter")}<input id="catalog-rule" name="title_filter" placeholder="${t("titleExample")}" maxlength="120"></label>
      <details><summary>${t("overrides")}</summary><div class="stack">
      ${prefs({},true,{inherited:state.settings})}${checked("auto",t("auto"),false)}<small>${t("autoNote")}</small></div></details>`}
    <div class="catalog-tools"><input type="search" id="catalog-q" aria-label="${t("scanSearch")}" placeholder="${t("scanSearch")}">
    <select id="catalog-kind" aria-label="${t("catalogFilter")}">${["all","videos","shorts","streams"].map(k=>option(k,t(k),"")).join("")}</select>
    ${btn("scan",t("refresh"),"","",source)}</div>
    <div class="catalog-playlists"><select id="catalog-playlist" aria-label="${t("playlistFilter")}"><option value="">${t("allPlaylists")}</option></select>
    <small id="playlist-status" role="status"></small></div>
    <div class="catalog-bulk"><p id="catalog-status" class="note" role="status"></p>
      <button id="catalog-all" type="button">${t("selectResults")}</button>
      <button id="catalog-clear" class="flat" type="button">${t("clearSelection")}</button>
    </div>
    <div id="catalog-results"></div><p role="alert"></p></div>
    <div class="dialog-actions"><span class="count" id="selection"></span><button type="submit" class="accent" id="catalog-submit">${t(channel?"queueSelection":"saveChannel")}</button></div></form>`,"catalog-dialog");
  const session = {source,channel,picks:new Set(),limit:60,last:"",seq:0,pending:true,busy:false,selectable:0,total:0};
  catalog = session;
  function changed() {
    session.limit=60;
    pollCatalog(session);
  }
  get("catalog-q").oninput = debounced(changed);
  get("catalog-kind").onchange = changed;
  get("catalog-playlist").onchange = async () => {
    const playlist = get("catalog-playlist").value;
    session.limit=60;
    try {
      if (playlist) await api("/scans/playlists","POST",{source,playlist});
      await pollCatalog(session);
    } catch (error) { flash(t(error.message)); }
  };
  if (get("catalog-rule")) get("catalog-rule").oninput = debounced(async()=>{
    if (catalog!==session || !modal.open) return;
    try {
      const params=catalogParams(session,{whole:true,ids:true});
      const filter=params.get("rule");
      const {ids}=await api(`${scanURL(source)}&${params}`);
      if (catalog!==session || !modal.open || get("catalog-rule").value!==filter) return;
      if (filter.trim()) {
        const allowed=new Set(ids);
        session.picks=new Set([...session.picks].filter(id=>allowed.has(id)));
      }
      changed();
    } catch(error) { flash(t(error.message)); }
  });
  get("catalog-all").onclick = async event=>{
    const button=event.currentTarget;
    const params=catalogParams(session,{ids:true});
    button.disabled=true;
    try {
      const {ids}=await api(`${scanURL(source)}&${params}`);
      if (catalog!==session || !modal.open || String(catalogParams(session,{ids:true}))!==String(params)) return;
      ids.forEach(id=>session.picks.add(id));
      selection();
    } catch(error) { flash(t(error.message)); }
    finally { if (catalog===session && modal.open) selection(); }
  };
  get("catalog-clear").onclick = ()=>{
    session.picks.clear();
    selection();
  };
  get("catalog-results").onchange = event => {
    if (event.target.type!=="checkbox") return;
    const {value,checked} = event.target;
    if (checked) session.picks.add(value); else session.picks.delete(value);
    selection();
  };
  bind("catalog-form",async data=>{
    if (session.busy) return;
    session.busy = true;
    try {
      const selected = [...session.picks];
      const result = channel ? await api(`/channels/${channel.id}/queue`,"POST",{selected}) :
        await api("/channels","POST",{source,selected,name:data.get("name"),overrides:readPrefs(data),
          auto:data.has("auto"),title_filter:data.get("title_filter")});
      await finish([result.queued?`${t("queued")} · ${result.queued}`:t("done"),
        result.blocked?`${t("blockedDownloads")} · ${result.blocked}`:""].filter(Boolean).join(" · "));
    } finally { session.busy = false; }
  });
  api("/scans/playlists","POST",{source}).catch(()=>{});
  selection();
  pollCatalog(session);
}
function selection() {
  const count = catalog.picks.size;
  get("selection").textContent = `${count} ${t("selection")}`;
  get("catalog-submit").disabled = catalog.busy || Boolean(catalog.channel && !count);
  get("catalog-all").disabled = catalog.pending || !catalog.selectable;
  get("catalog-clear").disabled = !count;
  for (const box of get("catalog-results").querySelectorAll('input[type="checkbox"]')) box.checked=catalog.picks.has(box.value);
}
async function pollCatalog(session) {
  if (!modal.open || catalog!==session) return;
  const seq = ++session.seq;
  try {
    const query = catalogParams(session);
    const data = await api(`${scanURL(session.source)}&${query}`);
    if (catalog!==session || seq!==session.seq || !modal.open) return;
    if (data.state==="stale"&&!session.refreshing) {
      session.refreshing=true;
      session.pending=true;
      await api("/scans","POST",{url:session.source});
      return pollCatalog(session);
    }
    const listState = data.playlists_state;
    session.pending = data.playlist ? (data.playlist.state==="loading"||data.playlist.state==="idle") : data.state==="loading";
    session.autoPoll = session.pending || listState==="loading" || listState==="idle";
    session.selectable=data.selectable;
    session.total=data.total;
    const name = get("catalog-form").elements.namedItem("name");
    if (name&&data.name&&!session.named) {
      if (!name.value) name.value=data.name.slice(0,100);
      session.named=true;
    }
    const playlistControl=get("catalog-playlist");
    const playlistSignature=JSON.stringify(data.playlists);
    if (session.playlists!==playlistSignature) {
      session.playlists=playlistSignature;
      const current=playlistControl.value;
      playlistControl.innerHTML=option("",t("allPlaylists"),current)+data.playlists.map(p=>option(p.id,p.title,current)).join("");
    }
    get("playlist-status").textContent = listState==="loading"||listState==="idle"?t("loadingPlaylists"):
      listState==="error"?t("playlistError"):`${data.playlists.length} ${t("playlists").toLowerCase()}`;
    const error=data.playlist?.error || (!data.playlist&&data.error);
    const count=`${data.entries.length} ${t("ofCount")} ${data.total} ${t("videos").toLowerCase()}`;
    get("catalog-status").textContent = session.pending?`${count} · ${t("scanning")}`:error?t(error):count;
    const signature = JSON.stringify([data.total,data.entries]);
    if (session.last!==signature) {
      session.last=signature;
      const list=data.entries.map(item=>`<label class="catalog-item"><input type="checkbox" value="${item.id}" ${item.saved?"disabled":""}>
        <span>${esc(item.title)}</span><small>${item.saved?t(item.saved==="removed"?"removed":"saved"):[item.kind!=="videos"?t(item.kind):"",duration(item.duration)].filter(Boolean).join(" · ")}</small></label>`).join("");
      const results=get("catalog-results"), priorOffset=results.querySelector(".catalog-items")?.scrollTop||0;
      const more=data.entries.length<data.total?`<div class="pages">${btn("catalogMore",t("loadMore"))}${btn("catalogAll",t("loadAll"))}</div>`:"";
      results.innerHTML=list?`<div class="catalog-items">${list}</div>${more}`:`<p class="empty">${t("emptyCatalog")}</p>`;
      if (list) results.querySelector(".catalog-items").scrollTop=priorOffset;
    }
    selection();
  } catch(error) {
    if (catalog===session&&modal.open) get("catalog-status").textContent=t(error.message);
  }
}


function languageName(code) {
  try { return new Intl.DisplayNames([locale],{type:"language"}).of(code) || code; }
  catch { return code; }
}

function watch(item, initialJobs=[], autoplay=false) {
  watchVideo = item;
  if (item.is_new) api(`/videos/${item.id}/opened`,"POST",{}).catch(error=>flash(t(error.message)));
  const chapters = (item.chapters||[]).map(c=>btn("seek",`${duration(c.start_time)||"0:00"} · ${c.title}`,"","",Number(c.start_time))).join(" ");
  const theater = (localStorage.getItem("gridtube.theater") ?? localStorage.getItem("untube.theater")) === "true";
  app.querySelector(".shell").classList.toggle("cinema",theater);
  get("library").innerHTML = `<div class="watch-topline">${btn("back",t("back"),"back","flat")}</div>
    <div id="watch-layout" class="watch-layout ${theater?"theater":""}">
      <div class="watch-primary">
        <div class="watch-frame ${item.kind==="shorts"?"portrait":""}">
          <video id="player" controls playsinline preload="metadata" aria-label="${esc(item.title)}"
            ${item.thumbnail?`poster="${asset(item.id,item.thumbnail)}"`:""} src="${asset(item.id,item.filename)}"></video>
        <div class="watch-controls">
          <details class="track-settings" id="track-settings">
            <summary aria-label="${t("playerSettings")}" title="${t("playerSettings")}">
              ${icon("gear")}<span class="track-alert" id="track-alert" hidden></span>
            </summary>
            <section class="track-settings-panel" aria-label="${t("playerSettings")}">
              <h2>${t("playerSettings")}</h2>
              <div class="cols" id="saved-tracks"></div>
              <p id="audio-provenance" class="note" hidden></p>
              <p id="audio-fallback" class="note" hidden>${t("audioFallback")}</p>
              <details id="watch-track-panel"><summary>${t("moreTracks")}</summary>
                <div class="stack"><button id="discover-tracks" type="button">${t("loadTracks")}</button>
                <p id="discovery-status" class="note" role="status"></p>
                <div id="offered-tracks"></div></div>
              </details>
              <div id="track-jobs" aria-live="polite"></div>
            </section>
          </details>
        </div>
        </div>
        <div class="player-meta">
          <h1 id="watch-title">${esc(item.title)}</h1>
          <div class="watch-bar">
            <div id="watch-channel" class="watch-channel"></div>
            <button class="watch-pill" type="button" id="theater-mode" aria-pressed="${theater}">${icon("theater")} ${t("theater")}</button>
            ${btn("organize",t("organize"),"more","watch-pill",item.id)}
          </div>
          <div class="watch-info">
            <div class="watch-date note" id="watch-date"></div>
            <div id="watch-description" hidden><p id="description-text"></p>
              <button id="expand-description" class="flat description-toggle" type="button" aria-expanded="false">${t("showDescription")}</button></div>
            ${youtubeLink(item)}
          </div>
          ${chapters?`<details><summary>${t("chapters")}</summary><div class="watch-chapters">${chapters}</div></details>`:""}
        </div>
      </div>
      <aside id="watch-next" class="watch-next" hidden></aside>
    </div>`;

  const player = get("player");
  const playerFrame = player.closest(".watch-frame");
  const endpoint = `/videos/${item.id}/tracks`;
  const saved = get("saved-tracks");
  const settingsMenu = get("track-settings");
  const settingsButton = settingsMenu.querySelector("summary");
  const description = get("watch-description");
  let video = item, jobs = initialJobs, offered = null;
  let audio = "", subtitle = "", signature = "", trackSignature = "", availableSignature = "";
  let last = item.position || 0, requestedTime = last, resume = autoplay, initialized = false;
  let polling = false, closed = false, loadingNext = false, lastPoll = performance.now();

  const active = () => !closed && get("player") === player;
  const videoUrl = () => audio
    ? `/playback/${encodeURIComponent(item.id)}/${encodeURIComponent(audio)}`
    : asset(item.id,video.filename);
  const update = (position,keepalive=false) => {
    if (!initialized || position===last) return;
    last=position;
    fetch(`/api/videos/${item.id}/progress`,{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({position}),keepalive}).catch(()=>{});
  };
  const positionedTracks = new WeakSet();
  const positionSubtitles = node => {
    const track = node.track;
    const cues = track.cues;
    if (!cues?.length || positionedTracks.has(node)) return;
    // A cue can retain the file's position anchor even when the browser omits its DOM setter.
    const originals = Array.from(cues);
    positionedTracks.add(node);
    for (const cue of originals) {
      const centered = new VTTCue(cue.startTime, cue.endTime, cue.text);
      centered.id = cue.id;
      centered.pauseOnExit = cue.pauseOnExit;
      centered.size = 90;
      track.removeCue(cue);
      track.addCue(centered);
    }
  };
  const setSubtitle = () => {
    for (const node of player.querySelectorAll("track")) {
      const selected = node.srclang === subtitle;
      node.track.mode = selected ? "showing" : "disabled";
      if (selected) positionSubtitles(node);
    }
  };
  const changeAudio = (next, position=initialized?player.currentTime:requestedTime,
                       playing=initialized?!player.paused:resume) => {
    audio = next;
    requestedTime = position;
    resume = playing;
    initialized = false;
    player.src = videoUrl();
    player.load();
  };
  player.onloadedmetadata = () => {
    if (requestedTime>0 && requestedTime<player.duration) player.currentTime=requestedTime;
    initialized = true;
    setSubtitle();
    if (resume) player.play().catch(()=>{});
    resume = false;
  };
  player.onerror = () => {
    if (!audio) {
      if (active()) flash(t("videoPlaybackError"));
      return;
    }
    flash(t("playbackError"));
    saved.querySelector("[name=watchAudio]").value = "";
    saved.querySelector('[data-remove-track][data-kind="audio"]').hidden = true;
    changeAudio("");
  };
  player.ontimeupdate = ()=>{if(Math.abs(player.currentTime-last)>=10) update(player.currentTime);};
  player.onseeked = ()=>update(player.currentTime);
  player.onpause = ()=>update(player.ended?0:player.currentTime);
  player.onended = ()=>{update(0);api(`/videos/${item.id}/watched`,"POST",{watched:true}).then(()=>{item.watched=true;}).catch(error=>flash(t(error.message)));};

  async function queue(kind,code,retry=false) {
    const result = await api(endpoint,"POST",{kind,code,retry});
    if (result.queued) flash(t("queuedState"));
    await poll();
  }

  const trackTrash = (kind, code, savedTrack) => {
    const title = t(savedTrack ? "deleteTrack" : "deleteTrackAttempt");
    return `<button type="button" class="flat danger track-trash" data-remove-track data-kind="${kind}" data-code="${esc(code)}"
      title="${title}" aria-label="${title}" ${savedTrack&&!code?"hidden":""}>${icon("trash")}</button>`;
  };
  async function deleteTrack(button, savedTrack) {
    const {kind,code} = button.dataset;
    await api(`${endpoint}/${kind}/${encodeURIComponent(code)}`,"DELETE",{saved:savedTrack});
    await poll();
  }

  function render() {
    const date = published(video.upload_date);
    get("watch-date").innerHTML = date ? `${t("publication")} ${date}` : t("noDate");
    const channel = channelOf(video.channel_id);
    const origin = video.source_profile || {};
    const author = esc(originName(video));
    const sameChannel = channel && (channel.source === video.source_channel_url ||
      (origin.handle && channel.profile?.handle?.toLowerCase() === origin.handle.toLowerCase()) ||
      (!video.source_channel_url && channel.name === video.source_channel));
    const channelMarkup = origin.avatar
      ? `<img class="channel-avatar" src="/source-branding/${video.id}/${encodeURIComponent(origin.avatar)}" alt="">`
      : sameChannel ? channelAvatar(channel) : `<span class="channel-avatar placeholder">${icon("folder")}</span>`;
    const channelHtml = sameChannel
      ? `<button type="button" class="source-channel flat" data-action="scope" data-value="channel:${channel.id}">${channelMarkup}${author}</button>`
      : `${channelMarkup}<strong>${author}</strong>`;
    const channelSlot = get("watch-channel");
    if (channelSlot.dataset.markup !== channelHtml) {
      channelSlot.dataset.markup = channelHtml;
      channelSlot.innerHTML = channelHtml;
    }
    get("watch-title").textContent = video.title;
    document.title = video.title + " · " + appName;
    watchVideo = video;
    description.hidden = !video.description;
    get("description-text").textContent = video.description || "";

    const provenance = get("audio-provenance");
    const tag = video.audio_file_language;
    const reported = video.audio_reported;
    const conflict = tag && reported && tag.toLowerCase().split("-")[0] !== reported.toLowerCase().split("-")[0];
    const explanation = conflict ? `${t("sourceConflict")}: ${languageName(tag)} · ${t("sourceReported")}: ${languageName(reported)}`
      : video.audio_label_source === "youtube" ? t("languageReported") : "";
    provenance.textContent = explanation;
    provenance.hidden = !explanation;
    get("audio-fallback").hidden = !video.audio_fallback;
    const failed = jobs.some(job=>job.state==="failed");
    get("track-alert").hidden = !failed;
    settingsButton.setAttribute("aria-label",failed ? `${t("playerSettings")} · ${t("trackAttention")}` : t("playerSettings"));
    const audioTracks = video.audio_tracks || {};
    const subtitles = video.subtitles || {};
    const newSignature = JSON.stringify([video.audio,audioTracks,subtitles]);
    if (signature !== newSignature) {
      signature = newSignature;
      if (audio && !audioTracks[audio]) changeAudio("");
      if (subtitle && !subtitles[subtitle]) subtitle = "";
      saved.innerHTML = `<div class="saved-track">${select("watchAudio",t("watchAudio"),
        [["",video.audio?languageName(video.audio):t("originalSaved")],
         ...Object.keys(audioTracks).map(tag=>[tag,languageName(tag)])],audio)}${trackTrash("audio",audio,true)}</div>
        <div class="saved-track">${select("watchSubtitles",t("watchSubtitles"),
          [["",t("none")],...Object.keys(subtitles).map(tag=>[tag,languageName(tag)])],subtitle)}${trackTrash("subtitle",subtitle,true)}</div>`;
      for (const node of player.querySelectorAll("track")) {
        if (!subtitles[node.srclang]) node.remove();
      }
      for (const [tag,filename] of Object.entries(subtitles)) {
        if ([...player.querySelectorAll("track")].some(node=>node.srclang===tag)) continue;
        const track = document.createElement("track");
        track.kind = "subtitles";
        track.src = asset(video.id,filename);
        track.srclang = tag;
        track.label = languageName(tag);
        track.addEventListener("load", () => positionSubtitles(track));
        track.track.addEventListener("cuechange", () => positionSubtitles(track));
        player.append(track);
      }
      setSubtitle();
    }

    const now = Date.now()/1000;
    const waiting = job=>job.retry_at>now;
    const renderableJobs = jobs.map(job=>({...job,waiting:waiting(job)}));
    const newJobs = JSON.stringify(renderableJobs);
    if (newJobs !== trackSignature) {
      trackSignature = newJobs;
      get("track-jobs").innerHTML = jobs.filter(job=>job.state!=="ready").map(job=>`
        <div class="track-job"><span>${esc(languageName(job.code))} · ${t(job.kind==="audio"?"watchAudio":"subtitleDownload")}<small>${esc(t(job.error || (job.state==="queued"?"queuedState":job.state)))}</small></span>
        ${job.state==="failed"?`<div class="track-actions">${waiting(job)?`<small>${t("retryAfter")} ${new Date(job.retry_at*1000).toLocaleTimeString(locale,{hour:"2-digit",minute:"2-digit"})}</small>`:`<button type="button" data-kind="${job.kind}" data-code="${esc(job.code)}">${t("retry")}</button>`}${trackTrash(job.kind,job.code,false)}</div>`:""}</div>`).join("");
    }

    const newAvailable = JSON.stringify([signature,trackSignature,offered]);
    if (offered && newAvailable !== availableSignature) {
      availableSignature = newAvailable;
      const busy = job=>job.state==="queued"||job.state==="running"||waiting(job);
      const choices = kind=>offered[kind].filter(option=>(
        !jobs.some(job=>job.kind===kind&&job.code===option.code&&busy(job)) &&
        (kind==="audio" ? option.code!==video.audio && !audioTracks[option.code] : !subtitles[option.code])
      )).map(option=>[option.code,kind==="subtitle"
        ? `${languageName(option.code)} · ${t(option.translated?"translated":option.automatic?"generated":"manual")}` : languageName(option.code)])
        .sort((a,b)=>a[1].localeCompare(b[1],locale));
      const rows = [["audio","additionalAudio"],["subtitle","additionalSubtitle"]].map(([kind,key])=>{
        const values = choices(kind);
        return values.length ? `<form id="extra-${kind}" class="add-track-row">${select("code",t(key),values,values[0][0])}
          <button type="submit">${t(key)}</button></form>` : "";
      }).filter(Boolean);
      get("offered-tracks").innerHTML = rows.join("") || `<p class="note">${t("trackEmpty")}</p>`;
      for (const kind of ["audio","subtitle"]) if(get(`extra-${kind}`)) bind(`extra-${kind}`,data=>queue(kind,data.get("code")));
    }
  }

  function ensureSuggestions() {
    if (loadingNext || !get("watch-next").hidden) return;
    loadingNext = true;
    loadNext(item,player).catch(()=>{}).finally(()=>{loadingNext=false;});
  }

  async function poll() {
    if (!active()||polling) return;
    ensureSuggestions();
    polling = true;
    lastPoll = performance.now();
    try {
      const result = await api(endpoint);
      if (!active()) return;
      video = result.video;
      jobs = result.jobs;
      render();
    } catch (error) {
      if (active()) get("discovery-status").textContent = t(error.message);
    } finally { polling = false; }
  }
  get("discover-tracks").onclick = async event=>{
    const button = event.currentTarget;
    const status = get("discovery-status");
    status.textContent = t("downloadingTracks");
    button.disabled = true;
    try {
      offered = await api(`${endpoint}/discover`,"POST");
      if (active()) {
        status.textContent = "";
        await poll();
        if (active()) render();
      }
    } catch(error) { status.textContent=t(error.message); }
    finally {button.disabled=false;}
  };
  saved.onchange = event=>{
    const input = event.target;
    const button = input.closest(".saved-track").querySelector("[data-remove-track]");
    button.dataset.code = input.value;
    button.hidden = !input.value;
    if (input.name === "watchAudio") changeAudio(input.value);
    else { subtitle = input.value; setSubtitle(); }
  };
  saved.onclick = async event=>{
    const button = event.target.closest("[data-remove-track]");
    if (!button) return;
    button.disabled = true;
    try { await deleteTrack(button,true); }
    catch (error) { flash(t(error.message)); }
    finally { button.disabled = false; }
  };
  get("track-jobs").onclick = async event=>{
    const button=event.target.closest("[data-code]");
    if(!button) return;
    button.disabled=true;
    try {
      if (button.hasAttribute("data-remove-track")) await deleteTrack(button,false);
      else await queue(button.dataset.kind,button.dataset.code,true);
    }
    catch(error) { flash(t(error.message)); }
    finally {button.disabled=false;}
  };
  function toggleTheater() {
    const layout = get("watch-layout");
    const enabled = layout.classList.toggle("theater");
    app.querySelector(".shell").classList.toggle("cinema",enabled);
    localStorage.setItem("gridtube.theater",String(enabled));
    get("theater-mode").setAttribute("aria-pressed",String(enabled));
  }
  get("theater-mode").onclick = toggleTheater;
  get("expand-description").onclick = event=>{
    const expanded = description.classList.toggle("expanded");
    event.currentTarget.setAttribute("aria-expanded",String(expanded));
    event.currentTarget.textContent = t(expanded?"hideDescription":"showDescription");
  };

  function closeSettings(event) {
    if (settingsMenu.open && !settingsMenu.contains(event.target)) settingsMenu.open = false;
  }
  document.addEventListener("click",closeSettings);
  function activateShortcut(event) {
    if (event.key==="Escape" && settingsMenu.open && !modal.open) {
      settingsMenu.open=false;
      settingsButton.focus();
      event.preventDefault();
      return;
    }
    if (!active() || modal.open || event.altKey || event.ctrlKey || event.metaKey ||
        (event.target instanceof Element && event.target.closest("input, textarea, select, button, summary, a, [contenteditable]"))) return;
    const key = event.key.toLowerCase();
    const limits = {arrowleft:-5,arrowright:5,j:-10,l:10};
    if (key===" " || key==="k") {
      if (player.paused) player.play().catch(()=>{});
      else player.pause();
    } else if (key in limits && Number.isFinite(player.duration)) {
      player.currentTime = Math.min(player.duration,Math.max(0,player.currentTime+limits[key]));
    } else if (key==="m") {
      player.muted = !player.muted;
    } else if (key==="f") {
      if (document.fullscreenElement) document.exitFullscreen().catch(()=>{});
      else if (playerFrame.requestFullscreen) playerFrame.requestFullscreen().catch(()=>{});
      else if (player.webkitEnterFullscreen) player.webkitEnterFullscreen();
    } else if (key==="t") {
      toggleTheater();
    } else if (key==="c") {
      const choice = saved.querySelector("[name=watchSubtitles]");
      if (choice.options.length<2) return;
      choice.selectedIndex = subtitle ? 0 : 1;
      subtitle = choice.value;
      setSubtitle();
    } else return;
    event.preventDefault();
  }
  window.addEventListener("keydown",activateShortcut);
  render();
  ensureSuggestions();
  const timer = setInterval(()=>{
    const pending = jobs.some(job=>job.state==="queued" || job.state==="running");
    if (!document.hidden && (pending || settingsMenu.open || performance.now()-lastPoll>=15000)) poll();
  },2500);
  const onHide = ()=>update(player.ended?0:player.currentTime,true);
  window.addEventListener("pagehide",onHide);
  watchCleanup = ()=>{
    closed = true;
    clearInterval(timer);
    player.pause();
    onHide();
    window.removeEventListener("pagehide",onHide);
    window.removeEventListener("keydown",activateShortcut);
    document.removeEventListener("click",closeSettings);
  };
}

function organize(item) {
  if (!item) return;
  dialog(t("organize"),`<div class="dialog-body"><strong>${esc(item.title)}</strong>
    ${youtubeLink(item)}
    ${!watchPath()?btn("selectVideo",t(selectedVideos.has(item.id)?"deselectVideo":"selectVideo"),"list","",item.id):""}
    ${btn("markWatched",t(item.watched?"markUnwatched":"markWatched"),"eye","",item.id)}
    ${btn("ignoreVideo",t(item.ignored?"unignoreVideo":"ignoreVideo"),"eyeOff","",item.id)}
    <form id="move">${select("channel",t("move"),[...channels(t("unfiled")),["__new__",t("createChannelOption")]],item.channel_id||"")}
    <button>${t("move")}</button></form>
    <form id="add-to">${select("playlist",t("addTo"),[["",t("choosePlaylist")],...state.playlists.map(p=>[p.id,p.name]),["__new__",t("createPlaylistOption")]],"")}<button>${t("addTo")}</button></form>
    ${scope.startsWith("playlist:")?btn("unplaylist",t("removeFrom"),"","flat",item.id):""}
    ${btn("removeVideo",t("removeVideo"),"","flat",item.id)}</div>`);
  get("move").elements.channel.onchange=event=>{if(event.target.value==="__new__") editChannel(undefined,item.id);};
  get("add-to").elements.playlist.required=true;
  get("add-to").elements.playlist.onchange=event=>{if(event.target.value==="__new__") editPlaylist(undefined,item.id);};
  bind("move",async data=>{
    if (data.get("channel")==="__new__") return editChannel(undefined,item.id);
    await api(`/videos/${item.id}/move`,"POST",{channel:data.get("channel")});await finish();
  });
  bind("add-to",async data=>{
    if (data.get("playlist")==="__new__") return editPlaylist(undefined,item.id);
    await api(`/playlists/${data.get("playlist")}/videos/${item.id}`,"PUT");await finish();
  });
}

function confirmRemove(item) {
  if (!item) return;
  const removed = item.state==="removed";
  dialog(t("removeVideo"),`<form id="remove-video" class="dialog-body"><strong>${esc(item.title)}</strong>
    <p class="note">${t(removed?"deleteMediaNote":"removeVideoNote")}</p><p role="alert"></p>
    <div class="system-actions">${removed?"":`<button type="submit" value="keep" class="danger">${icon("trash")} ${t("keepMedia")}</button>`}
    <button type="submit" value="disk" class="danger danger-solid">${icon("trash")} ${t("deleteMedia")}</button></div></form>`);
  get("remove-video").onsubmit = async event=>{
    event.preventDefault();
    const form = event.currentTarget, alert = form.querySelector('[role="alert"]');
    const buttons = [...form.querySelectorAll("button")];
    buttons.forEach(button=>button.disabled=true);
    try {
      const disk = event.submitter?.value==="disk";
      await api(`/videos/${item.id}`,"DELETE",{disk});
      if (watchPath()) showLibrary("");
      await finish();
    } catch (error) {
      alert.textContent=t(error.message);
      buttons.forEach(button=>button.disabled=false);
      await refresh().catch(()=>{});
    }
  };
}

async function confirmBulkRemove(kind, id) {
  const collection=kind?await api(`/${kind}s/${id}/delete-preview`):null;
  const videos=collection?null:[...selectedVideos.values()];
  const ids=collection?collection.ids:videos.map(v=>v.id);
  if (!collection&&!ids.length) return;
  const title=collection?t(kind==="channel"?"deleteChannel":"deletePlaylist"):t("deleteSelected");
  dialog(title,`<form id="remove-bulk" class="dialog-body">
    ${collection?`<strong>${esc(collection.name)}</strong>`:""}
    <strong>${selectionCount(ids.length)}</strong>
    ${videos?`<ul class="deletion-titles">${videos.slice(0,8).map(v=>`<li>${esc(jobTitle(v))}</li>`).join("")}${videos.length>8?"<li>…</li>":""}</ul>`:""}
    <p class="note">${t(collection?"collectionDeleteHelp":"removeVideoNote")}</p>
    <p class="note">${t("sharedDeleteHelp")}</p>
    ${collection?.shared?`<strong>${t("sharedVideos")}: ${collection.shared}</strong>`:""}
    ${collection?`<p class="note">${t("collectionKeepHelp")}</p>`:""}
    <p role="status"></p><p role="alert"></p><div class="system-actions">
    <button type="submit" value="keep" class="danger">${icon("trash")} ${t(collection?"keepCollectionFiles":"keepMedia")}</button>
    <button type="submit" value="disk" class="danger danger-solid">${icon("trash")} ${t(collection?"deleteCollectionFiles":"deleteMedia")}</button></div></form>`);
  get("remove-bulk").onsubmit=async event=>{
    event.preventDefault();
    const form=event.currentTarget, buttons=[...modal.querySelectorAll("button")];
    const alert=form.querySelector('[role="alert"]'), status=form.querySelector('[role="status"]');
    const disk=event.submitter?.value==="disk";
    const preventClose=event=>event.preventDefault();
    buttons.forEach(button=>button.disabled=true);
    modal.addEventListener("cancel",preventClose);
    alert.textContent="";
    try {
      let result;
      do {
        status.textContent=t(result?.pending?"cancellingForDelete":"deletingVideos");
        if (result?.pending) await new Promise(resolve=>setTimeout(resolve,1200));
        result=await api(collection?`/${kind}s/${id}`:"/videos/delete",collection?"DELETE":"POST",{ids,disk});
      } while (result.pending);
      selectedVideos.clear();
      if (collection) showLibrary("");
      prior="";
      await finish();
    } catch (error) {
      status.textContent="";
      alert.textContent=t(error.message);
      await refresh().catch(()=>{});
    } finally {
      modal.removeEventListener("cancel",preventClose);
      buttons.forEach(button=>button.disabled=false);
    }
  };
}

async function act(action,value) {
  const item = watchVideo?.id===value ? watchVideo : displayed.find(v=>v.id===value);
  switch (action) {
    case "home":
      if (!watchPath()&&!scope) location.reload();
      else showLibrary("");
      break;
    case "menu": app.querySelector(".shell").classList.toggle("menu"); break;
    case "scope":
      showLibrary(value);break;
    case "back":
      if (history.state?.watchFromApp) history.back(); else showLibrary("");
      break;
    case "page": page=Number(value);rememberLibrary();await loadLibrary();break;
    case "libraryFilter":
      if (value==="all") libraryFilters.clear();
      else if (["new","today","week","unwatched","progress"].includes(value)) {
        if (libraryFilters.has(value)) libraryFilters.delete(value);else libraryFilters.add(value);
      }
      page=1;rememberLibrary();await loadLibrary();break;
    case "markWatched":
      await api(`/videos/${value}/watched`,"POST",{watched:!item.watched});
      item.watched=!item.watched;selectedVideos.delete(value);closeSelectionMenu();if(modal.open)modal.close();await refresh();break;
    case "ignoreVideo":
      await api(`/videos/${value}/ignored`,"POST",{ignored:!item.ignored});
      item.ignored=!item.ignored;selectedVideos.delete(value);closeSelectionMenu();if(modal.open)modal.close();await refresh();break;
    case "contentKind":
      if (!["videos","shorts","streams"].includes(value)) break;
      contentKind=value;page=1;rememberLibrary();await loadLibrary();break;
    case "catalogMore": catalog.limit+=60;await pollCatalog(catalog);break;
    case "catalogAll": catalog.limit=catalog.total;await pollCatalog(catalog);break;
    case "scan": {
      const session=catalog;
      const playlist=get("catalog-playlist").value;
      if (playlist) await api("/scans/playlists","POST",{source:value,playlist,force:true});
      else { await api("/scans","POST",{url:value}); await api("/scans/playlists","POST",{source:value,force:true}); }
      if (session!==catalog || !modal.open) break;
      session.limit=60;session.pending=true;await pollCatalog(session);break;
    }
    case "addChannel":
      simple("addChannel",field("channelUrl","","required type=url"),"startScan",async data=>{
        const {source}=await api("/scans","POST",{url:data.get("channelUrl")});openCatalog(source);
      });break;
    case "localChannel": editChannel();break;
    case "edit": editChannel(channelOf(value));break;
    case "profile":
      await api(`/channels/${value}/profile`,"POST",{force:true});
      pendingLocalizedProfile={key:`${value}:${locale}`,until:performance.now()+45000};
      flash(t("queuedState"));break;
    case "browse": {
      const channel = channelOf(value);
      try { await api(scanURL(channel.source)); }
      catch { await api("/scans","POST",{url:channel.source}); }
      openCatalog(channel.source,channel);break;
    }
    case "link": downloadByLink();break;
    case "settings": openSettings();break;
    case "settingsTab": settingsTab(value);break;
    case "updateDependency": await runMaintenance(false);break;
    case "restartDependency": await runMaintenance(true);break;
    case "addPlaylist": editPlaylist();break;
    case "editPlaylist": editPlaylist(state.playlists.find(p=>p.id===value));break;
    case "deleteChannel": await confirmBulkRemove("channel",value);break;
    case "deletePlaylist": await confirmBulkRemove("playlist",value);break;
    case "deleteSelected": await confirmBulkRemove();break;
    case "clearSelection": selectedVideos.clear();updateSelection();break;
    case "selectionMenu": {
      const anchor=get("library").querySelector(`[data-action="selectionMenu"][data-value="${CSS.escape(value)}"]`);
      if (anchor) openSelectionMenu(item,anchor);
      break;
    }
    case "selectVideo":
      if (item) {
        if (selectedVideos.has(item.id)) selectedVideos.delete(item.id);
        else selectedVideos.set(item.id,item);
        lastSelectedVideo=item.id;
        updateSelection();
      }
      closeSelectionMenu(true);
      if (modal.open) modal.close();
      break;
    case "unplaylist": await api(`/playlists/${scope.slice(9)}/videos/${value}`,"DELETE");await finish();break;
    case "watch": openWatch(value);break;
    case "organize": organize(item);break;
    case "removeVideo": confirmRemove(item);break;
    case "restoreVideo": await api(`/videos/${value}/restore`,"POST",{});await refresh();break;
    case "editRetry": editRetry(item);break;
    case "retry": await api(`/videos/${value}/retry`,"POST");await refresh();break;
    case "cancelDownload": {
      const button = document.querySelector(`[data-action="cancelDownload"][data-value="${CSS.escape(value)}"]`);
      if (button) button.disabled = true;
      try {
        const result = await api(`/downloads/${value}`,"DELETE",{});
        flash(t(result.cancelling?"cancelling":"download_cancelled"));
        await refresh();
      } catch (error) {
        await refresh();
        throw error;
      } finally { if (button) button.disabled = false; }
      break;
    }
    case "seek": get("player").currentTime=Number(value);break;
    case "close": modal.close();break;
  }
}
document.addEventListener("click",event=>{
  const checkbox=event.target.closest("[data-select-video]");
  if (checkbox) {
    const id=checkbox.dataset.selectVideo, checked=checkbox.checked;
    const index=displayed.findIndex(v=>v.id===id), previous=displayed.findIndex(v=>v.id===lastSelectedVideo);
    const videos=event.shiftKey&&previous>=0?displayed.slice(Math.min(index,previous),Math.max(index,previous)+1):[displayed[index]];
    videos.filter(Boolean).forEach(v=>checked?selectedVideos.set(v.id,v):selectedVideos.delete(v.id));
    lastSelectedVideo=id;
    updateSelection();
    return;
  }
  const target = event.target.closest("[data-action]");
  if (!target) return;
  if (target.matches("a")) {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button!==0) return;
    event.preventDefault();
  }
  act(target.dataset.action,target.dataset.value||"").catch(error=>flash(t(error.message)));
});
document.addEventListener("change",event=>{
  if (event.target.id!=="select-page") return;
  displayed.forEach(v=>event.target.checked?selectedVideos.set(v.id,v):selectedVideos.delete(v.id));
  updateSelection();
});
document.addEventListener("contextmenu",event=>{
  if (modal.open||event.target.closest("input,textarea,select")) return;
  const card=event.target.closest("#library [data-video-id]");
  const item=card&&displayed.find(video=>video.id===card.dataset.videoId);
  if (!item) return;
  event.preventDefault();
  const anchor=card.querySelector('[data-action="organize"],[data-action="selectionMenu"]');
  const point=event.clientX||event.clientY?{x:event.clientX,y:event.clientY}:null;
  openSelectionMenu(item,anchor,point);
});
document.addEventListener("pointerdown",event=>{
  if (!event.target.closest("#video-context-menu")) closeSelectionMenu();
});
document.addEventListener("keydown",event=>{
  if (!get("video-context-menu")) return;
  if (event.key==="Escape") { event.preventDefault();closeSelectionMenu(true); }
  else if (event.key==="Tab") closeSelectionMenu(true);
});
window.addEventListener("scroll",()=>closeSelectionMenu(),true);
window.addEventListener("resize",()=>closeSelectionMenu());
window.addEventListener("popstate",()=>showLocation(false,true));
document.addEventListener("visibilitychange",()=>backgroundRefresh(true));
document.addEventListener("input",event=>{
  if (event.target.matches('[name="collectionColor"]')) {
    event.target.closest(".collection-picker").style.setProperty("--collection-color",event.target.value);
  }
});
shell();
refresh().catch(error=>flash(t(error.message)));
setInterval(()=>{if(!document.hidden&&(catalog?.pending||catalog?.autoPoll)&&modal.open) pollCatalog(catalog);},1600);
setInterval(pollSystem,1800);
setInterval(backgroundRefresh,2000);
