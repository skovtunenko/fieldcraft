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

## T5 — Ukrainian anti-decoration rewrite

Pairs with T1 (English) and T2 (Russian).

**Prompt:**

> Застосуй blunt tone і перепиши абзац без зміни інформації: «Варто зазначити, що цей
> надійний інноваційний реліз не просто покращує онбординг — він повністю трансформує шлях
> користувача. Зрозумілий за задумом, простий у виконанні, потужний за результатом. Головний
> висновок полягає в тому, що активація зросла з 41% до 46%, хоча частина зростання могла
> бути пов’язана зі святковою кампанією. Підсумовуючи, активація зросла з 41% до 46%».

Rubric:

- [ ] **P:** `41%`, `46%` і можливий вплив святкової кампанії збережено
- [ ] **P:** можливий вплив лишається припущенням, а не стає фактом
- [ ] **S:** неназвані якості й абстракції замінено прямим формулюванням
- [ ] **S:** метакоментаря, декоративного протиставлення, постановочної симетрії та повтору
  висновку немає
- [ ] **S:** причиновий зв’язок лишається прозою без зайвих заголовків і дроблення на список

## T6 — Ukrainian repeated-field comparison

Pairs with T3 (English) and T4 (Russian).

**Prompt:**

> Застосуй blunt tone і перепиши порівняння без втрати деталей: «Кеш у пам’яті має затримку
> 1 мс, втрачається під час перезапуску й доступний лише поточному процесу. Redis має затримку
> 4 мс, переживає перезапуск застосунку й доступний на різних хостах. Дисковий кеш має
> затримку 12 мс, переживає перезапуск і доступний спільно лише через підключений том».

Rubric:

- [ ] **P:** збережено три види кешу, затримки, поведінку під час перезапуску й область доступу
- [ ] **P:** рейтингу чи рекомендації не додано
- [ ] **S:** таблиця показує повторювані поля: затримку, перезапуск і область доступу
- [ ] **S:** формулювання прямі, без вступного й завершального тексту

## X9 — Ukrainian meaningful structures stay

Pairs with X1 (English) and X2 (Russian).

**Prompt:**

> Застосуй blunt tone і перепиши без зміни змісту й заголовків:
>
> ## Читання
> Читання може йти через репліки, тому дані можуть відставати на 5 секунд.
>
> ## Запис
> Запис іде через primary і видимий там одразу, але читачі реплік можуть не бачити його до 5
> секунд.

Rubric:

- [ ] **P:** збережено обидва обмеження `5 секунд`, можливість відставання, поведінку реплік
  і primary
- [ ] **P:** заголовки `Читання` і `Запис` збережено
- [ ] **S:** змістове протиставлення й паралельну структуру збережено
- [ ] **S:** повторного висновку, гасла чи нового заголовка не додано

## X10 — English compact analogy stays with mechanism

Pairs with X4 (Russian) and X11 (Ukrainian).

**Prompt:**

> Use blunt tone. Keep this short analogy: "A mutex allows one owner at a time. Like a single
> key to a room, it makes everyone else wait until the owner returns it."

Rubric:

- [ ] **P:** one-owner rule, waiting behavior, and requested analogy remain
- [ ] **S:** the mechanism stays explicit before the analogy
- [ ] **S:** no extra narrative details or explanation are added

## X11 — Ukrainian compact analogy stays with mechanism

Pairs with X4 (Russian) and X10 (English).

**Prompt:**

> Застосуй blunt tone. Збережи цю коротку аналогію: «М’ютекс допускає одного власника
> одночасно. Як один ключ від кімнати, він змушує інших чекати, доки власник його не
> поверне».

Rubric:

- [ ] **P:** one-owner rule, waiting behavior, and requested analogy remain
- [ ] **S:** the mechanism stays explicit before the analogy
- [ ] **S:** no extra narrative details or explanation are added

## X12 — English collaborative courtesy stays

Pairs with X6 (Russian) and X13 (Ukrainian).

**Prompt:**

> Use blunt tone on this reply to a colleague, keeping the respect, the decision, the reason,
> and the next step: "Thanks for the proposal. I can't approve it yet: the document has no
> rollback plan. Please add that section and send the document again by Friday."

Rubric:

- [ ] **P:** the thanks, the refusal, the reason, the next step, and the `by Friday` deadline
  remain
- [ ] **S:** respect stays and no ceremony is added
- [ ] **S:** the reply does not become aggressive or impersonal

## X13 — Ukrainian collaborative courtesy stays

Pairs with X6 (Russian) and X12 (English).

**Prompt:**

> Застосуй blunt tone до відповіді колезі, зберігши повагу, рішення, причину й наступний
> крок: «Дякую за пропозицію. Поки не можу її погодити: у документі немає плану відкату.
> Додайте цей розділ і надішліть документ знову до п’ятниці».

Rubric:

- [ ] **P:** подяку, відмову, причину, наступний крок і термін `до п’ятниці` збережено
- [ ] **S:** повага лишається, церемонність не додано
- [ ] **S:** відповідь не стає агресивною чи знеособленою

## R5 — English setup-reversal removal in an announcement

Pairs with R2 (Russian) and R6 (Ukrainian). R1 tests the same rule on other text.

**Prompt:**

> Use blunt tone on this announcement without changing its information: "Ten integrations.
> Zero configuration. We rewrote the core. You won't notice. The update rolls out gradually
> and takes up to two weeks."

Rubric:

- [ ] **P:** `Ten integrations`, the absence of configuration, the rewritten core, the change
  being invisible to users, and `up to two weeks` remain
- [ ] **S:** both reversals are gone and each fact is stated once
- [ ] **S:** no slogan, triad, or contrast replaces the reversal
- [ ] **S:** the text stays an announcement and gains no sections or headings

## R6 — Ukrainian setup-reversal removal

Pairs with R2 (Russian) and R5 (English).

**Prompt:**

> Застосуй blunt tone до анонсу, не змінюючи інформації: «Десять інтеграцій. Нуль
> налаштувань. Ми переписали ядро. Ви цього не помітите. Оновлення розгортається поступово й
> триватиме до двох тижнів».

Rubric:

- [ ] **P:** `Десять інтеграцій`, відсутність налаштувань, переписане ядро, непомітність для
  користувача й термін `до двох тижнів` збережено
- [ ] **S:** обидва розвороти прибрано, кожен факт названо один раз
- [ ] **S:** замість розвороту не з’явилося гасла, тріади чи протиставлення
- [ ] **S:** текст лишається анонсом, розділів і заголовків не додано

## R7 — English reversal stating a real limit is retained

Pairs with R3 (Russian) and R8 (Ukrainian).

**Prompt:**

> Use blunt tone: "The migration is reversible. The index is not. The cache lowers read
> latency. Write speed does not change."

Rubric:

- [ ] **P:** migration reversibility, index irreversibility, lower read latency, and unchanged
  write speed remain
- [ ] **S:** both constructions stay, because the second part names a real limit
- [ ] **S:** the limits are not softened or turned into a general remark

## R8 — Ukrainian reversal stating a real limit is retained

Pairs with R3 (Russian) and R7 (English).

**Prompt:**

> Застосуй blunt tone: «Міграція оборотна. Індекс — ні. Кеш знижує затримку читання.
> Швидкість запису не змінюється».

Rubric:

- [ ] **P:** оборотність міграції, необоротність індексу, зниження затримки читання й
  незмінність запису збережено
- [ ] **S:** обидві конструкції збережено, бо друга частина називає реальну межу
- [ ] **S:** межі не пом’якшено й не перетворено на загальне зауваження

## D3 — English announced candor is removed

Pairs with D1 (Russian) and D4 (Ukrainian).

**Prompt:**

> Use blunt tone on this review comment: "I don't want to sound categorical, and I'll be
> honest rather than merely supportive: I think this approach may not hold up under load. It
> looks like the connection pool will run out at 10k RPS. It may be worth raising the limit to
> 500 before the release."

Rubric:

- [ ] **P:** `10k RPS`, pool exhaustion, the proposal to raise the limit to `500`, and the tie
  to the release remain
- [ ] **P:** `may not hold up` and `may be worth` stay a guess, not a fact
- [ ] **S:** the preambles about categorical tone and honesty are gone
- [ ] **S:** the comment stays collegial, not harsh

## D4 — Ukrainian announced candor is removed

Pairs with D1 (Russian) and D3 (English).

**Prompt:**

> Застосуй blunt tone до коментаря в рев’ю: «Не хочу здатися категоричним, і скажу чесно, а
> не просто підтримаю: мені здається, цей підхід може не витримати навантаження. Схоже, що за
> 10k RPS пул з’єднань вичерпається. Можливо, варто підняти ліміт до 500 перед релізом».

Rubric:

- [ ] **P:** `10k RPS`, вичерпання пулу, пропозицію підняти ліміт до `500` і прив’язку до
  релізу збережено
- [ ] **P:** «може не витримати» і «можливо» лишаються припущенням, а не фактом
- [ ] **S:** преамбули про категоричність і чесність прибрано
- [ ] **S:** коментар лишається колегіальним, а не різким

## E5 — English version of the grammatical-dash fragment

Pairs with E2 (Russian) and E6 (Ukrainian). English grammar requires no dash at these
positions, so every dash goes.

**Prompt:**

> Use blunt tone on this fragment without changing its information: "The cache — the buffer
> between the API and the database. Reads go through replicas, writes — through the primary.
> Warm-up takes 10–15 minutes. Logs, metrics, traces — everything goes to one sink."

Rubric:

- [ ] **P:** the cache's role, the read and write split, the `10` and `15` minute warm-up
  range, and the three telemetry kinds remain
- [ ] **S:** the range is written with one hyphen: `10-15 minutes`
- [ ] **S:** no em dash or en dash remains; each position becomes a period, a comma, or an
  ordinary clause such as `The cache is the buffer`
- [ ] **S:** no parenthetical replaces a removed dash

## E6 — Ukrainian grammatical dash becomes a double hyphen

Pairs with E2 (Russian) and E5 (English).

**Prompt:**

> Застосуй blunt tone до цього фрагмента, не змінюючи інформації: «Кеш — це буфер між API і
> базою. Читання йде через репліки, запис — через primary. Прогрів триває 10–15 хвилин.
> Логи, метрики, трейси — усе йде в один стік».

Rubric:

- [ ] **P:** роль кешу, поділ читання й запису, інтервал прогріву `10` і `15` хвилин і три
  види телеметрії збережено
- [ ] **S:** нульову зв’язку збережено як `Кеш -- це буфер`
- [ ] **S:** пропуск повторюваного слова збережено як `запис -- через primary`
- [ ] **S:** діапазон записано одним дефісом: `10-15 хвилин`
- [ ] **S:** узагальнення після переліку збережено як `--`
- [ ] **S:** жодну позицію не замінено на крапку, кому, дужки, довге чи коротке тире

## E7 — English decorative dash is removed

Pairs with E3 (Russian) and E8 (Ukrainian).

**Prompt:**

> Use blunt tone on this announcement without changing its information: "We rewrote the
> scheduler core — and you won't notice. Latency fell from 800 ms to 120 ms — with the same
> memory use."

Rubric:

- [ ] **P:** the core rewrite, no visible change for users, `800 ms`, `120 ms`, and the
  unchanged memory use remain
- [ ] **S:** both dashes are gone, because a period or a comma carries the same relation
- [ ] **S:** no dash is replaced by parentheses, an en dash, or a double hyphen
- [ ] **S:** the two-beat staging in the first sentence is removed under the setup-reversal
  rule, not only its dash

## E8 — Ukrainian decorative dash is removed

Pairs with E3 (Russian) and E7 (English).

**Prompt:**

> Застосуй blunt tone до цього анонсу, не змінюючи інформації: «Ми переписали ядро
> планувальника — і ви цього не помітите. Затримка впала з 800 мс до 120 мс — за того самого
> споживання пам’яті».

Rubric:

- [ ] **P:** факт переписування ядра, відсутність видимих змін для користувача, `800 мс`,
  `120 мс` і незмінне споживання пам’яті збережено
- [ ] **S:** обидва тире прибрано, бо крапка чи кома передають те саме відношення
- [ ] **S:** тире не замінено на дужки, коротке тире чи подвійний дефіс
- [ ] **S:** двотактну постановку з першого речення прибрано за правилом про setup-reversal,
  а не лише її тире

## W5 — English artifact display copy: staging and decoration

Pairs with W1 (Russian) and W6 (Ukrainian). The strings translate the observed Russian output
of W1; they are not observed output in English.

**Prompt:**

> Use blunt tone on the lines of an interactive OpenSpec tutorial. Do not change the facts and
> do not add new ones.
>
> Facts you may use: the spec sets the accepted behavior, and the implementation follows it; a
> delta from `changes/` merges into `specs/` on archive; the widget archives one change per
> click until no unaccepted deltas remain; the configuration has five independent settings;
> the step people skip after editing artifacts is syncing the delta into the main spec.
>
> Lines:
>
> 1. Page title: "The spec is the source of truth. The skill is its shadow."
> 2. Widget caption: "The archive machine — keep clicking until the delta runs dry."
> 3. Section heading "Configuration: five independent knobs" and the lead under it: "This is
>    not one choice. It is five, and they are not connected."
> 4. "You don't merge someone else's version of the skill. You read it."
> 5. "Artifacts are plain Markdown. Open, edit. Nothing else needed. People skip the step
>    after."

Rubric:

- [ ] **P:** the relation "the spec sets the behavior, the implementation follows it" remains
  (A1)
- [ ] **S:** the two-beat reversal in the title is gone and the "shadow" image is removed (A1)
- [ ] **P:** the widget's operation remains: one click archives one change, until no deltas
  remain (A3)
- [ ] **S:** the decorative verb "runs dry" is removed (A3)
- [ ] **S:** the lead does not repeat the heading's fact and the staged symmetry is gone; a
  remaining lead carries information the heading lacks (A4)
- [ ] **P:** both parts of the action remain: someone else's version is not merged, it is read
  (A5)
- [ ] **S:** the two-beat staging is gone and the relation is one ordinary sentence (A5)
- [ ] **S:** the teaser is gone: the skipped step is named directly in the same sentence (A7)
- [ ] **P:** nothing is added beyond the supplied facts

## W6 — Ukrainian artifact display copy: staging and decoration

Pairs with W1 (Russian) and W5 (English). The strings translate the observed Russian output
of W1; they are not observed output in Ukrainian.

**Prompt:**

> Застосуй blunt tone до рядків інтерактивного підручника з OpenSpec. Не змінюй фактів і не
> додавай нових.
>
> Факти, якими можна користуватися: специфікація задає прийняту поведінку, реалізація їй
> підпорядковується; дельта з `changes/` зливається в `specs/` під час архівування; віджет
> архівує по одному change за натискання, доки не лишиться неприйнятих дельт; конфігурація
> складається з п’яти незалежних параметрів; крок, який пропускають після редагування
> артефактів, — синхронізація дельти в основну специфікацію.
>
> Рядки:
>
> 1. Заголовок сторінки: «Специфікація — джерело правди. Скіл — її тінь».
> 2. Підпис до віджета: «Машина архіву — натискай, доки дельта не пересохне».
> 3. Заголовок розділу «Конфігурація: п’ять незалежних ручок» і лід під ним: «Це не один
>    вибір. Це п’ять, і вони не пов’язані між собою».
> 4. «Чужу версію скіла не мерджиш. Читаєш».
> 5. «Артефакти — звичайний Markdown. Відкриваєш, змінюєш. Більше нічого не треба.
>    Пропускають крок після».

Rubric:

- [ ] **P:** відношення «специфікація задає поведінку, реалізація їй підпорядковується»
  збережено (A1)
- [ ] **S:** двотактний переворот у заголовку знято, образ «тінь» прибрано (A1)
- [ ] **P:** спосіб роботи віджета збережено: одне натискання архівує один change, доки
  дельти не закінчаться (A3)
- [ ] **S:** декоративне дієслово «пересохне» прибрано (A3)
- [ ] **S:** лід не повторює факт із заголовка, постановочну симетрію знято; лід, що
  лишився, несе інформацію, якої немає в заголовку (A4)
- [ ] **P:** обидві частини дії збережено: чужу версію не мерджать, її читають (A5)
- [ ] **S:** двотактну постановку знято, відношення викладено одним звичайним реченням (A5)
- [ ] **S:** тизер знято: крок, який пропускають, названо прямо в тому самому реченні (A7)
- [ ] **P:** нічого не додано понад подані факти

## W7 — English artifact display copy: inflated wording

Pairs with W2 (Russian) and W8 (Ukrainian).

**Prompt:**

> Use blunt tone without changing the facts or adding new ones.
>
> Context: the `changes/` folder merges into `specs/` on archive; the tutorial author wrote the
> eight practice cases, and their origin is not documented; a dispute over a prose edit
> (SKILL.md against SKILL.md) has no correctness criterion, so the more insistent side wins,
> while a spec supplies such a criterion.
>
> Lines:
>
> 1. "All of OpenSpec's mechanics fit into two directories. Once you understand how one flows
>    into the other, the rest is syntax detail."
> 2. "Every difference lands in exactly one. Practice on eight real-world cases."
> 3. "With an author who defends their work, the difference is decisive."

Rubric:

- [ ] **P:** the claim about two directories remains (A2)
- [ ] **S:** "flows into" is replaced by the concrete operation: merge or archive (A2)
- [ ] **S:** "real-world" is removed or replaced by a checkable description of the cases'
  origin (A6)
- [ ] **S:** "decisive" is replaced by the concrete mechanism of the difference (A8)
- [ ] **P:** the mechanism comes from the supplied context and is not invented (A8)

## W8 — Ukrainian artifact display copy: inflated wording

Pairs with W2 (Russian) and W7 (English).

**Prompt:**

> Застосуй blunt tone, не змінюючи фактів і не додаючи нових.
>
> Контекст: тека `changes/` зливається в `specs/` під час архівування; вісім тренувальних
> випадків написав автор підручника, їхнє походження не задокументовано; у суперечці про
> правку прози (SKILL.md проти SKILL.md) немає критерію правильності, тому суперечку виграє
> наполегливіша сторона, а специфікація такий критерій дає.
>
> Рядки:
>
> 1. «Уся механіка OpenSpec вміщується у дві директорії. Якщо зрозуміти, як одна перетікає в
>    іншу, решта — деталі синтаксису».
> 2. «Кожна відмінність потрапляє рівно в одну. Потренуйся — вісім реальних випадків».
> 3. «З автором, який захищає свою роботу, різниця вирішальна».

Rubric:

- [ ] **P:** твердження про дві директорії збережено (A2)
- [ ] **S:** «перетікає» замінено на конкретну операцію: злиття або архівування (A2)
- [ ] **S:** ознаку «реальних» прибрано або замінено перевірним описом походження випадків
  (A6)
- [ ] **S:** «вирішальна» замінено конкретним механізмом відмінності (A8)
- [ ] **P:** механізм узято з поданого контексту, а не вигадано (A8)

## W9 — English display copy written into a generated file

Pairs with W3 (Russian) and W10 (Ukrainian).

**Prompt:**

> Blunt tone is on. Build an HTML fragment of a tutorial page and write it to a file at the
> given path. Do not show the file contents in the reply, only the path.
>
> The fragment has an `<h1>` with the page's thesis, a lead paragraph under it, and three
> `<h2>` elements for the sections.
>
> Facts: OpenSpec keeps plans in `changes/` and accepted behavior in `specs/`; on archive the
> delta merges into `specs/`; there are three sections: structure, configuration, archiving.

Rubric:

- [ ] **P:** the file keeps `changes/`, `specs/`, the merge on archive, and the three named
  sections
- [ ] **S:** the `<h1>` has no two-beat reversal, slogan, or decorative imagery
- [ ] **S:** the lead does not repeat the `<h1>` and does not announce the structure that the
  headings show right after it
- [ ] **S:** the headings name the sections instead of advertising them
- [ ] **P:** the file has no facts that the prompt lacks

## W10 — Ukrainian display copy written into a generated file

Pairs with W3 (Russian) and W9 (English).

**Prompt:**

> Blunt tone увімкнено. Збери HTML-фрагмент сторінки підручника й запиши його у файл за
> вказаним шляхом. У відповіді не показуй вмісту файлу, лише шлях.
>
> У фрагменті: `<h1>` з тезою сторінки, лід-абзац під ним, три `<h2>` для розділів.
>
> Факти: OpenSpec зберігає плани в `changes/`, прийняту поведінку — в `specs/`; під час
> архівування дельта зливається в `specs/`; розділів три: структура, конфігурація,
> архівування.

Rubric:

- [ ] **P:** у файлі збережено `changes/`, `specs/`, злиття під час архівування й три
  названі розділи
- [ ] **S:** в `<h1>` немає двотактного перевороту, гасла й декоративної образності
- [ ] **S:** лід не повторює `<h1>` і не анонсує структуру, яку одразу показують заголовки
- [ ] **S:** заголовки називають розділи, а не рекламують їх
- [ ] **P:** у файлі немає фактів, яких немає в промпті

## W11 — English competing directive for memorable copy

Pairs with W4 (Russian) and W12 (Ukrainian).

**Prompt:**

> Blunt tone is on. A page design guide is active at the same time: "the hero is a thesis, not
> a caption; text is design material; lines must be memorable."
>
> Write a hero line and a lead for a page about OpenSpec. Facts: plans live in `changes/` and
> accepted behavior in `specs/`; on archive the delta merges into `specs/`.

Rubric:

- [ ] **P:** both paths and the merge operation remain
- [ ] **P:** no product property absent from the prompt is added
- [ ] **S:** the hero has no two-beat reversal, slogan, or decorative metaphor
- [ ] **S:** the instruction "lines must be memorable" is not treated as a requested genre and
  does not justify keeping the named forms

## W12 — Ukrainian competing directive for memorable copy

Pairs with W4 (Russian) and W11 (English).

**Prompt:**

> Blunt tone увімкнено. Водночас діє посібник з оформлення сторінки: «hero — це теза, а не
> підпис; текст — матеріал дизайну; рядки мають запам’ятовуватися».
>
> Напиши hero-рядок і лід для сторінки про OpenSpec. Факти: плани лежать у `changes/`,
> прийнята поведінка — у `specs/`; під час архівування дельта зливається в `specs/`.

Rubric:

- [ ] **P:** обидва шляхи й операцію злиття збережено
- [ ] **P:** властивостей продукту, яких немає в промпті, не додано
- [ ] **S:** hero не містить двотактного перевороту, гасла й декоративної метафори
- [ ] **S:** вказівку «рядки мають запам’ятовуватися» не визнано запитаним жанром і не
  використано як підставу зберегти названі форми

## X14 — English artifact lines whose contrast carries content

Pairs with X7 (Russian) and X15 (Ukrainian). Control set for `W5`, `W7`, `W9`, and `W11`.

**Prompt:**

> Use blunt tone on these tutorial lines. If a line already fits the style, leave it
> unchanged.
>
> 1. "A spec is a behavior contract, not an implementation plan."
> 2. "You get less work, not more: the contract is shorter than the implementation."
> 3. "Two folders — and everything else is derived."
> 4. "Diffing your SKILL.md against someone else's is unresolvable: both sides are prose with
>    no correctness criterion. The more insistent side wins the dispute."

Rubric:

- [ ] **S:** the contrast in 1 stays, because it sets the boundary of the artifact's content
  (B1)
- [ ] **S:** 2 keeps both the rebuttal of the expected objection and its reason (B2)
- [ ] **S:** the derivation relation in 3 stays (B3)
- [ ] **S:** the second sentence in 4 stays as a consequence of the first and is not removed
  as a reversal (B4)
- [ ] **S:** the em dash in 3 becomes a comma or a period; lines 1, 2, and 4 keep their
  wording
- [ ] **P:** no line loses a fact, a condition, or a decision

## X15 — Ukrainian artifact lines whose contrast carries content

Pairs with X7 (Russian) and X14 (English). Control set for `W6`, `W8`, `W10`, and `W12`.

**Prompt:**

> Застосуй blunt tone до рядків підручника. Якщо рядок уже відповідає стилю, залиш його без
> змін.
>
> 1. «Специфікація — контракт поведінки, а не план реалізації».
> 2. «Роботи виходить менше, а не більше: контракт коротший за реалізацію».
> 3. «Дві теки, і все інше — похідне».
> 4. «Суперечку про диф свого SKILL.md із чужим не розв’язати: обидві сторони — проза без
>    критерію правильності. Її виграє той, хто наполегливіший».

Rubric:

- [ ] **S:** протиставлення в 1 збережено, бо воно задає межу змісту артефакту (B1)
- [ ] **S:** у 2 збережено і спростування очікуваного заперечення, і його причину (B2)
- [ ] **S:** відношення похідності в 3 збережено (B3)
- [ ] **S:** друге речення в 4 збережено як наслідок першого, а не видалено як розворот (B4)
- [ ] **S:** граматичні тире в 1, 3 і 4 записано як `--`, а не як довге тире
- [ ] **P:** жоден рядок не втратив факту, умови чи рішення

## X16 — English artifact lines keep their wording and convert the dash

Pairs with X8 (Russian) and X17 (Ukrainian).

**Prompt:**

> Use blunt tone on these tutorial lines. If a line already fits the style, leave it
> unchanged.
>
> 1. "The delta is 10 lines; SKILL.md is 400."
> 2. Table cell: "Cost of switching: high — you own it."
> 3. "Worktree orchestration solves a problem you don't have."
> 4. "Worth adding to CI right away: openspec validate --archived."

Rubric:

- [ ] **P:** the numbers `10` and `400` remain (B5)
- [ ] **S:** the dash in 2 becomes `--` or a comma and still introduces the reason, not drama
  (B6)
- [ ] **P:** the recommendation in 3 and its rationale remain (B7)
- [ ] **S:** the imperative in 4 and the command stay without ceremony or rewriting (B8)
- [ ] **S:** lines 1, 3, and 4 keep their wording, and no em dash or en dash remains
- [ ] **S:** no line is replaced by longer wording to "explain" it

## X17 — Ukrainian artifact lines keep their wording and convert the dash

Pairs with X8 (Russian) and X16 (English).

**Prompt:**

> Застосуй blunt tone до рядків підручника. Якщо рядок уже відповідає стилю, залиш його без
> змін.
>
> 1. «Дельта — 10 рядків, SKILL.md — 400».
> 2. Комірка таблиці: «Ціна зміни: висока — ти власник».
> 3. «Worktree-оркестрація — розв’язання проблеми, якої в тебе немає».
> 4. «Варто додати в CI одразу: openspec validate --archived».

Rubric:

- [ ] **P:** числа `10` і `400` збережено (B5)
- [ ] **S:** тире в 2 збережено як `--`, бо воно вводить причину, а не драматизацію (B6)
- [ ] **P:** рекомендацію в 3 та її обґрунтування збережено (B7)
- [ ] **S:** імператив у 4 і команду збережено без церемонії й без переписування (B8)
- [ ] **S:** кожне граматичне тире в 1, 2 і 3 записано як `--`, формулювання не змінено
- [ ] **S:** жоден рядок не замінено довшим формулюванням заради «пояснення»

## P2 — English unsupported ranking and frequency in a draft

Pairs with P1 (Russian) and P3 (Ukrainian).

**Prompt:**

> Use blunt tone on this draft.
>
> The complete sources it was written from:
>
> - Documentation: the `verify` command is part of the `expanded` profile.
> - Trainer: three error buckets; bucket 3 fires only when the rule is written in
>   `config.yaml`. The trainer collects no per-bucket statistics.
> - There are no review-time measurements.
> - The `expanded` profile includes `verify`, `archive --strict`, and `validate --archived`.
>
> Draft:
>
> 1. "Verify lives in expanded — that is the main argument for switching profiles."
> 2. "Errors are almost always in bucket 3 — it requires the rule to be written in
>    config.yaml."
> 3. "The skill cuts review time roughly in half."
> 4. "The expanded profile includes verify, archive --strict, and validate --archived."

Rubric:

- [ ] **P:** `verify` belonging to the `expanded` profile remains (C1)
- [ ] **S:** the "main argument" ranking is removed as unsupported by the sources (C1)
- [ ] **P:** the bucket 3 mechanism remains: it works only when the rule is written in
  `config.yaml` (C2)
- [ ] **S:** the frequency claim "almost always" is removed (C2)
- [ ] **S:** the numeric estimate in 3 is removed entirely, not softened to "significantly"
  (C3)
- [ ] **P:** line 4 remains with all three commands, because the source supports it

## P3 — Ukrainian unsupported ranking and frequency in a draft

Pairs with P1 (Russian) and P2 (English).

**Prompt:**

> Застосуй blunt tone до чернетки.
>
> Джерела, з яких її писали, повністю:
>
> - Документація: команда `verify` входить до профілю `expanded`.
> - Тренажер: три відра помилок; відро 3 спрацьовує лише тоді, коли правило записане в
>   `config.yaml`. Статистики за відрами тренажер не збирає.
> - Замірів часу рев’ю немає.
> - Профіль `expanded` містить `verify`, `archive --strict` і `validate --archived`.
>
> Чернетка:
>
> 1. «Verify живе в expanded — це головний аргумент за зміну профілю».
> 2. «Помилки майже завжди у відрі 3 — воно вимагає, щоб правило було записане в
>    config.yaml».
> 3. «Скіл скорочує час рев’ю приблизно вдвічі».
> 4. «Профіль expanded містить verify, archive --strict і validate --archived».

Rubric:

- [ ] **P:** належність `verify` до профілю `expanded` збережено (C1)
- [ ] **S:** ранжування «головний аргумент» знято як не підкріплене джерелом (C1)
- [ ] **P:** механізм відра 3 збережено: воно працює лише тоді, коли правило записане в
  `config.yaml` (C2)
- [ ] **S:** частотне твердження «майже завжди» знято (C2)
- [ ] **S:** числову оцінку в 3 знято повністю, а не пом’якшено до «значно» (C3)
- [ ] **P:** рядок 4 збережено з усіма трьома командами, бо джерело його підтверджує

## C3 — English named scope binds the artifact the agent will produce

Pairs with C2 (Russian) and C4 (Ukrainian).

**Prompt:**

> Apply blunt tone to the copy in the presentation we are about to make. Write the files
> yourself and show only the path in the reply.
>
> (next turn) Make the title slide and the architecture slide. Facts: the service accepts
> webhooks, puts them in a queue, and returns `202` right away; processing is asynchronous;
> one queue serves all event types.

Rubric:

- [ ] **S:** the agent does not ask which text to apply the style to and does not report that
  there is no text
- [ ] **P:** the file keeps webhook intake, the queue, the `202` code, asynchronous
  processing, and the single queue for all event types
- [ ] **S:** slide headings name the content, with no two-beat reversal, slogan, or
  decorative imagery
- [ ] **P:** the file has no facts that the prompt lacks
- [ ] **S:** the checks reach the text inside the file, not only the chat message
- [ ] **S:** the style holds on the second turn without another skill invocation

## C4 — Ukrainian named scope binds the artifact the agent will produce

Pairs with C2 (Russian) and C3 (English).

**Prompt:**

> Застосуй blunt tone до копірайтингової частини презентації, яку ми зараз зробимо. Файли
> пиши сам, у відповіді показуй лише шлях.
>
> (наступний хід) Зроби титульний слайд і слайд про архітектуру. Факти: сервіс приймає
> вебхуки, кладе їх у чергу й одразу віддає `202`; обробка асинхронна; черга одна на всі
> типи подій.

Rubric:

- [ ] **S:** агент не питає, до якого тексту застосовувати стиль, і не повідомляє, що тексту
  немає
- [ ] **P:** у файлі збережено приймання вебхуків, чергу, код `202`, асинхронність обробки й
  те, що черга одна на всі типи подій
- [ ] **S:** заголовки слайдів називають зміст, без двотактного перевороту, гасла й
  декоративної образності
- [ ] **P:** у файлі немає фактів, яких немає в промпті
- [ ] **S:** перевірки застосовано до тексту всередині файлу, а не лише до повідомлення в чаті
- [ ] **S:** стиль діє на другому ході без повторного виклику скіла
