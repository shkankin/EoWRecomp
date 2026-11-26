# Status

Atualizado: 2026-11-25 (sessão 10: versão 1.1.0 do jogo, Bazzite / AppImage, Async por padrão — ver abaixo). Antes: 2026-11-24 (sessão 9: Windows / RTX 3070). Antes: 2026-11-20 (sessão 8: Linux x86-64 / RX 7600 RADV — `v0.5.0`: pré-compilação de shaders no launcher (`shader_prep`), padrão `SHADER_SYNC`, suporte ao RecompLauncher e correção da iluminação/IBL dinâmica de cubemap).

## Sessão 10 (2026-11-25): versão 1.1.0 do jogo; Linux (Bazzite) pelo AppImage; Async por padrão

O usuário vai jogar no Bazzite (Fedora Atomic, Radeon 890M, aberto pela Steam / Gamescope) e pediu a versão 1.1.0
(o `.nsp` do update ao lado do `.xci`, como em outros recomps).

### Versão 1.1.0 (update v196608, `main` build id `9f221e1afa65ba54`)
- **Pacote (`runtime/nxpkg.c`, `nx_setup_update`)**: o ExeFS do update substitui o da base; o RomFS do update é lido
  sobre o da base sem cópia: IndirectStorage (BucketTree {virt, phys, storage}: storage 0 = seção RomFS do programa
  base, 1 = dados do patch) e AesCtrCounterExtendedStorage (AES-CTR com a geração do contador por faixa), no nível da
  seção, abaixo do IVFC e do CompressedStorage descritos pelo fs header do patch. `romfs.src` ganha `patch_*`,
  `indirect`, `ctrex`. Verificado: `tools/test_nxpkg.c --update` confere 3025 blocos amostrados contra a árvore de
  hashes (IVFC) da própria seção: 2944 vindos da base, 81 do update, todos SHA-256 iguais.
- **Launcher**: os pacotes menores ao lado do jogo são tentados como update (outro título / DLC: ignorados); versões
  por build id em `runtime/paths.c` (`rt_game_version`); a tela inicial mostra "Nintendo Switch · v1.1.0".
- **Módulos de SDK mais novo**: `sdk`, `subsdk0`, `subsdk1` só têm `DT_GNU_HASH` (sem `DT_HASH`) e os quatro usam
  `DT_RELR`. Loader e `tools/nso.py` contavam 0 símbolos ("nn::init::Start not found", 4435 imports em stubs) e não
  aplicavam as relocações RELR (o gen.py perdia ~449 mil inícios de função). Corrigido nos dois; 1.0.0 igual.
- **hid**: o SDK novo lê `GetNpadJoyHoldType` da memória compartilhada (npad condition em `0x3E200`, revisão 5 do
  `ActivateNpadWithRevision`) e abortava com hid 710; a condição agora é escrita (e `SetNpadJoyHoldType` é seguido).
- **am**: `IApplicationFunctions` 210 devolve o evento que `nn::oe::GetOperationMode` espera (sem ele, o jogo ficava
  em loop no handle 0 no boot). `GetDisplayVersion` responde a versão real.
- **Áudio (sem som na 1.1.0)**: o SDK novo usa o audio renderer REV15, com biquads em float: `VoiceInParameter`
  passa de 0x170 a 0x188 bytes (cada filtro 0xC -> 0x18; o resto 0x18 adiante). Lido de 0x170 em 0x170, todas as
  vozes menos a primeira eram lixo: silêncio (usuário, Bazzite / Legion Go 2). O tamanho agora vem da seção. Medido com
  `EOWRECOMP_AUDIO_WAV` (60 s do boot): antes pico 0,000; depois pico 0,62 e RMS a cada 5 s a 0,002 do da 1.0.0.
- **Diagnóstico**: `svcBreak` e espera em handle inválido mostram a cadeia de chamadas do jogo com símbolos (achou os
  dois problemas acima).
- **Resultado (Windows / RTX 3070, Vulkan)**: setup pelo launcher com XCI + update + keys, código do jogo gerado em
  24 min, boot até o prólogo a 60 fps; os saves do usuário (feitos na 1.0.0) listados e carregados, Zelda andando
  na cela do subterrâneo do castelo, 60 fps, sem erros no log.
- Não testado ainda: Linux com a 1.1.0 (mesmo código; o AppImage novo vai ao usuário), jogo longo na 1.1.0, se um
  save gravado na 1.1.0 abre na 1.0.0 (provavelmente não: o usuário deve manter cópia dos saves).

### Linux / Bazzite (AppImage)
- O jogo parava no boot com `FATAL: no usable system font substitute`: o Bazzite não tem DejaVu Sans e o AppImage não
  levava a cópia que `runtime/hle/pl.c` procura ao lado do executável. Agora leva (`tools/linux/package.sh`).
- No Bazzite com o modo Sync (o padrão), quedas a 1-3 fps; com Async "muito melhor" (usuário).
- O AppImage é gerado no GitHub (`.github/workflows/build-linux.yml` no fork, só artefato; baixado e apagado).

### Async por padrão
- `sync_shaders` padrão agora é Async (antes Sync; o menu marcava Smart como padrão). Medido na sessão 9: Sync 18-22
  janelas com quadro >100 ms (pior 1,2-2,2 s), Async 8-10 (pior 0,18 s); confirmado pelo usuário nas duas máquinas.

### O que o usuário deve testar
- No Bazzite: Settings → Game files → escolher a pasta com o `.xci`, o `.nsp` do update e o `prod.keys` (o código do
  jogo é gerado de novo, ~25 min). A tela inicial deve mostrar v1.1.0.
- Jogar com os saves e observar travamentos novos (mandar `~/.local/share/eowrecomp/eowrecomp.log`).

### Confirmado depois
- **Linux / Bazzite com 1.1.0**: o usuário jogou no Legion Go 2 com som ("playing great").
- **1.0.0 com o código novo** (Windows, instalação de teste `C:\EoW\pkg-100`, só o XCI): Set up regenera o código do
  jogo (o gerador mudou: `nso.py`), 1242 s; saves carregam, Zelda anda, 60 fps, som (REV11). O `eowgame.dll` antigo é
  recusado ("built for another version"), como esperado: quem atualiza precisa rodar Set up de novo.

### Branches e PRs (desde 2026-11-26)
- `dev`: tudo; trabalho novo entra aqui. `main` do fork = `dev` + README do fork + CI do AppImage.
- PRs para patrickksmdev/EoWRecomp, um assunto cada, a partir do `main` dele: #1 `win-on-patrick` (Windows / NVIDIA),
  #2 `pr/v110` (1.1.0 + som REV15; compila sozinho), #3 `pr/appimage-font`. O padrão Async fica só no fork (ele
  escolheu Sync).

### Próximo passo
- Corrigir o que o usuário encontrar jogando (log do Bazzite).
- `ICommonStateGetter` 66 aparece como não tratado na 1.1.0 (inofensivo até agora).

## Sessão 9 (2026-11-24): Windows 11 / RTX 3070 Laptop (NVIDIA, Vulkan 1.4) — este tree no Windows

Primeiro teste deste tree no Windows com NVIDIA (o usuário shkankin; até aqui o Windows só tinha sido testado com
RX 580). Build cruzado no WSL (`tools/windows/build.sh`, zig cc), janela 1280x720.

### Trazido do fork Windows (branch `win-on-patrick`)
- `windows: POSIX rename` (substitui o destino: o `rename` da CRT falha com EEXIST, então `romfs.src` numa 2ª configuração e `eowgame.dll`
  num rebuild falhavam).
- **Import library no link da `eowgame.dll`** (`Makefile`): o zig nomeia a import library da DLL pelo 1º arquivo de
  entrada e ignora `--out-implib`; com `$(IMPLIB)` antes dos objetos, `eowrecomp.lib` era sobrescrita e o 2º link
  sempre falhava (`rt_dispatch` indefinido). A lib agora vai depois dos objetos; dois relinks forçados mantêm o md5.
- `nca_extract.py --romfs-src` (RomFS lido no lugar, de dentro do XCI/NSP).
- Depuração: `EOWRECOMP_VS_DUMP` + `tools/vsemu.py` (roda o GLSL do vertex shader na CPU sobre os vértices de uma
  draw), `EOWRECOMP_DUMP_SHADERS` (compute que não traduz), linhas de instância/índices no log `[draw]`,
  `EOWRECOMP_SKIP_COUNT` e `EOWRECOMP_SKIP_CS` com lista.
- O resto do fork já estava aqui com outro nome (BRX, LDC.64, RGB565, tabelas de salto, autosave do cache, etc.).

### Visto funcionando (RTX 3070, scripts com `EOWRECOMP_INPUT` sobre cópia dos saves do usuário)
- Boot, filme de abertura, lista de saves (6 arquivos lidos), carregar autosave.
- Luta com Ganon (Link): escada, cutscene, ~80 s de luta, 60 fps, nenhuma draw pulada (o script não vence a luta).
- **A fenda/portal no chão** (Suthorn, depois de libertar Zelda) aparece certa (vazio escuro com destroços); no fork
  Windows antigo só o contorno aparecia.
- Ritmo: 60,0 fps estáveis (120 quadros a cada 2 s). O limitador de FPS deste tree (`fps_limit`, padrão 60) evita o
  bug de velocidade 2x que o fork Windows corrigiu com uma fila de apresentação (54971fd); fica o deste tree.
- `VK_EXT_map_memory_placed` não é usado no NVIDIA/Windows: o heap entra por `gmem_import` (log "guest heap
  imported ... 3220 MB"), o mesmo caminho do fork antigo.

### Corrigido: perda do dispositivo no NVIDIA depois da capa de Zelda (`6ba840d`)
- Sintoma: logo depois de Zelda pegar a capa do espadachim (Ruínas de Suthorn, antes do título), `VK_ERROR_DEVICE_LOST`
  com page fault numa leitura (`address read invalid 0x42c8d4000`..`0x42dd59000`), em ~1 de cada 4-6 execuções; com o
  `EOWRECOMP_VK_CHECKPOINTS` ligado, 8 de 16. O fork Windows antigo não caía ali (mas desenhava a fenda errada).
- Achado com `VK_NV_device_diagnostic_checkpoints` (novo `EOWRECOMP_VK_CHECKPOINTS=1`, com `EOWRECOMP_VK_DEVLOST_TRACE=1`):
  todas as falhas param na draw da fenda (vs 72a46f4000 / fs 72a46f5000, 1152 índices), que amostra o stencil do próprio
  depth-stencil via o snapshot de feedback.
- Causa: `resolve_feedback` reaproveitava o snapshot de uma textura sem conferir se ela mudou. O jogo reinicializa os
  objetos de textura no lugar (resolução dinâmica 896x504..1067x600; um objeto foi alvo de cor R11G11B10 antes de virar
  D24S8), e as views eram feitas com o formato/aspecto atuais: views de profundidade/stencil sobre uma imagem de cor.
  Agora o snapshot só é reusado se tamanho, formato e aspecto batem; senão é copiado de novo (log
  `feedback snapshot ... is stale`).
- Medido (rota com script da capa ao título, RTX 3070): 8/16 perdas antes, 0/16 depois; `EOWRECOMP_NO_SNAPSHOT_REUSE=1`
  também 0/12. Build final sem opções de depuração: 8/8 sem perda, 3 min passando a fenda a 60 fps, boot com save vazio
  e a luta com Ganon (até o quadro 8520, 60 fps) sem erro.
- Descartados no caminho (cada um com 6-12 execuções, todos ainda caíam): `EOWRECOMP_VK_LIVE_UBO=0`, `EOWRECOMP_VK_GMEM_FAST=0`,
  pular o compute SUST, limitar os acessos `gmem_` ao tamanho importado, `EOWRECOMP_SYNC_SUBMIT=1`. Pular os computes
  de culling 72a4711000/15000 pareceu resolver (0/16), mas eles nem eram despachados nessa rota: foi sorte; atenção a isso
  ao bisectar com `EOWRECOMP_SKIP_CS` (conferir "skip list" no log).

### Engasgos quando aparecem gráficos novos (relato do usuário, 2026-11-24)
- O usuário jogou o build `run-patrick` com os próprios saves: rodou e ficou bonito, mas às vezes caíam alguns quadros
  quando algo novo aparecia na tela.
- Causa principal: compilação de shaders/pipelines na primeira vez que aparecem (modo `sync_shaders = sync`, o
  padrão deste tree, espera a compilação). Com cache vazio, travadas de 0,5-4,5 s; com o cache do usuário (111 MB),
  no máximo ~170 ms, e só onde surgem pipelines novos (cena da capa).
- A preparação de shaders da tela inicial nunca rodava: o `play.bat` usa `EOWRECOMP_NO_LAUNCHER=1`, e
  `EOWRECOMP_SHADER_PREP=1` não fazia nada (`shader_prep_boot` não era chamado). Agora é chamado (`dc47ac9`) e o
  `play.bat` liga a opção (6 s com cache quente, 71 s com cache vazio). Ganho medido: cache vazio, compilações em jogo
  775 -> 634 e pior travada 4,5 s -> 1,6 s; cache quente, pouca diferença. Limite: das 246 combinações de shader que
  a rota usa, só 38 estão na lista distribuída (`shader_variants.txt`), e 251 entradas da lista não existem nos
  arquivos deste jogo; a lista própria do jogador (`cache/shader_seen.txt`) cobre o resto depois da primeira vez.
- Outra causa, sem shader: o cache de pipelines era gravado no disco a cada 30 s na thread de render, entre dois
  quadros: 120-140 ms com o cache de ~100 MB. Agora grava numa thread separada (`23da42b`): essas travadas sumiram.

### Modo de compilação de shaders (Sync / Smart / Async) - medido, 2026-11-24
- O usuário achou o jogo pior que o fork Windows antigo depois de instalar o pacote (cache vazio): 49 de 146 janelas de
  2 s com quadro > 100 ms, várias de 1-1,8 s. O fork antigo (~1000 compilações por sessão) tinha 3-5.
- Causa: o padrão deste tree é `sync_shaders = sync` (espera cada shader novo); o fork antigo pulava o draw até o shader
  ficar pronto (como Async). Em Sync, a tradução e a compilação rodam na thread de render, uma de cada vez.
- Mesma rota (Ruínas de Suthorn), cache vazio: Sync 18-22 janelas > 100 ms, pior 1,2-2,2 s; Smart 14-17, ~1 s; Async
  8-10, pior 0,18 s. Async mostra 1 quadro preto / um efeito faltando na primeira vez que um efeito grande aparece
  (quadros a cada 4: 2108 todo preto, 5592/5596 manchas); Sync não. Com cache quente os três ficam parecidos.
- O que o Smart espera (nova linha `[vk] render thread waited ... ms`, e `compile N (waited G+C ms)` nas estatísticas):
  pipelines de tela cheia que o driver NVIDIA leva 100-580 ms para montar, sem nada na fila na frente. Tirar o job da fila
  e montar na thread de render não mudou nada (pior 0,95-1,01 s contra 0,98 s): descartado.
- Pré-compilação não fecha a lacuna: adicionar as 739 variantes vistas pelo usuário à lista distribuída deixou ~260
  compilações em jogo, e 310 delas não são achadas no índice de shaders (o jogo monta/ajusta esses shaders em memória);
  a lista do upstream também tem 251 assim. Revertido.
- Decisão para o usuário: Async nas pastas de jogo (`run-patrick`, `pkg`), como o fork antigo ("Shader compilation" no
  menu F1). Próximo passo possível: Smart com tempo máximo de espera (pular quando a montagem passa de ~1 quadro).

### Também neste tree
- `gmem_import`: ao crescer o heap, a importação antiga era destruída depois de esperar só o trabalho já submetido,
  mas o command buffer em gravação pode já ter descritores dela; agora é liberada quando a submissão seguinte termina
  (`4ade00d`). Visto lendo o código; nas execuções medidas o heap foi importado uma vez só.
- `tools/test_vmnmx.c` não compilava com clang/zig (`int` de ponteiro).
- `tools/test_translate.sh` usa `REF=652e234`, que não está neste repositório (nem no upstream).

### Próximo passo / o que o usuário deve testar
1. Jogar com este build (pasta `C:\EoW\run-patrick`): a cena da capa e o título, e passar da fenda.
2. Vencer a luta com Ganon (o script não vence).
3. Áudio ainda não verificável (o laptop não tem saída de som).
4. O log mostra a resolução dinâmica do jogo variando (896x504..1067x600 escalados); ver se causa outros efeitos.

## Sessão 8 (2026-11-20): Linux x86-64 / AMD RX 7600 (RADV) — Pré-compilação de shaders (`shader_prep`), RecompLauncher e cubemap dinâmico (`v0.5.0`)

### Adicionado e corrigido nesta sessão
- **Pré-compilação antecipada de shaders (`a34e9885`, `a2b9f7b4`):**
  - Portado o sistema `shader_prep` / `shader_seen` de `LASRecomp` para `runtime/nvn/shader_prep.c`, `runtime/nvn/shader_seen.c` e `runtime/nvn/shader_prep.h` (adaptado para `ShaderKey.stencil_tex` e leitura direta de `.xci`/`.nsp` via `nx_romfs_open`).
  - Integrado na tela inicial (`runtime/ui/launcher.mm`) com pré-aquecimento em background e barra `"Preparing shaders"` ao clicar em `PLAY` caso ainda esteja em andamento.
  - Populado `runtime/nvn/shader_variants.txt` com **1.173 variantes** reais gravadas em gameplay (apenas hashes one-way e estado NVN, sem código proprietário).
- **Modo de shader padrão (`1182032c`):** `sync_shaders` em `runtime/settings.c` alterado para `SHADER_SYNC` por padrão, evitando pop-in visual em áreas inéditas enquanto `shader_prep` + `shader_seen.txt` mantêm o gameplay fluido.
- **Correção da iluminação ambiente / cubemap dinâmico (`e5799572`):**
  - Ao caminhar em áreas como a escadaria do Castelo de Hyrule, a luz ambiente e os reflexos metálicos (ex.: capacetes dos guardas) caíam para preto ao trocar do cubemap estático (`0x7f90f0325ab0`, BC6H) para o cubemap dinâmico (`0x7f913d7b1a00`, `64x64 f0x25 lv 7`) gerado pelo compute shader `72a4723000`.
  - Causa raiz: `texture_info()` e `shader_texture_object()` em `runtime/nvn/vulkan/exec.c` só consultavam `st.tex` (`0x20..0x118`) e retornavam dummy `1x1` para o `TXQ` (`tsize0`) no slot de imagem `c[2][0x120]` (`st.img[5][0]`), fazendo o compute shader sair sem gravar os pixels do cubemap; além disso, `stage_set()` não preenchia `rscale` para compute (`stage == 5`).
  - Adicionado `stage_tex_handle()` (cobrindo `st.tex` e `st.img`) e `rscale = 1.0f` para compute. Verificado in-game na escadaria do Castelo de Hyrule com iluminação e reflexos restaurados.
- **Integração com RecompLauncher (`23e79f7a`):** adicionado `recomplauncher.json` ao repositório e ao `.github/workflows/release.yml` para publicação automática nos assets das releases.

### Próximo passo
1. Continuar a progressão após a 2ª dungeon (Gerudo Desert) verificando novos shaders/SVCs/serviços IPC e ampliando `shader_variants.txt`.
2. Investigar os 2 opcodes de fragment shader sem tradução que aparecem no boot (`df02022020770600` e `c8380226aff70400`).
3. Validar em uma máquina Windows o pacote gerado pelo CI (`release.yml`).

## Sessão 7 (2026-11-19): Linux x86-64 / AMD RX 7600 (RADV) — Shaders, `unstick` no kernel e otimização de CPU (`gw_hit`)

### Corrigido e verificado nesta sessão
- **Piscadas de cenário/iluminação no modo `smart` (`75af504e`):**
  - `vk_prewarm_drain()` em `runtime/nvn/vulkan/exec.c` usava `flip_y = 1` e `depth_minus_one = 1` fixos em vez de `nvn_window_origin() == 0` / `nvn_depth_mode() == 0`, pré-compilando variantes erradas que `draw_()` nunca usava.
  - `SHADER_SYNC` passou a aguardar quando `pr->state == 0` ou `pp->state == 0` (mesmo após prewarm assíncrono), e `SHADER_SMART` passou a considerar críticos draws indexados de até 6 índices (`!ind_buf && r->x[2] <= 6`, como passes fullscreen de iluminação).
- **Causa raiz do freeze / `*** unstick` e watchdog duplicado (`3f8abb4a`):**
  - **Lost wake-up em `svc_wait_process_wide_key()` (`runtime/kernel.c`):** `mutex_release(mutex)` rodava antes de `*key = 1`, permitindo que outro core pegasse o mutex em user-space, enfileirasse jobs, destravasse, lesse `*key == 0` e pulasse `svcSignalProcessWideKey`. Agora `wait_kind = WAIT_CONDVAR` e `*key = 1` (`__ATOMIC_SEQ_CST`) são publicados antes de liberar o mutex.
  - **Race `TimedWait` vs `Signal`/`Unstick` em `block_current()` (`runtime/kernel.c`):** ao expirar `kwait()`, `block_current()` não rechecando `wait_kind` sobrescrevia `R_OK` com `R_TIMEOUT` mesmo após a posse do mutex já ter sido entregue (causando auto-deadlock em `t88`). Agora preserva `R_OK` se `WAIT_NONE`, continua sem timeout se já virou `WAIT_MUTEX`, usa `wait_tag` em `mutex_release()` e limpa `*key = 0` em `kernel_unstick()`.
  - **Watchdog duplicado no Linux (`runtime/platform/linux.c`):** `plat_crash_handler_install()` passou a instalar `sigaction` e iniciar `watchdog_thread` apenas uma vez por processo (mantendo `sigaltstack()` por thread).
  - Verificado em `build/run.log`: **0 `unstick`** em ~272 s de jogo.
- **Gargalo de CPU em áreas pesadas (`ac1639e8`):**
  - `gw_hit()` em `runtime/nvn/vulkan/exec.c` chamava `vk_completed_seq()` (`vkGetSemaphoreCounterValue`) antes de verificar sobreposição em `gw_tab`, gerando alto overhead em `gw_before_cbufs()` e `cbuf_info()` (~900–1.016 ms / 2 s em áreas com ~95k draws / 2 s).
  - Adicionados fast-reject por bounding box (`gw_min_lo`..`gw_max_hi`), cache de sequência concluída (`gw_done_seq`) podado na reutilização de slots em `sub()`, e consulta ao driver apenas em colisão real de submissão já enviada.
  - Medido em `build/run.log` (área pesada, RX 7600): `pre(snap)` caiu de **509–525 ms → 6–36 ms** / 2 s, `sets(cbuf)` de **481–491 ms → 30–127 ms** / 2 s, e o framerate subiu de **46–50 FPS (`pace 30`) → 99,8–120,0 FPS (`pace 60`)**.

### Próximo passo
1. Continuar a progressão após a 2ª dungeon (Gerudo Desert) verificando novos shaders/SVCs/serviços IPC.
2. Investigar os 2 opcodes de fragment shader sem tradução que aparecem no boot (`df02022020770600` e `c8380226aff70400`).
3. Validar em uma máquina Windows o pacote gerado pelo CI (`release.yml`).

## Sessão 6 (2026-11-16 a 2026-11-18): Linux x86-64 / AMD RX 7600 (RADV) — Rifts, estabilidade e performance (`v0.3.0`)

Marco: M5 avançado (jogável até a **2ª dungeon — Gerudo Desert** com áudio, save/load, Rifts limpos e zero freezes). Backend testado: **Linux x86-64 / Vulkan (RADV)**; Windows x64 é gerado no CI (`release.yml`), sem teste local nesta sessão.

### Corrigido e verificado nesta sessão
- **Glitch visual ao sair de Rifts (`7e317ea3`, portado de `tcsenpai/EoWRecomp@97d8b3ed`):** `gw_tab` agora expira entradas já concluídas via `vk_completed_seq()` e `gw_before_cbufs()` sincroniza apenas quando `guest_live` não pode ser usado por alinhamento/limites, removendo o workaround por endereço fixo. Testado em Suthorn Forest e Gerudo Desert.
- **Freezes aleatórios e falsos positivos (`99ea82c5`):** `ARB_DEC_WAIT_LESS`, `ARB_SIGNAL_INC_EQ` e `ARB_SIGNAL_MOD_EQ` em `runtime/kernel.c` passaram a usar `__atomic_compare_exchange_n` (CAS), eliminando corridas no árbitro; o watchdog em `runtime/platform/linux.c` subiu de 500 ms para 2 s com `kernel_dump_threads()` antes do `kernel_unstick()`. Verificado em log: **0 `unstick`** em 459 s / 38.553 frames e >2 h de jogo contínuo.
- **Gargalo de `vkQueueSubmit2` no RADV/AMDGPU + `draw_()` (`8fc8db0f`):**
  - Substituído `VK_EXT_external_memory_host` (`userptr`, que fazia o kernel `amdgpu` validar 3,2 GB a cada submit: `1,36–5,02 ms/submit`) por memória GTT nativa (`HOST_VISIBLE | HOST_COHERENT | HOST_CACHED`) mapeada em `HEAP_BASE` com **`VK_EXT_map_memory_placed` + `VK_KHR_map_memory2`** (`0,027 ms/submit`, ~50× menor), mantendo `gmem_import` como fallback.
  - Cache de `stencil_slots(stage)` invalidado por geração de texture pool (`nvn_tpool_gen`) / binds, e gating dos hashes FNV-1a de VS/FS e do scan de bisect (`F10`) em `draw_()` (`pre` de `4,55 µs` → `3,45–4,15 µs/draw`).
  - Medido em `build/prof.log` (área aberta, RX 7600): **~66 FPS → 91–116 FPS** (`max 10 ms`, `pace 60`).
- **Release & CI (`c97af6a7`, `de55d550`):** versão atualizada para `v0.3.0` e adicionado `.github/workflows/release.yml` para gerar AppImage Linux x86-64 + pacote Windows x64 automaticamente em tags `v*`.

### Experimentos descartados (revertidos)
- **Prewarm síncrono em `nvnProgramSetShaders`**, **`VK_EXT_graphics_pipeline_library` (GPL)** e **cache de descriptor sets `ds_cache[2048]` por submission**: todos pioraram FPS ou adicionaram contention/cache misses frente ao pipeline monolítico + `stage_set()` atual.

### Próximo passo
1. Continuar a progressão após a 2ª dungeon (Gerudo Desert) verificando novos shaders/SVCs/serviços IPC.
2. Investigar os 2 opcodes de fragment shader sem tradução que aparecem no boot (`df02022020770600` e `c8380226aff70400`).
3. Validar em uma máquina Windows o pacote `EoWRecomp-v0.3.0-windows-x86_64.zip` gerado pelo CI.

## Sessão 5 (2026-11-10 a 2026-11-14): Windows / Radeon RX 580 / Vulkan — vegetação, HUD, fenda do vazio; release beta_1

Marco: M5 em andamento (jogo jogável no Windows; faltam efeitos e desempenho). Backend testado: **só Vulkan, no Windows**
(Xeon E5-2650 v4, RX 580 8 GB). Metal, macOS e Android não foram tocados nem retestados.

### O que funciona (visto em screenshot/log do usuário)
- **Árvores e vegetação** (commit 0721dad): o jogo faz culling na GPU (compute 72a4711000/72a4715000: ballot + lane id +
  `lanemask_lt`) e desenha com `DrawElementsIndirect`. Faltavam `ClearBuffer`, os desenhos indiretos e, na RX 580 (subgrupo
  de 64), lane id/máscaras reais: S2R 0x00/0x38–0x3c agora saem de `mw_lane()` (`gl_SubgroupInvocationID & 31`) e
  ballot/vote/shuffle ficam numa metade de 32 lanes. Teste: `tools/test_lane.sh`.
- Corações do HUD (RGB565 com alfa no canal R), feixes esticados, ícone no `.exe` (via `windows_manifest.rc`, o runner não tem
  `windres`), artefato do CI = uma pasta só (`EoWRecomp-windows-x64`).
- **Leitura de stencil** (a1c0904): o shader da fenda (`72a71bb500`) amostra o *stencil* do D24S8 (`nvnTextureViewSetDepthStencilMode`
  = STENCIL) e testa os bits 5/6 com `R2P`. Antes recebia profundidade em float. Agora `ShaderKey.stencil_tex` (bit por slot de
  handle) faz o binding virar `usampler2D`, o texel volta como bits (`uintBitsToFloat`), a view usa o aspecto stencil com sampler
  NEAREST e os snapshots de feedback têm view de stencil. Efeito visto: tracinhas viraram linha contínua brilhante.
  Teste: `tools/test_stencil.sh` (TEXS e TLDS).
- Launcher: versão `beta_1`.

### O que ainda está quebrado
- **Fenda do vazio (perto de Suthorn)**: a borda roxa aparece, mas o **preenchimento escuro não aparece em frames normais**. No
  frame do F9 ele aparece (`pass_041.png`) e o stencil está certo (`fbstencil_*.pgm`: bit 6 em ~13 800 texels). Ou seja, a
  diferença é entre um frame normal e um frame em que cada passe é esvaziado (flush). Hipóteses já descartadas: decal
  (72a7db6000), quad iluminado (72a74ac500), precisão do EQUAL, discard do chão, prepass 72ee694000 sozinho, e **snapshot de
  feedback velho** (ae46b3d invalida o snapshot em escrita de stencil; o usuário viu que não mudou, nem com
  `EOWRECOMP_NO_SNAPSHOT_REUSE`). Suspeita atual: memória do guest lida pela GPU tarde demais (matrizes por instância do chão
  vêm de gmem) ou ordenação dos passes.
- Hachurado preto no G-buffer perto do portal (some ao pular todo o prepass `vs 8b62cd3f67cab37d`): pode ter a mesma causa.
- Desempenho 39–56 fps: ~3 flushes por frame por causa da leitura, na CPU, dos argumentos dos desenhos indiretos.
- Congelamentos intermitentes: provável wake perdido no kernel Horizon simulado; o auto-unstick é só mitigação.

### Diagnóstico novo
- `EOWRECOMP_SKIP_VSPROG=<endereço do VS,...>` (pula desenhos por endereço do VS; o hash de VS só cobre 0x200 bytes e os
  prepasses dividem o mesmo hash).
- `EOWRECOMP_FLUSH_PASSES=1`: submete e espera a GPU a cada passe (como o F9). `EOWRECOMP_VK_COPY_OPT=0`: desliga os aliases
  de cópia. F9 agora loga o stencil de cada draw (`sten en/ops/ref/wm`) e salva `build/fbstencil_NNN_snap.pgm` com o histograma.
- PowerShell mantém `$env:EOWRECOMP_*` na sessão: abrir outra janela (ou `Remove-Item Env:EOWRECOMP_*`) entre testes.

### Próximo passo
1. Rodar com `EOWRECOMP_FLUSH_PASSES=1` e com `EOWRECOMP_VK_COPY_OPT=0` perto do portal: se o vazio aparecer, achar a leitura de
   memória/ordem que falta (bisect por passe); se não, voltar aos shaders 72a7143000/72a7144500 (preenchimento).
2. Desenhos indiretos na GPU (`vkCmdDrawIndexedIndirect`) para tirar os flushes; depois a causa do freeze.
3. Validar o backend Metal e os comandos `CMD_*` ainda sem tratamento.

### O que o usuário deve testar e observar
- Sem variáveis `EOWRECOMP_*`: fps e o portal de Suthorn (borda roxa sim; preenchimento escuro ainda não).
- Os dois testes acima, dizendo só "apareceu / não apareceu"; se aparecer, print.
- Se travar: mandar `eowrecomp.log` (o watchdog registra os frames).

## Sessão 4 (2026-11-07): pacote do Windows pelo GitHub Actions

### Feito
- `.github/workflows/build-windows.yml` (push em `runtime/`, `tools/`, etc., ou "Run workflow"): três jobs.
  `exe` (cross-build com zig, `tools/windows/build.sh RELEASE=1`, sem console, log em `eowrecomp.log`), `helper`
  (`eowgen.exe` por PyInstaller no windows-latest) e `package` (zig para Windows de `tools/fetch_zig.sh`,
  `gamelib-src/`, `eowrecomp.dll.a`). Artefato `EoWRecomp-windows-x64`: ~164 MB (528 MB descompactado), sem arquivos
  do jogo. O zig é o completo (sem `tools/zig_slim.sh`).
- `runtime/nxpkg.c` inclui `platform.h` (pread/mkdir no Windows). `Makefile`: `all` só inclui o `eowgame.dll`
  quando há código gerado (`$(strip $(GEN_SRC))`). Manifest `activeCodePage` UTF-8
  (`runtime/platform/eowrecomp.manifest`): caminhos com acento (`C:\Users\José\...`) falhavam no `stat()` e a tela
  inicial dizia "No game files found". A busca do pacote agora registra no log o que achou e descartou.

### Primeiro teste no Windows (usuário: Windows 10, Xeon E5-2650 v4, RX 580, Vulkan 1.3.260)
- Funciona: XCI + `prod.keys` achados; código do jogo gerado e compilado na máquina (1917 s, uma vez; 4 módulos,
  296 677 funções, `extracted/eowgame.dll`); os 4 módulos carregam; boot do SDK; RomFS lido direto do XCI
  (8 033 071 180 bytes, 10 963 arquivos); swapchain Vulkan 1280x720; áudio (audren) abre; XInput detectado.
- **Problema**: tela preta com os botões Y / X / A e o contador de fps por cima (screenshot do usuário). Execução de
  ~95 s até fechar a janela. No log, milhares de desenhos pulados por "program compiling" / "pipeline compiling" a
  cada 2 s até o fim (ex.: 4 797 desenhos x 11 700 pulados). Ainda não se sabe se é só a compilação assíncrona
  atrasada (primeira execução, 95 s) ou um defeito neste driver; no Linux (Iris Xe) a abertura aparecia.
- Mesmo `SUST eb20138600f70018` sem tradução do problema aberto 3 (um compute shader).
- Próximo teste (usuário): deixar rodar vários minutos; e `set EOWRECOMP_SYNC_SHADERS=1` antes de abrir o `.exe`
  (compila cada shader na primeira vez, bloqueando: sem desenhos pulados) e olhar se a cena aparece.


## Jogo fixado (único build suportado)

| | |
|---|---|
| Título | The Legend of Zelda: Echoes of Wisdom |
| Title ID | **01008CF01BAAC000** |
| Versão | **v0 (0x0)**, display version **1.0.0**, sem update (partição update do XCI vazia) |
| Requisito de sistema (CNMT) | 16.0.0 (0x40000000) |
| SDK | NintendoSDK 16.2.0 (program NCA: SDK 16.2.0.0, key generation 0x11) |
| Program NCA | `0449fda9301caaad241256ec54b3c89f.nca` (5 804 949 504 bytes) |
| Nome interno do `main` | `Edward.nss` |

Build IDs dos módulos (endereços de patches/HLE valem só para estes):

| Módulo | Build ID | Arquivo |
|---|---|---|
| main | `a581406bc985865113d18cb19f11d5448ceea783` | 26 093 400 B |
| sdk (nnSdk) | `3053b22935e32ddf15ef81997603e5c267534a90` | 6 215 109 B |
| subsdk0 (glslc) | `e0d8adcc446cf14d6af1a51193f72e30ed3db9ac` | 5 392 097 B |
| subsdk1 (multimedia) | `ff0149d0b5e882b87c2f06a981302b130c1edb32` | 3 436 212 B |
| rtld | `2f1967113a281280a48ce3fc6dc23049327bf924` | 7 358 B |

RomFS: 10 963 arquivos, 8 032 371 686 bytes (todos com magic válido: FRES, BNTX, MsgS, FSTM, SARC, FSHA, webm…).

## Sessão 3 (2026-10-20, MacBook Air M1 8 GB, macOS 27): macOS e Android

**Bloqueio**: o NSP entregue nesta sessão (`~/Downloads/data`, ver memória do agente) está **truncado**: 5 637 144 576
bytes de 5 806 819 063 (faltam 162 MiB, cópia interrompida em exatamente 5376 MiB). O ExeFS (código) e a tabela de
compressão do RomFS ficam justamente no fim do NCA: nada do jogo pôde ser extraído, gerado ou rodado no Mac. Um vigia
em segundo plano retoma sozinho quando um NSP íntegro aparecer na pasta. **O usuário precisa copiar o NSP de novo.**

### Feito e verificado (sem os arquivos do jogo)
- **macOS = Vulkan via MoltenVK** (padrão; `MACOS_BACKEND=metal` mantém o renderer do LAS, sem as correções do EoW).
  Portabilidade (`VK_KHR_portability_enumeration`/`_subset`). Tela inicial renderizada no M1 (MoltenVK 1.4.2).
  `tools/macos/dev_deps.sh`, `docs/BUILD-macos.md`.
- **Leitura do pacote no runtime** (`runtime/nxpkg.c`): NSP/XCI/NCA com as chaves do usuário, AES (ARMv8 AES no CTR),
  XTS, LZ4 e BucketTree em C. O setup extrai só o ExeFS (~40 MB) e lê o RomFS direto do pacote (`romfs.src`): sem
  `romfs.bin` de 8 GB. `tools/test_nxpkg.sh`: vetores FIPS-197 / SP 800-38A / IEEE 1619 e blocos LZ4; com o NCA real:
  cabeçalho e cabeçalho do RomFS corretos. `nca_extract.py` lê NSP e recusa pacote truncado.
- **Android** (`android/`, `docs/BUILD-android.md`): app Gradle/CMake (NDK 27.2, volk, SDL3, FFmpeg LGPL, shaderc),
  camada de plataforma e JNI (do LASRecomp-Android-Plus), deslocamento do layout do guest (`GUEST_SHIFT`,
  `gen.py --shift`), setup pelo seletor de pastas do sistema lendo o pacote por *file descriptor* (sem copiar o
  jogo), controles de toque (`runtime/ui/touch.mm`), ciclo de vida (superfície recriada ao voltar do segundo plano),
  swapchain pré-rotacionado, afinidade de núcleos. `tools/android/build_game.sh` gera o APK pessoal com o código do
  jogo. **Verificado no emulador Android 15 arm64** (AVD próprio `eow_test`): tela inicial em paisagem, pré-rotação
  90°, seletor → JNI → leitura do pacote (pacote de teste truncado: mensagem certa), fundo/frente.
- **Código do jogo**: `Cpu *__restrict` nas funções geradas e `FN_ENTER` compilado fora (`FNPROF=1` o traz de volta):
  ~10% menos instruções no LAS-Android. **Ainda não medido no EoW.**
- **Tradutor Maxwell**: RED S32 min/max e INC/DEC (laço CAS no GLSL); auxiliares do GLSL renomeados (`mw_*`) — no
  MoltenVK `popcount`/`clz`/`fmin` colidiam com built-ins do Metal (1015 de 3200 shaders do fuzz falhavam; agora 63
  de 5882, todos artefatos do método: textura 1D, atributo 31). `tools/test_moltenvk.sh`.
- **Release macOS**: `make app` → `build/EoWRecomp.app` (FFmpeg LGPL de `tools/build_deps_macos.sh`, MoltenVK + loader
  embutidos e forçados, gerador + zig para compilar o código do jogo na máquina do usuário). Tela inicial ok.
- gfast (cópias de buffers antes de compute) só em GPU dedicada por padrão (memória unificada: só custo). Não medido.
- **Build do código do jogo no celular** (`tools/android/ondevice/`, `-PonDeviceBuild=true`): CPython 3.14 Android +
  capstone/unicorn/lz4, zig 0.17 (clang 22 + lld), kit do NDK; `gamebuild.c` com ramo Android (geradores um por vez,
  compiladores com nice e controle de memória, link com ld.lld contra `libmain.so`, instalação no armazenamento
  interno), `BuildService` (serviço em primeiro plano). **No emulador**: zig roda da pasta de bibliotecas nativas, o
  Python importa capstone/unicorn/lz4 e roda `gen.py`, `gamelib_entry.c` compila e linka contra `libmain.so`.
  `check_public_apk.sh`: APK de 79 MB sem código do jogo.
- **Lifter no ARM64** (`test_lift.py --synth`, sem NSO): 15 000 codificações sintetizadas contra o Unicorn; achou e
  corrigiu um crash (LDR literal SIMD opc 3) e C com UB em formas UNDEFINED de 32 bits. O Unicorn 2.1.4 erra
  LDSMAX/LDSMIN de 8/16/32 bits (compara sem sinal): `tools/test_lse.c` confere as 9 operações LSE x 4 tamanhos contra
  o próprio M1 — todas certas.
- Botão Voltar do Android abre o menu.
- **Release alpha_1** (2026-10-21, pré-release no GitHub, pedida pelo usuário mesmo sem o jogo rodado no Mac/Android):
  `.app` para **macOS 15+** — o loader do Vulkan, o shaderc e o Python do gerador (python-build-standalone) agora vêm
  de `build_deps_macos.sh` (os do Homebrew exigiam macOS 27); `bundle_macos.sh` confere todos os Mach-O. APK assinado
  com chave de release própria (fora do repo: `android/keystore.properties` → `~/.eowrecomp-signing/`, **guardar**:
  sem ela, as próximas versões não instalam por cima) e com o build no celular; `check_public_apk.sh` ok; tela inicial
  vista no M1 (Vulkan/MoltenVK) e no emulador Android 15. A tela inicial agora consulta as releases do repositório
  (`alpha_<n>` < `beta_<n>` < `v1.x`).

### Próximo passo (assim que houver um NSP íntegro)
1. `tools/venv/bin/python -I tools/nca_extract.py <prod.keys> <nsp> extracted --no-romfs --romfs-image` (ou setup pela
   tela inicial), `make gen`, `make -j8`, rodar no M1: abertura, primeira cena, áudio, save. Medir fps.
2. Comparar -O1 x -O2 no código do jogo no M1; medir o efeito do `restrict`/`FN_ENTER`.
3. SUST (imagens de armazenamento: tradutor + descritores) com o shader real `eb20…`.
4. Android: `build_game.sh --apk` e rodar no emulador (arm64 nativo no M1) e num celular. Em drivers sem
   `VK_EXT_external_memory_host` (comum no Android) a memória global dos compute shaders lê zero: precisa de um caminho
   por cópia.

## Marco atual (sessão 2): M4 concluído, M5 parcial (Linux / Vulkan)

Comprovado por screenshot (`EOWRECOMP_SHOT_AT`, capturas em `docs/screenshots/`): o jogo inicializa, toca a abertura
(masmorra do prólogo, Link e os moblins), entra na **primeira cena controlável** (HUD com corações e itens) e
**responde a input** (input roteirizado `EOWRECOMP_INPUT`: Link anda pelo corredor, entra na sala; prompts
"Swing sword", "Place / Toss" aparecem). Execução de 330 s / 2.819 frames sem travar. Backend testado: **Vulkan no
Linux** (Intel Iris Xe, Mesa ANV). Metal não foi tocado nem testado.

### Funciona
- M1: geração dos 4 módulos sem `Unsupported` (296 mil funções); lifter com LDXP/STXP, CAS/CASP, LSE (testado contra
  Unicorn); jump tables resolvidas também em funções divididas.
- M2/M3: boot pelo `nn::init::Start` do SDK 16.2 (3 callbacks), sm via TIPC, fs (RomFS original), acc, hid, am, time,
  audren REV11 (abre e é aceito pelo SDK), threads, mutex/condvar com a semântica do Horizon.
- M4: imagem correta da abertura. M5 (parcial): primeira cena jogável com input.

### Corrigido nesta sessão (cada um com a causa achada no código do jogo / SDK)
- Z-cull com tamanho 0; NVNsamplerBuilder maior que os 0x40 bytes que o jogo reserva (sobrescrevia a pilha);
  memória de comandos NVN (sombra 8x); revisão REV11 do áudio (status de efeito 0x90); `VFormatString` (jump table
  em função dividida); cabeçalho de 0x100 bytes dos compute shaders do NVN novo; tradutor Maxwell: BFE.BREV,
  HSETP2/HSET2 imediatos, VOTE, RED, LEA.HI, FLO.SH/.INV (o FLO errado fazia o laço de luzes rodar demais);
  laços estruturados nos shaders; timeout do `WaitProcessWideKeyAtomic` não readquire o mutex (travava a thread
  principal após ~1.200 frames).

### Problemas abertos (por prioridade)
1. **Desempenho de GPU**: ~9–12 fps na abertura numa Iris Xe. O material mais caro (fs `72ee66f300`, laço de
   luzes) ainda domina o passe principal; medir de novo sem outra carga na máquina (as últimas medidas tiveram a
   compilação do Windows em paralelo). Ferramentas: `EOWRECOMP_VK_PROF=1`, `EOWRECOMP_GPUPROF_AT=<frame>`,
   `EOWRECOMP_SKIP_FSHASH=<hash>`, `EOWRECOMP_SHADER_GUARD=<n>`, `EOWRECOMP_SAVE_MSL=1` (GLSL em `build/glsl/`).
2. **Artefato**: faixa escura vertical do topo da tela até o Link na abertura. Próximo passo: `EOWRECOMP_DEBUG_FRAME`
   (imagens por passe) para achar o draw.
3. Dois compute shaders sem tradução (RED com min/max assinado; `SUST` `eb20…`): 128 dispatches pulados.
4. Áudio não verificado a ouvido; save não testado (o diretório monta).
5. **Windows**: o `.exe` cruzado linka (7 exports para a DLL do jogo); a compilação da `eowgame.dll` foi
   interrompida a pedido do usuário em 44%. Rodar `tools/windows/build.sh all` de novo (só recompila o que falta) e
   testar no Windows.

### Como testar (Linux)
- `tools/run.sh` (SECS=60; janela oculta; `SHOW=1` mostra) — log em `build/run.log`, pilha do jogo resolvida
  (`tools/symgame.py`).
- Screenshots: `EOWRECOMP_SHOT_AT=300,600,900` → `build/frames/`. Input roteirizado:
  `EOWRECOMP_INPUT="1550:STICK_UP:150,1820:A:10"` (frame:botão:duração).
- Travamentos: rodar dentro do `gdb` e mandar `SIGINT` (o `ptrace_scope` impede anexar depois).

### Como compilar (Linux, sem sudo)
1. `tools/venv` (Python: capstone, unicorn, lz4, cryptography, pillow).
2. `tools/linux/dev_deps.sh`: zig 0.17.0 (clang 22 + lld, hash conferido) e os pacotes -dev (SDL3, Vulkan, shaderc,
   FFmpeg, VMA) via `apt-get download`, sem instalar nada no sistema.
3. `make gen` (84 s) e `PATH=$PWD/build/bin:$PATH make -j12 DEPS=$PWD/build/deps-linux GENARCH=-mcpu=x86_64_v3`
   (código do jogo: ~1 h na primeira vez; depois só o que muda).

### Pendências conhecidas
- `docs/linux.md` / `docs/BUILD-windows.md` ainda são do LAS.
- Widescreen, ícones de botão, menu sem abas específicas do EoW: M7.

### Sessão 4, continuação (2026-11-08): travamento de pipelines no Windows / Radeon RX 580
- Log com `[vk] jobs`: tradutor ocioso, 16 workers presos por minutos, sempre no mesmo job: `p fs code 72a5c12e00, glsl 50007 bytes`
  (criação de pipeline, `build_pipeline`). >186 s sem terminar, memória privada até 38 GB; draws pulados (pipeline compiling).
  Causa ainda não provada (driver AMD Windows vs. forma do GLSL).
- `EOWRECOMP_MAX_FS_GLSL=<bytes>` falha os pipelines de fragment shaders maiores que isso (experimento). `EOWRECOMP_SAVE_MSL=1`
  grava `build/glsl/<code>_fs.glsl` para inspeção.
- Pista do LASRecomp (branch `beta_6`, não a `main`): modo de shaders estruturados (`LARECOMP_VK_STRUCTURE`, `static_stacks_resolve`,
  `struct_blocks`, port do StructuredIr do Ryujinx, MIT): if/else/do-while em vez do laço `switch (pc)`; padrão no Mali/Adreno.
  Candidato a port se o `.glsl` travado for dominado pelo laço `switch (pc)`.
- Próximo passo: o usuário roda com `EOWRECOMP_MAX_FS_GLSL=30000` e `EOWRECOMP_SAVE_MSL=1`, manda `eowrecomp.log` e o `.glsl`.

- 2026-11-08 (later): causa provável do travamento: os shaders pesados (vs 72a5c0e100 990 cases, vs 72a5c2b000 392, fs 72eb9d4700 1254)
  têm todos um `BRX`, que fazia o tradutor rotular TODAS as instruções como destino (um `case` por instrução no laço `switch (pc)`).
  O LASRecomp já corrigiu isso (d92cc2a, issue #237, "AMD Windows nunca termina o build"): só os destinos da tabela de saltos (cb1) ganham
  `case`. Portado para `translate.c` (`brx_table_labels`; `EOWRECOMP_BRX_ALL_LABELS=1` volta ao antigo) + `tools/test_brx.sh`
  (4 labels com a tabela, 11 sem). MSL inalterado (só GLSL). Ainda NÃO verificado no PC do usuário (RX 580, Windows).
- Também: `EOWRECOMP_MAX_FS_GLSL` / `EOWRECOMP_MAX_VS_GLSL` (descartam pipelines grandes, só experimento), `EOWRECOMP_NO_PIPELINE_CACHE`,
  linha `[vk] jobs` com o job mais longo (tipo, fs/vs, tamanho). `EOWRECOMP_VK_OPT=1` não ajudou.
- Usuário deve testar: duplo clique, sem variáveis; olhar se a cena 3D aparece e se `pipeline compiling` zera, mandar `eowrecomp.log`.

- 2026-11-08 (verificado): com o port do BRX a cena 3D renderiza na RX 580 / Windows (Vulkan), 60 fps, workers ociosos, memória estável.
- Abertura/título com save existente: o vídeo agora é lido do RomFS (XCI) quando não existe no disco (`fs_rom_read`, `movie.c`);
  CI ok, ainda NÃO verificado pelo usuário com save.
- Crash após ~6 min: `FATAL: no function at 7001a65870 (lr=7001a65160)`, x10 = alvo. É um `br` indireto não resolvido pelo lifter
  (alvo ~0x710 depois do lr: provavelmente dentro da mesma função). Hipótese: tabela de endereços absolutos
  (`ldr xt,[xb,xi,lsl #3]; br xt`), que `computed_target` não reconhecia e ia direto para `rt_dispatch`. Correção em `tools/gen.py`
  (esse padrão ganha o fallback de todas as instruções) + `tools/test_gen_br.py`. NÃO verificada: o binário do jogo não está
  neste ambiente; precisa regenerar no PC do usuário. Se repetir, o alvo/lr novos dizem se a hipótese estava errada.
- Abertos: corações da HUD e item largado pretos; malha/textura do Link esticada; compute shader com SUST não traduzido (840 dispatches/2 s);
  efeito de áudio tipo 3; `[tex] type mismatch: want 3 have 1`.
- Usuário deve testar: novo pacote (regenera o código do jogo, build demorado), jogar >10 min com o save, mandar o log se cair.

- 2026-11-09: crash ao sair da sala persistiu com o pacote do b9850dc (a hipótese `ldr x,[b,i,lsl #3]` não bastou; o fallback ficou, é inofensivo).
  `dispatch.c` agora imprime x0-x30 e o código da função chamada pelo `bl` antes do lr (até o primeiro `br`) no FATAL; precisa do log.
- Suspeita nova para corações/item pretos e Link esticado: o port do BRX (labels só dos alvos da tabela). Esses materiais/skinning têm
  BRX; se a tabela de cb1 lida a partir de `blob+const_offset` estiver incompleta, o dispatcher cai no `default`. No Linux/Intel (antes
  do port, com todos os labels) a HUD saía certa mesmo com o compute `SUST` pulado, então `SUST` não parece a causa.
  `EOWRECOMP_BRX_LOG=1` imprime por BRX: hash do shader, nº de entradas e as instruções-alvo. A/B: `EOWRECOMP_BRX_ALL_LABELS=1`
  (volta ao antigo, mas na RX 580 trava os builds de pipeline: usar só numa cena curta com `EOWRECOMP_SHADER_THREADS` alto).
  `[tex] type mismatch: want 3 (CUBE) have 1 (2D) 1408x792 fmt 0x35`: um sampler de cubo recebe uma textura 2D de render target
  (slot não usado/obsoleto); vira textura preta, provavelmente inofensivo.

- 2026-11-09 (crash resolvido por leitura do log, aguarda teste): o diagnóstico novo mostrou `f_7001a657e0`:
  `adr x10,+0x20; ldrh w11,[x9,x8,lsl#1]; add x10,x10,x11,lsl#2; 4x mov; br x10` — tabela compacta LLVM com o `br` 7 palavras depois do ADR.
  `adr_feeds_br` olhava só 6 → o ADR virou início de função, a função foi dividida, o alvo (7001a65870) ficou em nenhum pedaço.
  Janela passou a 16 (`tools/gen.py`); `tools/test_gen_br.py` usa a sequência real (janela 6 falha, 16 passa). Exige regenerar o código do jogo.
  (A mudança `ldr xt,[xb,xi,lsl #3]` do commit b9850dc não era a causa; o fallback ficou, é inofensivo.)
- `[brx]` do log do usuário: 148 linhas, 66 shaders, tabelas de 3/5/6/8/13 entradas, ascendentes e sensatas (mesmo BRX na inst 30 dá 5 ou 8 entradas conforme
  o shader) — o port do BRX parece correto; a suspeita sobre ele enfraqueceu.
- Link, capa do Ganon esticados e portal do void ausente: todos deformação/partículas → suspeita volta ao compute shader `SUST` (7 dispatches/frame pulados).

- 2026-11-09 (2º crash, após a cutscene do logo): `no function at 7001810220`, lr=700180f698 (lr-4 é `blr`, sem dump do callee), x9=tabela em rodata,
  x8=0xa, x11=0x2e, x10=base+0xb8 → mesmo padrão de tabela compacta, mas o `br` não foi achado. O 1º crash (janela do ADR) foi corrigido e passou.
  Correção geral em `tools/gen.py`: `same_function()` — endereço de código materializado (ADR / ADRP+ADD) dentro da própria função do .eh_frame
  nunca é callback, então não vira início de função. Teste em `tools/test_gen_br.py`. NÃO verificado: precisa do pacote novo.
  `dispatch.c` agora também despeja 0x150 bytes antes do alvo (o `br` fica logo antes dos casos).

- 2026-11-09 SUST (compute `72a4723000`, `eb20138600f70018` = SUST.P.2D.RGBA [R0], R24, R39): traduzido (`emit_sust` em translate.c: imageStore em
  `image2D` writeonly sem formato; handle = LDC/MOV c[b][o] achado voltando no código; se não achar, o erro mostra a instrução que escreveu o registrador).
  Runtime (Vulkan): `vk_reflect` reconhece imagem de escrita; texturas com a flag NVN IMAGE (0x4) ganham `STORAGE`; `image_info()` resolve o handle
  (banco 0: slots de textura 0x20.., imagens 0x120.. — PALPITE; outros bancos: lê o handle da memória do buffer); features
  `shaderStorageImageWriteWithoutFormat/ExtendedFormats`; barreira total depois do dispatch. Teste: `tools/test_sust.sh`.
  NÃO verificado em execução (sem Vulkan/GPU aqui; só tradutor testado). O log do usuário mostra `[cs-img] ...` com handle/textura/flags: se disser
  "NOT writable" ou "(none)", o palpite do offset ou o valor da flag IMAGE está errado. Hipótese a confirmar: era isso que esticava Link/capa/portal.

- 2026-11-09 (log do usuário com o pacote da SUST): o crash dos `br` parou (cutscenes, água, teleporte). O compute `72a4723000` (SUST) traduz e roda, mas
  `[cs-img] c[2][0x120]: handle 0 -> none`: o handle está no banco 2 (não 0) → `image_info` agora trata bancos 0 e 2 como a tabela do driver (imagens em 0x120+8*i = st.img).
  Outros 2 computes (`72a4711000`, `72a4715000`, mesma instrução em 0xd28: `3b7707e061172a0f`) seguem sem tradução; ainda não identifiquei a instrução
  (não é SHF/BFI/DFMA; Rd=R15, Ra=R42, pred PT). A mensagem de erro agora traz as 3 instruções antes e depois. Gráficos ainda estranhos: corações com fundo vermelho
  opaco (alfa ignorado), Link/capa/espadas esticados, portal do void.

## 2026-11-09 (noite) — SUST por view, DEBUG_FRAME no Windows
- `vk_storage_view(tex, view)` agora usa o nível base / camada do view de cada handle (setmask 1/2): o log mostrava 6 handles da
  mesma textura (saídas de uma cadeia de mips) e todos escreviam no nível 0. **Não verificado em execução** (precisa de log novo:
  `[cs-img]` + imagem).
- `vk_save_png` cria o diretório de destino: no Windows não existe `build/` ao lado do exe e DEBUG_FRAME/SHOT_AT falhavam.
- **Aberto:** instrução `3b7707e061172a0f` (computes 72a4711000/72a4715000), reg-form 0x5d77. Campos: Rd bits 0-7, Ra 8-15,
  Rc = bits 39-46 (nos dois exemplos Rc == Rd/R31, vindo de um IADD32I logo antes), imm16 em 20-35 (0x611 / 0x610). Hipótese:
  VMNMX (vmin/vmax do PTX: d = op2(min|max(a,b), c)); sem a tabela de bits de min/max, sinal e seletores NÃO traduzido de propósito
  (chutar produziria índices de ossos errados). Pista de uso: IMNMX seguinte é max(R15,R16).
- Próximo teste do usuário: `$env:EOWRECOMP_DEBUG_FRAME="300"; .\eowrecomp.exe`; enviar `build/pass_*.png` + log (corações vermelhos).

## 2026-11-10 — diagnóstico de skinning / corações (sem correção ainda)
- Testes do usuário (RX 580) com a build 2b7ae2a: 60 fps estáveis, 0 compute pulado (SUST OK). Link/Zelda continuam esticados **só controlando**
  (algumas cutscenes normais); corpo da Zelda ok, uma peça vira um feixe vertical. `EOWRECOMP_VK_VCACHE=0` e `EOWRECOMP_VK_NO_GMEM=1`
  não mudam o esticamento (cache de vértices e gmem descartados; NO_GMEM só faz o texto sumir).
- VS 72a5c2b000 (personagem): índice de osso em a7 (uvec4, 32 bits) * 0x30 → matriz 3x4 lida de `cb6` (UBO do jogo, `ubuf[0][3]`).
- Corações: FS 7269fa9900 = (tex*cb3[0] + cb3[1]) * cor do vértice; textura 250x100 ASTC 4x4 sRGB (0x87). Ícones ASTC (0x8a/0x8b) saem certos.
  Decodificador ASTC revisado (modos de cor, pesos): sem erro achado. Blend factor: sem "unknown blend" nos logs.
- `EOWRECOMP_DEBUG_DATA=1` (com F9) agora também imprime todos os vertex streams (floats + words) e os cbufs do VS (`vcbN`, tamanho do
  range vs. declarado). **Pedir ao usuário:** `$env:EOWRECOMP_DEBUG_DATA="1"; $env:EOWRECOMP_DEBUG_FRAME="300"; .\eowrecomp.exe`, F9 com a Zelda
  esticada na tela, e enviar o log (e `build/pass_*.png` finais) — e o mesmo na cena dos corações para `fcb3`.
- Aberto: VMNMX (`3b77…`, tabelas do envytools recebidas; falta o bit min/max da 1ª operação).
- 2026-11-10 (log DEBUG_DATA, frame 2445): paletas de ossos (vcb6) OK — 1 osso = 48 B, 2 = 96 B, Link/Zelda 58 = 2784 B, matrizes com rotação/translação
  sãs; hipótese "matriz fora da faixa/lixo" não sustentada. Personagens compartilham o mesmo FS (hash 9f4e87dd94e644eb): VS 72a5c2b000,
  72ee694000, 72a6c0c000, 72a64cc000. Novo `EOWRECOMP_SKIP_VSHASH=h1,h2` (+ "vs hash" no log de draw) para achar qual VS desenha o feixe.
- 2026-11-10 (noite): formatos de atributo de esqueleto conferidos no log (a7 = R8UI/RG8UI/RGBA8UI, a8 = RG8/RGBA8/RGBA16 UNORM, a0 F32x3/F16x4,
  a6 snorm10): todos mapeados certo em `vertex_format`; 0x3E já tratado. Hipótese testável: paleta de ossos (cb6, dinâmico) copiada por
  `guest_copy` antes de o compute do mesmo submit escrever os ossos secundários (capuz/capa/espada). `cbuf_info` agora lê UBOs dinâmicos
  (não-compute) direto do heap (`guest_live`, gmem com usage UNIFORM). `EOWRECOMP_VK_LIVE_UBO=0` volta à cópia. **Não verificado em jogo**:
  se piorar (tremor/flicker de personagens), testar com LIVE_UBO=0 e reportar.
- 2026-11-10: UBO in-place (10ce7aa) NÃO resolveu o esticamento (usuário testou). Próximo: `EOWRECOMP_DEBUG_DATA` imprime por draw skinned
  "skin: N vertices, palette cbK P matrices, max bone index, indices out of range, unsane matrices". (Nota: as linhas "vbuf16" dos logs
  anteriores eram na verdade ubuf[0][0] — overrun de vbuf[16], corrigido.)
- 2026-11-10 (tarde): log DEBUG_DATA com a build 0ff6ddb+: a7 = R8UI (stride 32, 1 osso) ou RGBA8UI (stride 40, 4 ossos, pesos em a8 RGBA16 UNORM), a0 = F32x3,
  nenhum atributo usa 0x3E; 36 verificações `skin:` limpas (índices dentro da paleta de 58 matrizes, matrizes sãs). Ainda esticado (usuário testou).
  Índices, paleta e formatos de atributo estão descartados como causa. Novo em `EOWRECOMP_DEBUG_DATA` (**não verificado em jogo**):
  - `skin-cpu:` por draw skinned — faz o skinning na CPU com os mesmos dados que a GPU lê e imprime bbox bind-pose vs. skinned, distância média,
    nº de vértices a mais de 8x a média e o pior vértice (ossos e pesos). Se já aparece um feixe aqui, o problema está nos dados (pose/pesos);
    se a malha sai compacta aqui mas esticada na tela, o problema está no lado da GPU (VS traduzido, fetch do atributo).
  - `blend rtN on:` por draw — fatores/operações de blend crus + máscara de escrita + formato do RT (corações com fundo vermelho opaco).
  - `[astc] nvn fmt ... alpha min/max ...` para cada textura ASTC decodificada na CPU, e PNGs `build/astc_87_WxH_N.png` + `_alpha.png` das primeiras
    texturas 0x87 (4x4 sRGB, a dos corações é 250x100): mostra se o alfa já está errado no decodificador.
  Pedir ao usuário: `$env:EOWRECOMP_DEBUG_DATA="1"; $env:EOWRECOMP_DEBUG_FRAME="300"; .\eowrecomp.exe`, F9 com Link/Zelda esticados na tela (e
  de novo na cena dos corações), e enviar o log + os `build/astc_87_*.png`.
- 2026-11-10 (log eb740ce4, build fe3a172): 36 draws skinned, todos com índices de osso dentro da paleta (58 matrizes, max 57) e 0 matrizes
  NaN/enormes; 12 primeiras matrizes = rotação de escala 1 + translação ~(160,-45,170). Novo diagnóstico: "skin: bones used by vertices that look
  uncomputed (zero / near origin)" — hipótese: ossos secundários (capuz/capa/espada) com matriz nunca calculada → vértices colapsam à origem.

### 2026-11-10 — corações (fs 72d9aafe00)
- GLSL do fs: alfa final = sat(t2.r + t2.g*(1-t0.a) + [cb3[0].y!=0] * (t0.a+t2.a+t1.a)*cb3[0].y); cor = t0.rgb + t1.rgb*cb3[3].xyz*t0.a*cb3[2].w + t2.g*cb3[1].xyz. t0 = ASTC, t1 = RG8, t2 = RGB565. A forma do coração vem de t2.r (RGB565) e/ou de cb3[0].y.
- O log `fcb` indexava `ubuf[1][c]` em vez de `ubuf[1][c-3]` (o "1.13 4 0 1" visto antes era outro banco, não o cb3 real). Corrigido; falta ver o cb3 real do fs num log novo.
- Mapeamento 0x3C→R5G6B5 mantido (igual ao Metal/MoltenVK); sem evidência de troca R/B.
- Log 66497297 (DEBUG_FRAME=1500, fcb corrigido): cb3 real dos corações = (5i,0,0.27,1)(1,1,1,0)(1,1,1,0)(0,0,0,1) → p0 desligado; cor = t0.rgb + t2.g, alfa = t2.r (RGB565). Dados sãos; resta a textura RGB565 (ordem de canais ou conteúdo). Interruptor de teste: EOWRECOMP_RGB565_BGR=1 (B5G6R5). Não verificado.
- 2026-11-10: **corações corrigidos** (confirmado pelo usuário com EOWRECOMP_RGB565_BGR=1, Vulkan): RGB565 do NVN = R nos bits baixos = B5G6R5 do Vulkan. Agora é o padrão (EOWRECOMP_RGB565_RGB=1 volta ao antigo). Pendente verificar: 0x39 (RGBA4), 0x3B/0x95–0x97 (RGB5A1) podem ter a mesma troca; o Metal (metal.m) também usa B5G6R5Unorm para 0x3C e pode precisar do mesmo ajuste. Esticamento de Link/Zelda continua aberto.
- 2026-11-10 (esticado, análise): todos os "feixes" (capuz do Link, lâminas do inimigo) saem na MESMA direção na tela; o VS de skinning lê o nº de influências de cb12[0][0] (0 = rígido via cb5) e salta por BRX com tabela em cb1. skin-cpu assume ncomp influências, mas o jogo usa cb12 (draws RGBA8 mostram 4º peso 255 = só artefato do modelo). Falta saber se algum compute escreve a paleta (vcb6): novo log `[cs-frame]` (DEBUG_DATA + DEBUG_FRAME) lista sbufs/ubufs de cada dispatch do frame capturado.
- 2026-11-11 (esticado): log 97eda089 — nenhum compute escreve a paleta por sbuf (os 5 com gmem podem escrever via ponteiros); paleta vista pela CPU idêntica antes/depois dos computes (CPU lê antes da GPU). Nº de influências por draw (cb12[0][0]): 1 (a7 R8UI, rígido), 2 (RG8UI+RG8), 3 (RGBA8UI+RGBA8), 4 (RGBA8UI+RGBA16). skin-cpu compacto em todas as malhas → dado bom, defeito provavelmente no lado GPU. Nova tecla **F10** (Vulkan): percorre as malhas esqueléticas (por contagem de índices), pulando uma de cada vez e logando `[skipmesh]`, para achar a malha do feixe.
- 2026-11-11: o stepper F10 por malha falhou (lista de 32 encheu com inimigos/cenário; log 5bbbb663: o feixe não sumiu em nenhum passo). Trocado por **busca binária sobre todos os draws** (vs + nº de índices): F10 = pula a 1ª metade dos candidatos; F7 = "o feixe sumiu"; F8 = "o feixe continua"; no fim loga `[bisect] FOUND`.
- 2026-11-11 (esticado): **bisect achou o feixe**: draw vs 72a46e1000 (336 índices) → cone de luz renderizado num mapa 128x72 RGBA8 (vp 85x48 pela escala 2/3), usado depois como dado. VS lido: modo cb14[3][1] (1/2 = cone com matriz 3x4 em cb14[0..2] e escalas cb14[3][2..3]; outro = clip direto), mapeia (prof. cb4[11], lateral cb4[10]) para x/y do mapa com cb4[70]. Hipótese: o mapa não deve ser escalado (era tratado como buffer de tela 16:9). Mudança: `tex_scalable` exige largura >= EOWRECOMP_SCALE_MIN_W (padrão 160). **Não verificado**; teste sem build: EOWRECOMP_NO_SCALE=1.

## 2026-11-11 — feixes esticados: LDC.64 com endereço == destino (CONFIRMADO pelo usuário em 2026-11-11, Vulkan/RX 580)
- vs 72ee694000 / 72ee677700 / 72a5c2b000, caminho de 4 influências (pc 0x7a8): `LDC.64 R6, c[6][R6+0x28]`. O tradutor
  emitia `r6 = cbr(.., r6+40); r7 = cbr(.., r6+44)`, a segunda palavra com o r6 já sobrescrito -> endereço de cbuf lixo
  (clamp no último vec4) -> componente de translação gigante do 4º osso -> cabelo/capuz/capa viram feixes.
- Correção em `runtime/nvn/maxwell/translate.c` (LD c[idx][reg+imm]): copia o registrador de endereço antes de escrever.
  Teste: `tools/test_ldc.sh` (PASS). Os dados de ossos/CPU já estavam sãos (log 744b66ec), o que apontou para o shader.
- Backend: Vulkan (GLSL). O caminho MSL compartilha o mesmo emissor, mas não foi testado no Metal.
- Verificado: usuário rodou o build 0a8f643 e os feixes sumiram. Próximo: textura faltando no portal do vazio; depois desempenho (overlay, 120 fps) se pedido.

## 2026-11-12 — VMNMX (árvores invisíveis, save 100%) e deadlock raro
- Log do usuário (F9 na floresta, frame 17381): `skipped: compute program 432` por frame = dispatches dos computes 72a4711000 / 72a4715000, que
  falhavam em `3b7707e061172a0f` (VMNMX). Hipótese: são eles que alimentam as árvores (invisíveis). **Não verificado** (precisa do exe novo).
- VMNMX implementado em `translate.c` só para o caso conhecido (Rb registrador, 32 bits, op2 acc/min/max/nop; layout do yuzu
  `shader_bytecode.h`, commit 76f178ba): nos dois shaders é `Rd = max(Ra, Rb, Rc)` com sinal. Qualquer outra combinação continua falhando (não chuta).
  Teste: `tools/test_vmnmx.sh` (PASS). Ainda falta a forma imm16 e formatos/seletores estreitos.
- Shaders pesados (FS/VS de ~60 KB de GLSL) levam 2–9 s para compilar no Xeon: draws pulados ("program/pipeline compiling") até terminar.
  Candidato a otimização: cache de pipelines em disco.
- Deadlock raro (jogo congela, áudio segue): watchdog (`runtime/platform/windows.c`) imprime pilhas + estado das threads + histórico de
  mutex/condvar do kernel (`kernel_dump_threads`). Log 4c1b77be: só a thread principal (t80) presa num condvar, tickers vivos; aguardando um log com o histórico novo.
- 2026-11-12 (log 5c37cc47, build com VMNMX): VMNMX passou; os mesmos computes 72a4711000/72a4715000 agora param em `ed03000000500005` = `ATOM.E.ADD.S32 R5, [R0], R5`
  (atômica global COM retorno do valor antigo; só existia RED). ATOM implementada em `translate.c` (campos do Ryujinx InstAtom; add/min/max/inc/dec/and/or/xor/exch,
  U32/S32; MSL sem inc/dec). Teste: `tools/test_atom.sh`. Hipótese: contador de instâncias visíveis do culling de vegetação (árvores/grama). **Não verificado.**
