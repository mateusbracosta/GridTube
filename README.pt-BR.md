# GridTube

[English](README.md) · Português do Brasil

[Versão mais recente](https://github.com/mateusbracosta/GridTube/releases/latest)

Biblioteca de vídeos auto-hospedada para adquirir conteúdo quando há internet e consultar o acervo pela rede local.

Clique no logo GridTube para voltar à biblioteca de outra tela. Se já estiver na biblioteca, o clique recarrega a página. O símbolo vermelho de grade e reprodução aparece no app e no favicon do navegador.

Biblioteca, canais, Avulsos, playlists, Assistidos e Ignorados têm as abas **Vídeos**, **Shorts** e **Lives**, com Vídeos como padrão. Voltar do player preserva aba, página e filtros. O seletor **Mais recentes primeiro / Mais antigos primeiro** usa a publicação, com fallback à captura, e salva a escolha neste navegador. As abas filtram a exibição sem alterar vínculos de playlists ou arquivos.

Em cada aba há **Todos, Novos, Hoje, Esta semana, Não assistidos e Em andamento**. Os filtros podem ser combinados para refinar o resultado; Todos limpa os demais. Hoje/Esta semana usam a publicação e a data local do navegador, com semana iniciando na segunda-feira. Em andamento reúne downloads aguardando/ativos e vídeos parcialmente assistidos. Todos é o padrão e mantém os assistidos visíveis.

Ações do canal, abas, filtros e seletor de ordem usam controles compactos de 32 pixels, cantos consistentes e ícones de traço pequenos, com seleção discreta.

Downloads selecionados aparecem imediatamente como cards no canal e na biblioteca, com título, prévia da capa, estado da fila e progresso medido. Erros aparecem no card e em Downloads, com repetir e lixeira para cancelar. A prévia dos pendentes vem do YouTube quando há internet; vídeos concluídos usam capas locais salvas. Não é inventada porcentagem quando a fase não permite medi-la.

No menu do vídeo, use **Marcar como assistido / Marcar como não assistido**. Concluir a reprodução também marca como assistido. A aba lateral **Assistidos** reúne esses vídeos. O antigo menu Continuar assistindo passou a **Ignorados**: **Ignorar vídeo** oculta um vídeo salvo das listas comuns e sugestões, preservando arquivos, progresso, canal e vínculos com playlists. Em Ignorados, **Voltar à biblioteca** desfaz a ação. Links diretos e exportações continuam disponíveis.

Quando o acompanhamento de um canal baixa automaticamente um vídeo novo, o card mostra **Novo** até você abri-lo. Downloads manuais e vídeos já existentes ficam sem o selo. Abrir remove o selo de forma persistente para esta biblioteca compartilhada, mesmo sem reproduzir. **Duração do selo Novo (dias)** tem padrão **Até abrir o vídeo** (vazio ou 0); um número personalizado faz o selo sumir antes se o prazo vencer. Marcar como assistido também remove Novo.

Em **Configurações → Downloads**, **Shorts** e **Lives** controlam todas as novas capturas: seleção manual, link, nova tentativa e acompanhamento automático. Cada canal pode substituir a escolha global. **Não baixar** bloqueia aquele tipo sem excluir vídeos, legendas, áudios ou progresso já salvos. **Somente Shorts** também bloqueia vídeos comuns e lives. Itens aguardando na fila são conferidos com as preferências atuais antes de iniciar; os bloqueados mostram o motivo e podem ser tentados novamente após alterar a preferência. Transferências já iniciadas não são canceladas à força. As regras de download são independentes das opções de exibição em Interface.

Os dois seletores oferecem **Permitir / Não baixar / Somente**, com o nome do tipo explícito. **Somente Lives** baixa apenas gravações de lives. Se os dois tipos estiverem em Somente, permite a união: Shorts e Lives, sem vídeos comuns.

**Duração máxima do vídeo (minutos)** começa em **Sem limite** (vazio ou 0) e aceita um número inteiro personalizado. O canal pode herdar o teto global ou usar 0 para não limitar. **Excluir automaticamente do disco após (dias)** começa em **Nunca** (vazio ou 0). Um valor personalizado apaga definitivamente bundles vencidos, arquivos auxiliares e seus registros no catálogo, inclusive vídeos ignorados. O prazo começa na conclusão do download; acervos antigos sem esse horário usam a data da captura. A conferência é periódica, em lotes, e respeita arquivos em exportação/preparação para reprodução. Essa configuração é global; atividades e falhas aparecem em Sistema.

O teto de duração também filtra o catálogo de seleção do canal, suas contagens e Selecionar todos os resultados. Com teto ativo, candidatos sem duração confirmada ficam fora até ser possível confirmá-la. Vídeos já salvos continuam acessíveis. Os campos de download têm controles alinhados; explicações adicionais podem ser abertas em Ajuda sobre downloads.

Em **Configurações → Interface**, **Nunca exibir Shorts** e **Nunca exibir lives** ocultam suas abas e conteúdos na biblioteca, canais, playlists, Avulsos, Assistidos, Ignorados e sugestões. As escolhas são salvas neste navegador e não afetam downloads ou arquivos. As filas de downloads e removidos continuam visíveis para gerenciamento.

## Rodar no Docker

Com Git, Docker Engine e Compose instalados, clone o repositório e inicie o GridTube.

~~~sh
git clone https://github.com/mateusbracosta/GridTube.git
cd GridTube
docker compose up -d --build
~~~

Abra [GridTube](http://localhost:3987). A porta é publicada no loopback por padrão. Para servir outros aparelhos da sua rede de confiança, configure `GRIDTUBE_BIND` com o IP LAN do host. O app é de uso local e esta versão opera sem contas de usuário.

### Escolher o HD e a pasta dos vídeos

Antes de iniciar o GridTube, crie um arquivo `.env` ao lado do `compose.yaml`. Escolha a linha do seu sistema e substitua o endereço pela pasta no computador que roda o Docker.

~~~dotenv
# Windows
GRIDTUBE_ARCHIVE_PATH="D:/Geral/GridTube/Videos"
# Linux ou Orange Pi (use esta linha no Linux)
# GRIDTUBE_ARCHIVE_PATH=/mnt/hd/GridTube/Videos
~~~

Os vídeos ficam em `library/` dentro da pasta escolhida. Downloads em andamento e cache ficam em `work/`, no mesmo HD. O caminho padrão do acervo é `./archive`. Para migrar um acervo existente, rode `docker compose stop`, copie o conteúdo da pasta atual do acervo para a nova, ajuste o `.env` e rode `docker compose up -d --wait`.

### Orange Pi e outros servidores ARM64

Use o mesmo comando do Compose numa instalação Linux de 64 bits com Docker. Na Orange Pi Zero 3, confira se `uname -m` retorna `aarch64`. A placa pode servir a biblioteca pela rede local. Quem decodifica o vídeo é o navegador, e a compatibilidade depende dos codecs que o aparelho usado para assistir suporta.

Se o espaço for limitado, defina `GRIDTUBE_PLAYBACK_CACHE_MIB=512` no `.env`. O padrão é 4096 MiB. Esse cache guarda as variantes temporárias de reprodução com áudio alternativo. A variante sendo preparada fica disponível mesmo quando supera o limite. Os arquivos originais ficam na biblioteca. Um disco USB para o acervo libera espaço no cartão do sistema.

## Atualizar a instalação

Depois de atualizar o código, execute na mesma pasta:

~~~sh
docker compose up -d --build --wait
~~~

O Compose recria o container quando a configuração ou a imagem muda. A biblioteca fica na pasta do acervo. O banco e as configurações da aplicação ficam em `data/`.

## Uso

- **Adicionar canal** consulta vídeos, Shorts e transmissões arquivadas. Em **Filtrar por playlist**, abra uma playlist do YouTube e selecione vídeos dela. **Carregar mais** e **Carregar todos** ampliam a lista. **Selecionar todos os resultados** cobre o filtro atual inteiro, inclusive itens ainda fora da lista visível. A seleção continua ao trocar de filtro ou playlist. **Título deve conter** define uma regra do canal, usada tanto na escolha manual quanto no acompanhamento automático. Os títulos são comparados sem distinção de caixa ou acentos.
- **Preferências globais** são o padrão. Em cada canal, escolha modo de download, limite de resolução, políticas de Shorts/Lives, áudio e legendas. As políticas valem para todas as novas capturas, inclusive seleção manual e links. Ao ativar acompanhamento, a primeira consulta registra a referência sem enfileirar o histórico. O acompanhamento consulta até 30 itens recentes de cada aba por ciclo, a cada 15 minutos.
- **Baixar por link** pode guardar em um canal ou em **Avulsos**. Em **Opções para este vídeo**, escolha modo de download, limite de resolução, áudio e legendas. Os campos deixados em **Usar padrão** herdam as preferências do canal ou os padrões globais. Em **Downloads**, use **Editar opções e tentar novamente** para ajustar uma tentativa que falhou. **Tentar novamente** reutiliza as escolhas individuais já feitas. Abra o menu de organização de um vídeo para mover a pasta para outro canal, criar um canal local e já mover o vídeo, ou criar/adicionar a uma playlist. Uma playlist aponta para o vídeo da biblioteca, com uma única cópia física.
- **PT-BR / EN** alterna o idioma da interface naquele navegador. O player local oferece legendas, capítulos quando disponíveis e retomada de posição.

Em canais locais, escolha **Ícone e cor** ao criar ou editar. Nas playlists criadas no app, use **Personalizar** no cabeçalho. As escolhas aparecem na barra lateral e nos cabeçalhos e são incluídas no backup do catálogo.

Clique com o botão direito no vídeo e escolha **Selecionar vídeo**, ou use o menu de três pontos, para começar a selecionar itens. A barra e as caixas de seleção aparecem depois do primeiro item marcado e somem ao desmarcar o último ou limpar a seleção. **Selecionar esta página** marca os itens visíveis; a seleção é mantida ao trocar de página. Shift + clique seleciona um intervalo na página atual. Trocar de coleção ou busca limpa a seleção. **Excluir selecionados** oferece manter os arquivos ou apagá-los do disco.

Use **Editar canal → Excluir canal e vídeos** para remover um canal. Nas playlists, **Excluir playlist e vídeos** fica no cabeçalho. A confirmação inclui todos os itens da coleção, de todas as páginas, e avisa sobre vídeos compartilhados com outras playlists. Excluir os vídeos de uma playlist afeta os mesmos vídeos na biblioteca inteira. Mantendo os arquivos, os vídeos ficam em **Removidos**; depois de excluir um canal, os vídeos restaurados ficam em **Avulsos**. Downloads em andamento são interrompidos antes de apagar seus arquivos. A coleção excluída não é preservada.

Os perfis de canais priorizam o idioma escolhido no app e a preferência regional do navegador. Na primeira visita, a interface usa um idioma compatível do navegador; uma escolha PT-BR/EN já salva tem prioridade. Ao abrir um canal, o app consulta o perfil no idioma escolhido se essa versão ainda não estiver salva. As versões ficam disponíveis offline, sem uma sobrescrever a outra ao trocar de idioma. O YouTube pode devolver o texto original quando não houver tradução. Nomes e descrições personalizados permanecem como foram escritos.

Em **Organizar vídeo**, as listas de canais e playlists incluem **Criar novo canal…** e **Criar nova playlist…**. Salvar o formulário de criação move ou adiciona o vídeo automaticamente. Ações de exclusão usam vermelho e lixeira; confirmações para apagar do disco têm botão vermelho preenchido.

Em **Downloads**, links avulsos exibem o título assim que o YouTube o disponibiliza. Enquanto o nome estiver indisponível, a fila exibe o identificador do vídeo. A porcentagem acompanha a fase atual. A transferência de vídeo e áudio usa os bytes baixados, e a montagem usa a posição processada que o FFmpeg informa. A interface marca estimativas e usa uma barra indeterminada quando a etapa não tem uma medida de progresso.

Use **Cancelar** para tirar um item da fila ou interromper um download e sua montagem. O item em andamento mostra **Cancelando…** enquanto encerra o processo e limpa os temporários. Uma consulta de rede em curso pode precisar terminar antes do cancelamento ser concluído. Use **Remover tentativa** para limpar uma falha da lista. Você pode adicionar o vídeo novamente depois.

Em **Organizar vídeo → Excluir vídeo**, escolha **Remover da biblioteca** para manter os arquivos e restaurar o vídeo depois em **Removidos**. **Excluir também do disco** apaga a pasta daquele vídeo e seus arquivos auxiliares. Para excluir no disco, o Docker precisa de acesso de escrita à montagem do acervo.

### Modo de download

- **Resolução máxima** vale para os dois modos. Pode ser definida globalmente, por canal ou por vídeo. Alterar apenas a resolução mantém o modo herdado. **Melhor disponível (sem limite)** remove o teto de resolução.
- **Compacto** é o padrão. Dentro do limite configurado, o app encontra a melhor resolução e taxa de quadros disponíveis e prioriza o menor tamanho estimado entre as variantes comparáveis.
- **Qualidade original** seleciona a maior resolução e taxa de quadros dentro do mesmo limite e segue a preferência de qualidade da origem nos formatos equivalentes. O app copia a imagem e o áudio fornecidos pelo YouTube em ambos os modos. A imagem corresponde à versão publicada na plataforma.

A partir da 0.7.17, o limite também é respeitado em Qualidade original. Para baixar sem teto de resolução, escolha **Melhor disponível (sem limite)**. As escolhas são aplicadas às próximas capturas; os arquivos já salvos permanecem como foram baixados.

## Assistir

Cada vídeo abre em uma página com endereço próprio, player, canal, data, descrição e sugestões do acervo. **Voltar** recupera a seção anterior quando você veio pela interface. O **Modo cinema** amplia o player e compacta a barra lateral em ícones no desktop. O logo abre a Biblioteca. A escolha fica neste navegador.

Use **Abrir no YouTube** na página do vídeo ou no menu de três pontos do cartão para consultar a publicação na origem.

Com foco fora dos campos e botões, **K** ou **Espaço** pausa e retoma. **←/→** voltam ou avançam 5 segundos, e **J/L**, 10 segundos. **M** alterna som, **F** alterna tela cheia, **C** alterna legenda e **T** alterna modo cinema.

## Áudio, dublagem e legendas

Na engrenagem **Áudio e legendas**, dentro do vídeo, use **Buscar mais idiomas** para ver as faixas disponíveis na origem e baixar áudios ou legendas adicionais. Depois de salvas, **Faixa de áudio** e **Legenda em exibição** alternam entre as opções locais. Se uma legenda falhar, o vídeo permanece disponível e a faixa pode ser tentada novamente. A dublagem depende das faixas que o YouTube oferece.

A lixeira ao lado de uma faixa adicional selecionada apaga seu arquivo do HD. Ao lado de uma tentativa com erro, a lixeira limpa a tentativa. O áudio que faz parte do arquivo de vídeo continua disponível.

O player centraliza as legendas na parte inferior. Os arquivos de legenda exportados preservam o posicionamento de origem.

Canais conectados ao YouTube têm foto, capa e descrição armazenadas localmente. Em vídeos avulsos, o player usa o nome e a foto do canal obtidos pelo identificador oficial da origem. Para ligar um canal criado no app a uma origem, informe o link em **Editar canal**.

Consulte a [arquitetura e operação](ARQUITETURA.md) para ver fluxos, persistência, rotas e recuperação.

## Arquivos e Jellyfin

~~~text
archive/
  library/
    Avulsos/
      Título [ID de origem]/
        Título.webm
        Título.pt-BR.vtt
        Título.en.m4a
        Título-thumb.jpg
        video.json
    Nome do canal [ID local]/
      Título [ID de origem]/
        Título.mp4
  work/
data/
  library.sqlite
~~~

Cada captura publica um MP4 ou WebM com os fluxos baixados da origem. `video.json` registra o modo, os codecs e a resolução. Miniatura e legendas acompanham o vídeo quando disponíveis. A reprodução direta depende do suporte ao formato no navegador ou cliente Jellyfin. O nome da pasta do canal é definido na criação e permanece estável quando o nome exibido é editado. Os arquivos temporários ficam em `archive/work`, fora da biblioteca.

O GridTube salva a miniatura do YouTube localmente quando disponível. Se a capa original estiver indisponível, usa uma imagem gerada do vídeo. A posição assistida aparece na barra do cartão e é usada para retomar a reprodução.

Para levar só a mídia, copie `library/` dentro da pasta do acervo ou as pastas desejadas. Para usar com Jellyfin, monte essa `library/` em modo somente leitura e aponte uma biblioteca do tipo **Vídeos domésticos e fotos** para esse caminho. O app e o Jellyfin mantêm catálogos independentes, incluindo playlists e progresso. Faça o rescan do Jellyfin depois de mover arquivos.

Cada playlist tem um `playlist.m3u8` em UTF-8 na pasta `Playlists/` do acervo. Copie `library/` e `Playlists/` juntas para manter os caminhos relativos. Para levar só uma playlist, use **Exportar playlist em ZIP** no cabeçalho dela. O ZIP inclui a lista, os vídeos e os arquivos auxiliares disponíveis, com caminhos relativos à pasta extraída.

[Jellyfin e visualização por pastas](https://jellyfin.org/posts/jellyfin-release-12.0/) · [MP4 e convenções de arquivos auxiliares](https://jellyfin.org/docs/general/server/media/music-videos/)

### Acessar o acervo pelo Nextcloud

Aponte o armazenamento externo local do Nextcloud para a subpasta `library/` do acervo e dê à montagem o nome **Videos**. Downloads em andamento e cache ficam em `work/`, fora dessa montagem. Para baixar uma cópia pelo Nextcloud, basta baixar o arquivo ou a pasta desejada.

Depois de excluir um vídeo ou mover sua pasta pelo Nextcloud, abra **Configurações → Sistema → Conferir arquivos do acervo** no GridTube. Para mover entre canais que já têm pasta no acervo, mova a pasta inteira do vídeo, mantendo `[ID]` no nome e o arquivo `video.json` junto da mídia. Mover só o MP4 ou WebM para fora da pasta original fará o vídeo aparecer em **Removidos**.

O GridTube atualiza os caminhos e as playlists após reconhecer uma movimentação. Quando a mídia desaparece, guarda o progresso e as associações em **Removidos**. Para recuperar, devolva o arquivo à pasta original e confira o acervo novamente, ou use **Baixar novamente**. A conferência atualiza o catálogo sem apagar arquivos no HD.

## Levar para um ambiente off-grid

Com o serviço parado, copie `data/` e a pasta do acervo para restaurar o estado completo. Guarde também `compose.yaml` e a imagem do app. No novo host, ajuste `GRIDTUBE_ARCHIVE_PATH` para apontar para a cópia do acervo. Depois de construir para a arquitetura do outro host, exporte e importe a imagem conforme abaixo.

~~~sh
docker save -o gridtube-image.tar gridtube:0.7.20
docker load -i gridtube-image.tar
docker compose up -d --no-build --pull never
~~~

A interface, a busca, a organização e o player usam recursos locais. A leitura de um catálogo remoto, o acompanhamento de canais e a captura usam internet.

## Manutenção do yt-dlp

Em **Configurações → Sistema**, use **Atualizar yt-dlp** para consultar a versão estável do PyPI. O GridTube testa a instalação e mostra a versão pronta. No Docker, **Reiniciar e aplicar** ativa a versão baixada. O reinício interrompe a reprodução e a fila retoma os trabalhos pendentes. A atualização fica no volume `data/`. Consulte o **Registro de atividade** para ver resultados e falhas recentes.

## Backup, restauração e limpeza

Em **Configurações → Sistema**, exporte `gridtube-backup.jsonl` para levar os canais, playlists, catálogo, fila, progresso e preferências. **Restaurar backup** abre a seleção do arquivo. Depois de escolhido, o GridTube valida o backup, aplica os dados ao reiniciar e verifica a integridade do banco e os registros restaurados. A tela informa **Backup restaurado e verificado** quando a conferência termina.

Para migrar, copie a pasta do acervo para o novo host antes de restaurar. Vídeos com arquivos ausentes ficam em **Removidos** e podem ser restaurados depois de copiar os arquivos.

Em **Limpar dados do app**, digite `RESET` para apagar os dados do app e manter `library/`. Para apagar também os vídeos e os arquivos auxiliares dessa biblioteca, marque a caixa de exclusão no HD e digite `RESET MEDIA`. A restauração e a limpeza entram em vigor na reinicialização do serviço.
