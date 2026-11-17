# GridTube

[English](README.md) · Português do Brasil

Biblioteca de vídeos auto-hospedada para adquirir conteúdo quando há internet e consultar o acervo pela rede local.

## Rodar no Docker

Com o Docker Engine e o Compose ativos, execute na pasta do projeto.

~~~sh
docker compose up -d --build
~~~

Abra [GridTube](http://localhost:3987). A porta é publicada no loopback por padrão. Para servir outros aparelhos da sua rede de confiança, configure `GRIDTUBE_BIND` com o IP LAN do host. O app é de uso local e esta versão opera sem contas de usuário.

### Orange Pi e outros servidores ARM64

Use o mesmo comando do Compose numa instalação Linux de 64 bits com Docker. Na Orange Pi Zero 3, confira se `uname -m` retorna `aarch64`. A placa pode servir a biblioteca pela rede local. Quem decodifica o vídeo é o navegador, e a compatibilidade depende dos codecs que o aparelho usado para assistir suporta.

Se o espaço for limitado, defina `GRIDTUBE_PLAYBACK_CACHE_MIB=512` no `.env`. O padrão é 4096 MiB. Esse cache guarda as variantes temporárias de reprodução com áudio alternativo. A variante sendo preparada fica disponível mesmo quando supera o limite. Os arquivos originais ficam na biblioteca. Um disco USB para o acervo libera espaço no cartão do sistema.

## Atualizar a instalação

Depois de atualizar o código, execute na mesma pasta:

~~~sh
docker compose up -d --build --wait
~~~

O Compose recria o container quando a imagem muda. A biblioteca, o banco e as configurações da aplicação ficam nas pastas montadas `archive/` e `data/`.

## Uso

- **Adicionar canal** consulta vídeos, Shorts e transmissões arquivadas. Em **Filtrar por playlist**, abra uma playlist do YouTube e selecione vídeos dela. **Carregar mais** e **Carregar todos** ampliam a lista. **Selecionar todos os resultados** cobre o filtro atual inteiro, inclusive itens ainda fora da lista visível. A seleção continua ao trocar de filtro ou playlist. **Título deve conter** define uma regra do canal, usada tanto na escolha manual quanto no acompanhamento automático. Os títulos são comparados sem distinção de caixa ou acentos.
- **Preferências globais** são o padrão. Em cada canal, escolha modo de download, limite de resolução no modo compacto, política de Shorts, áudio e legendas. A política de Shorts vale para novas capturas automáticas, e a seleção manual sempre admite itens marcados. Ao ativar acompanhamento, a primeira consulta registra a referência sem enfileirar o histórico. O acompanhamento consulta até 30 itens recentes de cada aba por ciclo, a cada 15 minutos.
- **Baixar por link** pode guardar em um canal ou em **Avulsos**. Em **Opções para este vídeo**, escolha modo de download, limite de resolução no modo compacto, áudio e legendas. Os campos deixados em **Usar padrão** herdam as preferências do canal ou os padrões globais. Em **Downloads**, use **Editar opções e tentar novamente** para ajustar uma tentativa que falhou. **Tentar novamente** reutiliza as escolhas individuais já feitas. Abra o menu de organização de um vídeo para mover a pasta para outro canal, criar um canal local e já mover o vídeo, ou criar/adicionar a uma playlist. Uma playlist aponta para o vídeo da biblioteca, com uma única cópia física.
- **PT-BR / EN** alterna o idioma da interface naquele navegador. O player local oferece legendas, capítulos quando disponíveis e retomada de posição.

Em **Organizar vídeo → Excluir vídeo**, escolha **Remover da biblioteca** para manter os arquivos e restaurar o vídeo depois em **Removidos**. **Excluir também do disco** apaga a pasta daquele vídeo e seus arquivos auxiliares. Para excluir no disco, o Docker precisa de acesso de escrita à montagem do acervo.

### Modo de download

- **Compacto** é o padrão. Dentro do limite configurado, o app encontra a melhor resolução e taxa de quadros disponíveis e prioriza o menor tamanho estimado entre as variantes comparáveis. A opção de resolução **Melhor disponível** mantém a seleção compacta sem fixar um teto.
- **Qualidade original (máxima disponível)** seleciona a maior resolução e taxa de quadros disponíveis com a faixa de áudio escolhida. O app copia a imagem e o áudio fornecidos pelo YouTube em ambos os modos. A imagem corresponde à versão publicada na plataforma.

## Assistir

Cada vídeo abre em uma página com endereço próprio, player, canal, data, descrição e sugestões do acervo. **Voltar** recupera a seção anterior quando você veio pela interface. O **Modo cinema** amplia o player e compacta a barra lateral em ícones no desktop. O logo abre a Biblioteca. A escolha fica neste navegador.

Com foco fora dos campos e botões, **K** ou **Espaço** pausa e retoma. **←/→** voltam ou avançam 5 segundos, e **J/L**, 10 segundos. **M** alterna som, **F** alterna tela cheia, **C** alterna legenda e **T** alterna modo cinema.

## Áudio, dublagem e legendas

Na engrenagem **Áudio e legendas**, dentro do vídeo, use **Buscar mais idiomas** para ver as faixas disponíveis na origem e baixar áudios ou legendas adicionais. Depois de salvas, **Faixa de áudio** e **Legenda em exibição** alternam entre as opções locais. Se uma legenda falhar, o vídeo permanece disponível e a faixa pode ser tentada novamente. A dublagem depende das faixas que o YouTube oferece.

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

Para levar só a mídia, copie `archive/library` ou as pastas desejadas. Para usar com Jellyfin, monte `archive/library` em modo somente leitura e aponte uma biblioteca do tipo **Vídeos domésticos e fotos** para esse caminho. O app e o Jellyfin mantêm catálogos independentes, incluindo playlists e progresso. Faça o rescan do Jellyfin depois de mover arquivos.

[Jellyfin e visualização por pastas](https://jellyfin.org/posts/jellyfin-release-12.0/) · [MP4 e convenções de arquivos auxiliares](https://jellyfin.org/docs/general/server/media/music-videos/)

## Levar para um ambiente off-grid

Com o serviço parado, copie `data/` e `archive/library/` para restaurar o estado completo. Guarde também `compose.yaml` e a imagem do app. Depois de construir para a arquitetura do outro host, exporte e importe a imagem conforme abaixo.

~~~sh
docker save -o gridtube-0.7.tar gridtube:0.7
docker load -i gridtube-0.7.tar
docker compose up -d --no-build --pull never
~~~

A interface, a busca, a organização e o player usam recursos locais. A leitura de um catálogo remoto, o acompanhamento de canais e a captura usam internet.

## Manutenção do yt-dlp

Em **Configurações → Sistema**, use **Atualizar yt-dlp** para consultar a versão estável do PyPI. O GridTube testa a instalação e mostra a versão pronta. No Docker, **Reiniciar e aplicar** ativa a versão baixada. O reinício interrompe a reprodução e a fila retoma os trabalhos pendentes. A atualização fica no volume `data/`. Consulte o **Registro de atividade** para ver resultados e falhas recentes.


GridTube é um projeto independente inspirado pelo [UnTube](https://github.com/tomfriart/untube).
