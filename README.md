# Radar de vagas de dados (júnior)

Um robô que roda sozinho todo dia às 7h17. Ele busca vagas de dados (analista, engenheiro, cientista, BI, analytics) em fontes públicas, guarda só as de nível júnior e trainee (e as sem nível declarado que não pedem experiência demais) e publica tudo num painel só seu. No painel você marca cada vaga como **Interessado**, **Apliquei** ou **Descartar** e escreve anotações.

**Fontes**
- **Portal da Gupy**: reúne as vagas de milhares de empresas brasileiras.
- **Greenhouse** e **Lever**: quadros públicos de vagas de empresas como Nubank, Stone, VTEX, CI&T etc. (a lista é editável).

Custa R$ 0. Tudo roda no GitHub (Actions + Pages), dentro do plano gratuito.

---

## Instalação (uns 15 minutos, uma vez só)

### 1. Crie o repositório
1. Entre em <https://github.com> (crie uma conta se não tiver).
2. Clique em **New repository** (botão verde, ou o **+** no canto superior direito).
3. Em nome, escreva `radar-vagas-dados`. Marque **Public** e não marque nenhuma opção de README. Clique em **Create repository**.

> Por que público? O GitHub Pages (o site do painel) é gratuito só para repositórios públicos. O repositório guarda apenas vagas que já são públicas. **Suas marcações e anotações ficam no seu navegador, não no repositório.**

### 2. Envie os arquivos
1. Descompacte o `radar-vagas-dados.zip` no seu computador.
2. Na página do repositório recém-criado, clique em **uploading an existing file**.
3. Abra a pasta descompactada, selecione **tudo o que está dentro dela** e arraste para a página. Clique em **Commit changes**.
4. Confira se a pasta `.github` apareceu no repositório. Se não apareceu, veja "A pasta .github não subiu" lá embaixo.

### 3. Dê permissão para o robô salvar as vagas
**Settings** → **Actions** → **General** → role até **Workflow permissions** → marque **Read and write permissions** → **Save**.

### 4. Ligue o site do painel
**Settings** → **Pages** → em *Branch*, escolha `main` e a pasta `/docs` → **Save**.
Em 1 ou 2 minutos o endereço aparece no topo da página. Ele tem este formato:
`https://SEU-USUARIO.github.io/radar-vagas-dados/`
Salve nos favoritos, inclusive no celular.

### 5. Rode a primeira coleta
Aba **Actions** → se aparecer um aviso, clique em **I understand… enable them** → clique em **Coleta diária de vagas** na lateral → **Run workflow** → **Run workflow**.
Leva de 3 a 6 minutos. Quando ficar verde ✅, abra o painel. As vagas de exemplo terão sido trocadas pelas reais.

Pronto. A partir daí ele roda sozinho todo dia.

### 6. (Opcional) Receber aviso das vagas novas
Para ganhar uma notificação (e e-mail) por dia com as vagas novas:
**Settings** → **Secrets and variables** → **Actions** → aba **Variables** → **New repository variable** → Name `AVISAR_POR_ISSUE`, Value `true`.
Todo dia que tiver vaga nova, o robô abre uma *issue* com a lista. O GitHub te notifica se você estiver "assistindo" o repositório (botão **Watch**, que já vem ligado para o dono).

---

## Usando o dia a dia

- **Para ver**: vagas que você ainda não marcou. As que chegaram nas últimas 36 h têm o selo **nova**.
- **★ Interessado / ✓ Apliquei / ✕**: clicar de novo desfaz. Vagas marcadas ganham um campo de anotação.
- **encerrada**: a vaga sumiu da fonte (foi fechada). Ela continua no painel por 30 dias e depois sai.
- Passe o mouse no selo de nível (ou abra "Ver descrição") para ver **por que** a vaga entrou, por exemplo "título diz júnior" ou "pede só 1 ano de experiência".
- **Marcações em outro aparelho**: elas ficam salvas no navegador onde você clicou. Para levar ao celular ou a outro computador, use **Exportar marcações** e depois **Importar marcações** do outro lado. Faça um export de vez em quando como backup.

## Ajustando o que você quer ver

Tudo está em **`config.yaml`**. No GitHub, abra o arquivo, clique no lápis ✏️, edite e clique em **Commit changes**. A próxima coleta já usa a regra nova (ou rode na hora pelo **Run workflow**).

| Quero… | Mude |
|---|---|
| ver estágios também | `niveis: [junior, trainee, estagio, nao_informado]` |
| só vagas que dizem "júnior" explicitamente | tire `nao_informado` de `niveis` |
| só remoto | `modalidades: [remoto]` |
| presencial/híbrido só em SP e Campinas… | `estados: [SP]` (remoto continua passando) |
| tolerar vagas que pedem até 3 anos | `max_anos_experiencia: 4` (descarta 4+) |
| incluir outro tipo de cargo (ex.: "governança de dados") | adicione em `palavras_area` e em `gupy.termos` |
| sumir com uma empresa | `empresas_bloqueadas: [Nome da Empresa]` |
| acompanhar uma empresa no Greenhouse/Lever | veja abaixo |

**Como achar uma empresa no Greenhouse ou no Lever:** abra uma vaga no site de carreiras dela. Se o link for `boards.greenhouse.io/XYZ/...` ou `job-boards.greenhouse.io/XYZ/...`, adicione `XYZ: Nome` em `greenhouse.empresas`. Se for `jobs.lever.co/XYZ/...`, adicione em `lever.empresas`. Empresas que usam Gupy já aparecem pelo portal e não precisam ser listadas.

## Como o filtro de nível funciona

1. Título com **estágio/estagiário/intern** → Estágio. Título com **trainee/aprendiz** → Trainee.
2. Título com **júnior, jr, entry level, "Analista I"** → Júnior (mesmo se também disser "Pleno", como em "Jr/Pleno").
3. Título com **sênior, sr, pleno, pl, especialista, lead, coordenador, gerente, head, II, III…** → descartada.
4. Sem nível no título, o robô lê a descrição:
   - pede `max_anos_experiencia` anos ou mais → descartada;
   - diz "perfil pleno/sênior" → descartada;
   - fala em júnior, início de carreira ou pede só 1–2 anos → Júnior;
   - nada disso → **Nível não informado**. Muitas vagas de entrada na Gupy aparecem assim.

O filtro erra às vezes, e é por isso que existe o botão ✕. Se perceber um padrão de erro, ajuste as listas no `config.yaml`.

## Quando algo quebra

O endereço de busca da Gupy é o que o próprio portal usa, mas não é uma API oficial e pode mudar. Isso já aconteceu em out/2026. O robô foi feito para **não falhar em silêncio**:
- o painel mostra a fonte em vermelho ("com problema");
- a execução no GitHub fica vermelha ❌ e o GitHub te manda e-mail;
- as outras fontes continuam funcionando, e as vagas que já estão no painel não são marcadas como encerradas por engano.

Se acontecer: em **Actions**, abra a execução vermelha, clique em **Coletar vagas** e copie o erro. Com ele dá para corrigir o endereço (no topo de `radar/fontes.py`). Se quiser, me mande o erro que eu corrijo.

Se uma empresa do Greenhouse/Lever mudar de sistema, ela só gera um aviso. Basta tirá-la do `config.yaml`.

## Problemas comuns na instalação

- **A pasta `.github` não subiu.** No Mac, pastas que começam com ponto ficam escondidas (aperte `Cmd + Shift + .` no Finder para mostrar). Outra opção: no repositório, clique em **Add file → Create new file**, digite o nome `.github/workflows/coleta.yml`, cole o conteúdo desse arquivo do zip e faça o commit.
- **Erro `403` / `Permission denied` no passo "Salvar resultado".** Refaça o passo 3 da instalação.
- **O painel diz 404.** Espere 2 minutos depois do passo 4 e confira se escolheu a pasta `/docs`.
- **A coleta parou de rodar sozinha.** O GitHub pausa agendamentos de repositórios sem atividade por 60 dias. Os commits diários do robô normalmente evitam isso. Se acontecer, vá em Actions e clique em **Enable workflow**.

## Rodar no seu computador (opcional)

```bash
pip install -r requirements.txt
python -m radar          # coleta de verdade
python -m pytest -q      # testes do filtro
python -m radar --demo   # painel com vagas fictícias, sem internet
```
Depois abra `docs/index.html` no navegador.

## Estrutura

```
config.yaml               suas preferências
radar/fontes.py           leitura da Gupy, Greenhouse e Lever
radar/filtros.py          regras de área, nível e local
radar/coletor.py          junta tudo, mantém o histórico e grava o painel
docs/index.html           o painel
docs/vagas.json|.js       os dados (atualizados pelo robô)
novas_hoje.md             lista das novas da última coleta
.github/workflows/        agendamento diário
tests/                    testes do filtro
```
