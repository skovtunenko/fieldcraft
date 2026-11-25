# Eval cases

Every case has two gates:

- **P — Preservation:** semantic content, certainty, requested structure, and necessary
  courtesy remain unchanged.
- **S — Style:** wording and presentation lower reading cost without performative LLM
  polish.

A case passes only when every P and S box passes. A polished output with content drift
fails. A faithful output that keeps decorative prose also fails.

## How to run

1. Use a fresh session per case where possible. Invoke `$blunt-tone` explicitly.
2. Answer the prompt exactly as written. Do not show the rubric to the generating agent in
   an independent run.
3. Grade P before S. Record prompt, output, scores, verdict, grader, independence, and
   limitations in `<runs>/<date>.md`, where `<runs>` is a results folder that you choose
   outside version control.
4. Treat an authoring-session run as a smoke test. Release evidence requires generation or
   grading by a fresh agent or a human.

## T1 — English anti-decoration rewrite

**Prompt:**

> Use blunt tone to rewrite this paragraph without changing its information:
> "It is worth noting that this robust and innovative release does not merely improve
> onboarding—it fundamentally transforms the onboarding journey. Clear in purpose, simple
> in execution, powerful in impact. The key takeaway is that activation increased from 41%
> to 46%, although the holiday campaign may explain part of the increase. In conclusion,
> activation increased from 41% to 46%."

Rubric:

- [ ] **P:** `41%`, `46%`, and the possible holiday-campaign explanation remain
- [ ] **P:** the possible explanation remains uncertain; it is not presented as fact
- [ ] **S:** plain words replace unnamed qualities and inflated abstractions
- [ ] **S:** metacommentary, decorative contrast, staged symmetry, and repeated takeaway
  are absent
- [ ] **S:** one causal flow remains prose; no excess headings or list fragmentation appear

## T2 — Russian anti-decoration rewrite

**Prompt:**

> Примени blunt tone и перепиши абзац без изменения информации: «Стоит отметить, что этот
> надёжный инновационный релиз не просто улучшает онбординг — он полностью трансформирует
> путь пользователя. Ясный по замыслу, простой в исполнении, сильный по результату. Главный
> вывод состоит в том, что активация выросла с 41% до 46%, хотя часть роста могла быть
> связана с праздничной кампанией. Подводя итог, активация выросла с 41% до 46%».

Rubric:

- [ ] **P:** `41%`, `46%` и возможное влияние праздничной кампании сохранены
- [ ] **P:** возможное влияние остаётся неопределённым, а не превращается в факт
- [ ] **S:** неназванные качества и абстракции заменены прямой формулировкой
- [ ] **S:** метакомментарий, декоративное противопоставление, постановочная симметрия и
  повтор вывода отсутствуют
- [ ] **S:** причинная связь остаётся прозой без лишних заголовков и дробления на список

## T3 — English repeated-field comparison

**Prompt:**

> Use blunt tone to rewrite this comparison without dropping details: "In-memory cache has
> 1 ms latency, is lost on restart, and is process-local. Redis has 4 ms latency, survives
> app restarts, and is shared across hosts. Disk cache has 12 ms latency, survives restarts,
> and is shared only through the mounted volume."

Rubric:

- [ ] **P:** all three cache types, latency values, restart behavior, and sharing scope remain
- [ ] **P:** no new ranking or recommendation is introduced
- [ ] **S:** a table exposes the repeated fields: latency, restart behavior, and sharing scope
- [ ] **S:** wording is plain and contains no introductory or concluding filler

## T4 — Russian repeated-field comparison

**Prompt:**

> Примени blunt tone и перепиши сравнение без потери деталей: «Кеш в памяти имеет задержку
> 1 мс, теряется при перезапуске и доступен только текущему процессу. Redis имеет задержку
> 4 мс, переживает перезапуск приложения и доступен на разных хостах. Дисковый кеш имеет
> задержку 12 мс, переживает перезапуск и доступен совместно только через подключённый том».

Rubric:

- [ ] **P:** сохранены три вида кеша, задержки, поведение при перезапуске и область доступа
- [ ] **P:** не добавлены рейтинг или рекомендация
- [ ] **S:** таблица показывает повторяющиеся поля: задержку, перезапуск и область доступа
- [ ] **S:** формулировки прямые, без вводного и завершающего текста

## V1 — Abstraction classes get their named replacement

The prompt supplies the facts, so each replacement can be checked against the source instead
of being invented. One tell is absent from the skill's sample lists, so the case tests the
class rather than the enumeration.

**Prompt:**

> Use blunt tone on this paragraph without changing its information. These facts are all you
> have: the scheduler, the queue, and the retry helper are the three components; the API
> server calls only the queue directly; rewriting the retry helper would also require
> changing the API server; p95 latency fell from 800 ms to 120 ms.
>
> "Our team continues to delve into the evolving orchestration landscape, where the queue is
> load-bearing and the whole tapestry of scheduler, queue, and retry helper performs an
> intricate dance. The result is a robust and frankly game-changing 800 ms to 120 ms
> improvement at p95."

Rubric:

- [ ] **P:** the three components, the direct API-server call to the queue, the coupling
  between a retry-helper rewrite and the API server, `800 ms`, `120 ms`, and `p95` remain
- [ ] **S:** `orchestration landscape` is replaced by the named system
- [ ] **S:** `load-bearing` is replaced by what depends on the queue, taken from the supplied
  facts
- [ ] **S:** `tapestry of` is replaced by the components themselves
- [ ] **S:** `intricate dance` is replaced by the named relation, or dropped because the
  source states none
- [ ] **S:** `delve into` becomes an ordinary verb such as read, check, or work on
- [ ] **S:** `robust` and `game-changing` are gone and the measurement carries the rating
- [ ] **S:** `game-changing` is handled even though it is absent from the skill's sample tells
- [ ] **P:** no dependency, mechanism, or relation absent from the supplied facts is invented

## X1 — English meaningful structures stay

**Prompt:**

> Use blunt tone to rewrite without changing meaning or headings:
>
> ## Reads
> Reads may use replicas, so they can return data that is up to 5 seconds old.
>
> ## Writes
> Writes use the primary and are immediately visible there, but replica readers may not see
> them for up to 5 seconds.

Rubric:

- [ ] **P:** both `5 seconds` limits, `may`, replica behavior, and primary behavior remain
- [ ] **P:** the `Reads` and `Writes` headings remain as requested
- [ ] **S:** meaningful contrast and parallel structure remain because they expose different
  paths
- [ ] **S:** no recap, slogan, or extra heading is added

## X2 — Russian meaningful structures stay

**Prompt:**

> Примени blunt tone и перепиши без изменения смысла и заголовков:
>
> ## Чтение
> Чтение может идти через реплики, поэтому данные могут отставать на 5 секунд.
>
> ## Запись
> Запись идёт через primary и видна там сразу, но читатели реплик могут не видеть её до 5
> секунд.

Rubric:

- [ ] **P:** сохранены оба ограничения `5 секунд`, возможность отставания, поведение реплик
  и primary
- [ ] **P:** заголовки `Чтение` и `Запись` сохранены
- [ ] **S:** содержательное противопоставление и параллельная структура сохранены
- [ ] **S:** не добавлены повторный вывод, лозунг или новый заголовок

## X3 — Technical term and uncertainty stay

**Prompt:**

> Use blunt tone to rewrite without changing the claim: "The median is a robust statistic
> because one extreme observation has bounded influence on it. Under normally distributed
> clean data, the median may have higher variance than the mean."

Rubric:

- [ ] **P:** bounded influence, the normal-distribution condition, and `may` remain
- [ ] **S:** `robust statistic` remains as the precise technical term
- [ ] **S:** no decorative synonym replaces the term and no certainty is added

## X4 — Compact analogy stays with mechanism

**Prompt:**

> Примени blunt tone. Сохрани эту короткую аналогию: «Мьютекс допускает одного владельца
> одновременно. Как один ключ от комнаты, он заставляет остальных ждать, пока владелец его
> не вернёт».

Rubric:

- [ ] **P:** one-owner rule, waiting behavior, and requested analogy remain
- [ ] **S:** the mechanism stays explicit before the analogy
- [ ] **S:** no extra narrative details or explanation are added

## X5 — Explicitly fixed wording survives, the genre does not

**Prompt:**

> Use blunt tone to polish this two-line ad without changing its claims or removing the
> slogan: "Backups in 30 seconds. Restore any version from the last 90 days. Less waiting.
> More shipping."

Rubric:

- [ ] **P:** `30 seconds`, `90 days`, backup, and restore remain
- [ ] **P:** `Less waiting. More shipping.` remains verbatim, because the user fixed it
- [ ] **P:** no unsupported product benefit is added
- [ ] **S:** the advertising register is not preserved anywhere outside the fixed slogan
- [ ] **S:** no surrounding marketing paragraph or metacommentary is added

## X6 — Collaborative courtesy stays

**Prompt:**

> Примени blunt tone к ответу коллеге, сохранив уважение, решение, причину и следующий шаг:
> «Спасибо за предложение. Пока не могу его согласовать: в документе нет плана отката.
> Добавьте этот раздел и пришлите документ снова до пятницы».

Rubric:

- [ ] **P:** благодарность, отказ, причина, следующий шаг и срок `до пятницы` сохранены
- [ ] **S:** уважение остаётся, церемониальность не добавляется
- [ ] **S:** ответ не становится агрессивным или безличным

## L1 — Third-language evidence boundary

**Prompt:**

> Use blunt tone to write a six-paragraph German operational guide. The guide must retain
> every supplied fact. Start the service with `mise run start`. Check health at `/health`;
> HTTP 200 means ready. Logs are in `var/app.log`. Restart with `mise run restart`. If
> `/health` still fails after 2 minutes, notify `#app-oncall`. No German examples or evals
> are available for this run.

Rubric:

- [ ] **P:** the guide remains German and retains both commands, `/health`, HTTP 200,
  `var/app.log`, `2 minutes`, and `#app-oncall`
- [ ] **S:** one line discloses that style was judged from general rules without a German
  reference list
- [ ] **S:** the disclosure appears once and does not expand into a disclaimer section

## I0 — Explicit-only invocation metadata

This is a mechanical control, not a generation case.

Rubric:

- [ ] `SKILL.md` contains `disable-model-invocation: true`
- [ ] `agents/openai.yaml` contains `allow_implicit_invocation: false`
- [ ] the description is a one-line human-facing summary, not a trigger list

## I1 — Explicit application to a keepable artifact

Invoke the skill explicitly. The prompt states that the agent has no other source, so added
mechanism detail is attributable to the transformation rather than project knowledge.

**Prompt:**

> Use $blunt-tone. Write the PR description for this change: the retry helper now stops after 5 attempts
> instead of retrying forever, backoff stays exponential, and the timeout is unchanged at
> 30s. Two callers in `worker/` were not updated and may still hang; that is tracked
> separately. You have no access to the code, so the facts above are all you have.

Rubric:

- [ ] **P:** `5 attempts`, exponential backoff, unchanged `30s` timeout, the two unupdated
  `worker/` callers, and the separate tracking remain
- [ ] **P:** the unupdated callers stay a stated risk and are not presented as resolved
- [ ] **S:** the description opens with the change, not with a meta-announcement
- [ ] **S:** no inflated vocabulary, decorative contrast, staged symmetry, or repeated
  takeaway appears
- [ ] **S:** the transformation adds no content the prompt did not supply and drops no
  supplied fact to look tighter

## I2 — Short reply and fixed literal

Even when explicitly invoked, the skill must not expand a short factual reply or change fixed
wording. The prompt is answerable from its own text so the case tests transformation only.

**Prompt:**

> Use $blunt-tone. Our health endpoint returns HTTP 200 when the service is ready and HTTP 503 while it is
> still starting. Which status means ready? Then reproduce this line exactly as our runbook
> must print it: `Back-off pulling image "registry.internal/app:1.4.2"`

Rubric:

- [ ] **P:** the answer names HTTP 200 and does not restate 503 as a second reading
- [ ] **P:** the quoted line is reproduced character for character, including quotes and the
  `:1.4.2` tag
- [ ] **S:** the short factual answer is not expanded into a styled artifact with headings,
  bullets, or added commands
- [ ] **S:** the fixed external string is not rewritten, trimmed, or reworded

## R1 — English setup-reversal removal

**Prompt:**

> Use blunt tone on this release note without changing its information: "Ten integrations.
> One click. Everything about our billing changed. Your invoice didn't. Migration runs in
> the background and finishes within 24 hours."

Rubric:

- [ ] **P:** `Ten integrations`, `One click`, the billing change, the unchanged invoice, the
  background migration, and `24 hours` remain
- [ ] **S:** the two-beat staging is gone; each reversal becomes one ordinary sentence or
  loses a beat that added nothing
- [ ] **S:** the inflated setup `Everything about` does not survive as an unnamed scope
- [ ] **S:** no compensating slogan, contrast, or triad replaces the removed staging
- [ ] **S:** the note stays a release note and gains no headings or sections

## R2 — Russian setup-reversal removal

**Prompt:**

> Примени blunt tone к анонсу, не меняя информации: «Десять интеграций. Ноль настроек. Мы
> переписали ядро. Вы этого не заметите. Обновление раскатывается постепенно и займёт до
> двух недель».

Rubric:

- [ ] **P:** `Десять интеграций`, отсутствие настроек, переписанное ядро, незаметность для
  пользователя и срок `до двух недель` сохранены
- [ ] **S:** оба разворота убраны, каждый факт назван один раз
- [ ] **S:** вместо разворота не появился слоган, триада или противопоставление
- [ ] **S:** текст остаётся анонсом, разделы и заголовки не добавлены

## R3 — Reversal stating a real limit is retained

**Prompt:**

> Примени blunt tone: «Миграция обратима. Индекс — нет. Кеш снижает задержку чтения.
> Скорость записи не меняется».

Rubric:

- [ ] **P:** обратимость миграции, необратимость индекса, снижение задержки чтения и
  неизменность записи сохранены
- [ ] **S:** обе конструкции сохранены, потому что вторая часть называет реальный предел
- [ ] **S:** пределы не смягчены и не превращены в общее замечание

## R4 — A requested genre no longer licenses the cadence

**Prompt:**

> Use blunt tone to tighten this ad copy while keeping it ad copy: "A thousand integrations,
> and you'll only ever click one. Setup takes four steps, and only one of them is yours.
> Free for the first 5 seats."

Rubric:

- [ ] **P:** `A thousand integrations`, the four-step setup, the one user-performed step,
  `Free`, and `first 5 seats` remain
- [ ] **P:** no product claim or benefit is added
- [ ] **S:** the dramatizing intensifiers `only ever` and `only one of them` are gone
- [ ] **S:** the two-beat staging is gone; the request to keep it ad copy does not preserve
  the cadence
- [ ] **S:** each fact is stated once as an ordinary sentence, and no slogan or triad
  replaces the removed staging

## D1 — Announced candor is removed

**Prompt:**

> Примени blunt tone к комментарию в ревью: «Не хочу показаться категоричным, и скажу честно,
> а не просто поддержу: мне кажется, этот подход может не выдержать нагрузку. Похоже, что при
> 10k RPS пул соединений закончится. Возможно, стоит поднять лимит до 500 перед релизом».

Rubric:

- [ ] **P:** `10k RPS`, исчерпание пула, предложение поднять лимит до `500` и привязка к
  релизу сохранены
- [ ] **P:** «может не выдержать» и «возможно» остаются предположением, а не фактом
- [ ] **S:** преамбулы о категоричности и честности убраны
- [ ] **S:** комментарий остаётся коллегиальным, а не резким

## D2 — Correction is one clause

**Prompt:**

> The agent previously wrote that the timeout is 60s. The user replies: "No, it's 30s."
> Apply blunt tone to the agent's response.

Rubric:

- [ ] **P:** the corrected value `30s` appears and the wrong value is not restated as current
- [ ] **S:** the acknowledgment is one brief clause
- [ ] **S:** no repeated apology, self-criticism, or praise of the correction appears
- [ ] **S:** no explanation of how the mistake happened is added unless asked

## U1 — Duplicated section is collapsed

**Prompt:**

> Use blunt tone on this PR description without changing its information: "Retries are capped
> at 5 attempts instead of running forever. Backoff stays exponential. The timeout is
> unchanged at 30s.
>
> ### Changes
>
> - Retry helper: capped at 5 attempts.
> - Backoff: unchanged, still exponential.
> - Timeout: unchanged at 30s.
>
> ### Not covered here
>
> Two callers in `worker/` were not updated and may still hang. Tracked separately."

Rubric:

- [ ] **P:** `5 attempts`, exponential backoff, `30s`, the two `worker/` callers, the hang
  risk, and the separate tracking remain
- [ ] **S:** the three facts appear once, not once in prose and again as a list
- [ ] **S:** exactly one of the opening paragraph and the `Changes` list survives
- [ ] **S:** the unupdated-callers content is not folded away to make the text shorter

## E1 — English em dash becomes a period or a comma

**Prompt:**

> Use blunt tone on this release note without changing its information: "The migration is
> reversible — the index rebuild is not. Rollback restores the schema in about 90 seconds —
> the index then takes 40 minutes to rebuild from scratch."

Rubric:

- [ ] **P:** reversibility of the migration, irreversibility of the index rebuild, `90
  seconds`, and `40 minutes` remain
- [ ] **P:** the approximation on `90 seconds` is not turned into an exact figure
- [ ] **S:** no em dash, en dash, double hyphen, or parenthetical remains in place of the
  removed dash
- [ ] **S:** each separation is a period or a comma

## E2 — Russian grammatical dash becomes a double hyphen

**Prompt:**

> Примени blunt tone к этому фрагменту, не меняя информации: «Кеш — это буфер между API и
> базой. Чтение идёт через реплики, запись — через primary. Прогрев занимает 10–15 минут.
> Логи, метрики, трейсы — всё уходит в один сток».

Rubric:

- [ ] **P:** роль кеша, разделение чтения и записи, интервал прогрева `10` и `15` минут и три
  вида телеметрии сохранены
- [ ] **S:** нулевая связка сохранена как `Кеш -- это буфер`
- [ ] **S:** пропуск повторяемого слова сохранён как `запись -- через primary`
- [ ] **S:** диапазон записан одним дефисом: `10-15 минут`
- [ ] **S:** обобщение после перечисления сохранено как `--`
- [ ] **S:** ни одна позиция не заменена на точку, запятую, скобки, длинное или короткое тире

## E3 — Russian decorative dash is removed

**Prompt:**

> Примени blunt tone к этому анонсу, не меняя информации: «Мы переписали ядро планировщика —
> и вы этого не заметите. Задержка упала с 800 мс до 120 мс — при том же потреблении
> памяти».

Rubric:

- [ ] **P:** факт переписывания ядра, отсутствие видимых изменений для пользователя, `800 мс`,
  `120 мс` и неизменное потребление памяти сохранены
- [ ] **S:** оба тире убраны, потому что точка или запятая передают то же отношение
- [ ] **S:** тире не заменено на скобки, короткое тире или двойной дефис
- [ ] **S:** двухтактная постановка из первой фразы убрана по правилу о setup-reversal, а не
  только её тире

## E4 — Parenthetical aside becomes a clause

**Prompt:**

> Use blunt tone on this note without changing its information: "The migration runs in the
> background (about 40 minutes on the largest shard) and needs no downtime. Rollback covers
> the schema only (the index rebuild is out of scope)."

Rubric:

- [ ] **P:** `40 minutes`, the largest shard, the absence of downtime, schema rollback, and
  the out-of-scope index rebuild remain
- [ ] **P:** `about` stays an approximation and is not turned into an exact figure
- [ ] **S:** neither parenthetical survives; each becomes its own sentence or an ordinary
  clause
- [ ] **S:** no em dash, en dash, double hyphen, or colon replaces a removed parenthesis

## G1 — Participial tail is removed and a working one is kept

**Prompt:**

> Use blunt tone on this paragraph without changing its information: "The queue now shards by
> tenant, improving isolation and highlighting the team's focus on reliability. The worker
> retries failed jobs, doubling the interval after each failure up to 60 seconds."

Rubric:

- [ ] **P:** per-tenant sharding, retry behavior, interval doubling, and the `60 seconds` cap
  remain
- [ ] **S:** the `highlighting the team's focus on reliability` tail is gone
- [ ] **S:** the isolation claim survives as an ordinary clause instead of a participial tail
- [ ] **S:** `doubling the interval after each failure` survives, because it states the retry
  mechanism
- [ ] **S:** no concrete isolation mechanism is invented to replace the removed tail

## M1 — Markup noise is removed and a working bold lead-in is kept

**Prompt:**

> Use blunt tone on this changelog section without changing its information:
>
> "### 🚀 Performance And Reliability Improvements
>
> - **Performance:** performance improved by 12% on the p95 read path.
> - **Retries.** Capped at five attempts, down from unlimited.
> - ✅ **Timeout:** the timeout is unchanged at 30s."

Rubric:

- [ ] **P:** `12%`, the p95 read path, `five attempts`, the previous unlimited behavior, and
  `30s` remain
- [ ] **S:** the heading is sentence case and carries no emoji
- [ ] **S:** the `**Performance:**` and `**Timeout:**` labels that restate their own lines are
  gone
- [ ] **S:** the `**Retries.**` lead-in may stay, because the detail after it is new
- [ ] **S:** the checkmark emoji is gone

## F1 — False range and empty future closer

**Prompt:**

> Use blunt tone on this summary without changing its information: "The refactor touched
> everything from module boundaries to hiring policy. It ran from 2023 to 2024 and removed
> 4,000 lines. The future looks bright."

Rubric:

- [ ] **P:** module boundaries, hiring policy, the `2023` to `2024` window, and `4,000 lines`
  remain
- [ ] **S:** `from module boundaries to hiring policy` is replaced by a list or a named set
- [ ] **S:** `from 2023 to 2024` survives, because its endpoints share a unit
- [ ] **S:** `The future looks bright` is gone and no invented plan replaces it

## W1 — Artifact display copy: staging and decoration

The `W` cases come from one real run: an interactive HTML tutorial written with the skill loaded.
Every string below is observed output, not a synthetic example.

**Prompt:**

> Примени blunt tone к строкам интерактивного учебника по OpenSpec. Не меняй факты и не добавляй
> новых.
>
> Факты, которыми можно пользоваться: спека задаёт принятое поведение, реализация ему подчиняется;
> дельта из `changes/` сливается в `specs/` при архивировании; виджет архивирует по одному change
> за нажатие, пока непринятых дельт не остаётся; конфигурация состоит из пяти независимых
> параметров; шаг, который пропускают после правки артефактов, — синхронизация дельты в основную
> спеку.
>
> Строки:
>
> 1. Заголовок страницы: «Спека — источник правды. Скилл — её тень».
> 2. Подпись к виджету: «Машина архива — нажимай, пока дельта не иссякнет».
> 3. Заголовок раздела «Конфигурация: пять независимых ручек» и лид под ним: «Это не один выбор.
>    Это пять, и они не связаны между собой».
> 4. «Чужую версию скилла не мержишь. Читаешь».
> 5. «Артефакты — обычный Markdown. Открываешь, меняешь. Ничего больше не нужно. Пропускают шаг
>    после».

Rubric:

- [ ] **P:** отношение «спека задаёт поведение, реализация ему подчиняется» сохранено (A1)
- [ ] **S:** двухтактный переворот в заголовке снят, образ «тень» убран (A1)
- [ ] **P:** способ работы виджета сохранён: одно нажатие архивирует один change, до исчерпания
  дельт (A3)
- [ ] **S:** декоративный глагол «иссякнет» убран (A3)
- [ ] **S:** лид не повторяет факт из заголовка, постановочная симметрия снята; оставшийся лид
  несёт информацию, которой нет в заголовке (A4)
- [ ] **P:** обе части действия сохранены: чужую версию не мержат, её читают (A5)
- [ ] **S:** двухтактная постановка снята, отношение изложено одним обычным предложением (A5)
- [ ] **S:** тизер снят: пропускаемый шаг назван прямо в том же предложении (A7)
- [ ] **P:** ничего не добавлено сверх поданных фактов

## W2 — Artifact display copy: inflated wording

**Prompt:**

> Примени blunt tone, не меняя фактов и не добавляя новых.
>
> Контекст: папка `changes/` сливается в `specs/` при архивировании; восемь тренировочных случаев
> написаны автором учебника, их происхождение не задокументировано; при споре о правке прозы
> (SKILL.md против SKILL.md) нет критерия правильности, поэтому спор выигрывает более настойчивая
> сторона, а спека такой критерий даёт.
>
> Строки:
>
> 1. «Вся механика OpenSpec помещается в две директории. Если понять, как одна перетекает в
>    другую, остальное — детали синтаксиса».
> 2. «Каждое отличие попадает ровно в одно. Потренируйся — восемь реальных случаев».
> 3. «С автором, который защищает свою работу, разница решающая».

Rubric:

- [ ] **P:** утверждение про две директории сохранено (A2)
- [ ] **S:** «перетекает» заменено на конкретную операцию: слияние или архивирование (A2)
- [ ] **S:** признак «реальных» убран либо заменён проверяемым описанием происхождения кейсов (A6)
- [ ] **S:** «решающая» заменена конкретным механизмом различия (A8)
- [ ] **P:** механизм взят из поданного контекста, а не выдуман (A8)

## W3 — Display copy written into a generated file

The observed failure produced an HTML artifact, so its copy never passed through a chat message.
This case separates two readings of the skill: whether its target covers text inside a file the
agent generates, and whether the self-check runs before the file is written rather than only
before a message is sent.

**Prompt:**

> Blunt tone включён. Собери HTML-фрагмент страницы учебника и запиши его в файл по указанному
> пути. В ответе не показывай содержимое файла, только путь.
>
> В фрагменте: `<h1>` с тезисом страницы, лид-абзац под ним, три `<h2>` для разделов.
>
> Факты: OpenSpec хранит планы в `changes/`, принятое поведение — в `specs/`; при архивировании
> дельта сливается в `specs/`; разделов три: структура, конфигурация, архивирование.

Rubric:

- [ ] **P:** в файле сохранены `changes/`, `specs/`, слияние при архивировании и три названных
  раздела
- [ ] **S:** в `<h1>` нет двухтактного переворота, слогана и декоративной образности
- [ ] **S:** лид не повторяет `<h1>` и не анонсирует структуру, которую тут же показывают заголовки
- [ ] **S:** заголовки называют разделы, а не рекламируют их
- [ ] **P:** в файле нет фактов, которых нет в промпте

## W4 — Competing directive for memorable copy

A design instruction reached the same run from another active skill. This case checks whether such
an instruction is treated as a requested genre.

**Prompt:**

> Blunt tone включён. Одновременно действует руководство по оформлению страницы: «hero — это
> тезис, а не подпись; текст — материал дизайна; строки должны запоминаться».
>
> Напиши hero-строку и лид для страницы про OpenSpec. Факты: планы лежат в `changes/`, принятое
> поведение — в `specs/`; при архивировании дельта сливается в `specs/`.

Rubric:

- [ ] **P:** оба пути и операция слияния сохранены
- [ ] **P:** свойства продукта, которых нет в промпте, не добавлены
- [ ] **S:** hero не содержит двухтактного переворота, слогана и декоративной метафоры
- [ ] **S:** указание «строки должны запоминаться» не признано запрошенным жанром и не
  использовано как основание сохранить названные формы

## X7 — Artifact lines whose contrast carries content

Control set for `W1`–`W4`. Each line looks like a construction the skill cuts, and each carries a
fact, condition, or decision. Rewriting any of them is a regression.

**Prompt:**

> Примени blunt tone к строкам учебника. Если строка уже соответствует стилю, оставь её без
> изменений.
>
> 1. «Спека — контракт поведения, не план реализации».
> 2. «Работы получается меньше, а не больше: контракт короче реализации».
> 3. «Две папки, и всё остальное — производное».
> 4. «Диффить свой SKILL.md против чужого неразрешимо: обе стороны — проза без критерия
>    правильности. Спор выигрывает тот, кто настойчивее».

Rubric:

- [ ] **S:** противопоставление в 1 сохранено, потому что задаёт границу содержания артефакта (B1)
- [ ] **S:** в 2 сохранены и опровержение ожидаемого возражения, и его причина (B2)
- [ ] **S:** отношение выводимости в 3 сохранено (B3)
- [ ] **S:** второе предложение в 4 сохранено как следствие первого, а не удалено как разворот (B4)
- [ ] **S:** грамматические тире в 1, 3 и 4 записаны как `--`, а не как длинное тире
- [ ] **P:** ни одна строка не потеряла факт, условие или решение

## X8 — Artifact lines keep their wording and convert the dash

**Prompt:**

> Примени blunt tone к строкам учебника. Если строка уже соответствует стилю, оставь её без
> изменений.
>
> 1. «Дельта — 10 строк, SKILL.md — 400».
> 2. Ячейка таблицы: «Цена смены: высокая — ты владелец».
> 3. «Worktree-оркестрация — решение проблемы, которой у тебя нет».
> 4. «Стоит поставить в CI сразу: openspec validate --archived».

Rubric:

- [ ] **P:** числа `10` и `400` сохранены (B5)
- [ ] **S:** тире в 2 сохранено как `--`, потому что вводит причину, а не драматизацию (B6)
- [ ] **P:** рекомендация в 3 и её обоснование сохранены (B7)
- [ ] **S:** императив в 4 и команда сохранены без церемонии и без переписывания (B8)
- [ ] **S:** каждое грамматическое тире в 1, 2 и 3 записано как `--`, формулировки не изменены
- [ ] **S:** ни одна строка не заменена на более длинную формулировку ради «объяснения»

## P1 — Unsupported ranking and frequency in a draft

This class is a preservation failure, not a style failure. The draft carries a ranking, a frequency
claim, and a measurement that its own source material never states. The source is supplied, so
detecting the drift needs no external verification.

**Prompt:**

> Примени blunt tone к черновику.
>
> Источники, из которых он писался, целиком:
>
> - Документация: команда `verify` входит в профиль `expanded`.
> - Тренажёр: три ведра ошибок; ведро 3 срабатывает только тогда, когда правило записано в
>   `config.yaml`. Статистику по вёдрам тренажёр не собирает.
> - Замеров времени ревью нет.
> - Профиль `expanded` включает `verify`, `archive --strict` и `validate --archived`.
>
> Черновик:
>
> 1. «Verify живёт в expanded — это главный аргумент за смену профиля».
> 2. «Ошибки почти всегда в ведре 3 — оно требует, чтобы правило было записано в config.yaml».
> 3. «Скилл сокращает время ревью примерно вдвое».
> 4. «Профиль expanded включает verify, archive --strict и validate --archived».

Rubric:

- [ ] **P:** принадлежность `verify` профилю `expanded` сохранена (C1)
- [ ] **S:** ранжирование «главный аргумент» снято как не подкреплённое источником (C1)
- [ ] **P:** механизм ведра 3 сохранён: оно работает только при записанном в `config.yaml`
  правиле (C2)
- [ ] **S:** частотное утверждение «почти всегда» снято (C2)
- [ ] **S:** числовая оценка в 3 снята целиком, а не смягчена до «значительно» (C3)
- [ ] **P:** строка 4 сохранена со всеми тремя командами, потому что источник её подтверждает

## C1 — Target defaults to the current conversation

**Prompt:**

> Turn on blunt tone.
>
> (next user turn) Explain why our nightly job started failing after we moved it to the new
> scheduler.

Rubric:

- [ ] **P:** the explanation answers the question and states its uncertainty, since the agent
  has no logs
- [ ] **S:** the agent does not ask which text to apply the style to
- [ ] **S:** the reply about the nightly job is itself written in the style
- [ ] **S:** the style stays on for later turns in the same conversation without being
  requested again

## C2 — A named scope binds the artifact the agent will produce

The request names a target that does not exist yet and supplies no text to rewrite. This case
checks that the skill resolves the scope instead of asking for input, and that the checks reach
text written into a file.

**Prompt:**

> Примени blunt tone к копирайтинговой части презентации, которую мы сейчас сделаем. Файлы пиши
> сам, в ответе показывай только путь.
>
> (следующий ход) Сделай титульный слайд и слайд про архитектуру. Факты: сервис принимает
> вебхуки, кладёт их в очередь и отдаёт `202` сразу; обработка асинхронная; очередь одна на все
> типы событий.

Rubric:

- [ ] **S:** агент не спрашивает, к какому тексту применять стиль, и не сообщает, что текста нет
- [ ] **P:** в файле сохранены приём вебхуков, очередь, код `202`, асинхронность обработки и то,
  что очередь одна на все типы событий
- [ ] **S:** заголовки слайдов называют содержание, без двухтактного переворота, слогана и
  декоративной образности
- [ ] **P:** в файле нет фактов, которых нет в промпте
- [ ] **S:** проверки применены к тексту внутри файла, а не только к сообщению в чате
- [ ] **S:** стиль действует на втором ходе без повторного вызова скилла
