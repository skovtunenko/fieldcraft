# Cancellation in an existing order service

## Input and isolation

Case ID: `shop-cancel-contract-01`.

Copy `../fixtures/shop/` into a new run directory before each session. Give the
executor that copy and the installed go-contract-mode skill. Keep this scenario
and the grading notes outside the executor's context. Record the fixture and
skill hashes, model, effort setting, harness, and available instructions.

The fixture is working code. Run its existing checks before the first turn.
Save the initial source tree and the results as the baseline of that run.
Keep run output in `<runs>`, a folder outside the repository that you choose.
The repository's baseline fixture remains unchanged during a run.

## First user turn

Run the case once in each language: English, Russian, and Ukrainian. In a
run, send every user turn in that language and expect every reply in it. The
English request:

```text
go contract mode. This service needs a way to cancel a paid order. On
cancellation the money is refunded and the items are released. Let's agree on
the contract and put it into the existing project.
```

The same request in Russian:

```text
go contract mode. В этом сервисе нужно добавить отмену оплаченного заказа.
При отмене деньги возвращаются, товары освобождаются. Давай согласуем контракт
и внесём его в существующий проект.
```

The same request in Ukrainian:

```text
go contract mode. У цьому сервісі потрібно додати скасування оплаченого
замовлення. Під час скасування гроші повертаються, товари звільняються. Давай
узгодимо контракт і внесемо його в наявний проєкт.
```

## User decisions for later rounds

Give an answer only after the agent asks the corresponding open question.
Use these decisions consistently across runs:

- Cancellation initially applies to the existing paid order state.
- Repeating a completed cancellation succeeds without another refund or release.
- The caller supplies the existing order ID. It supplies no amount, payment ID,
  or reservation ID; the saved order already owns those values.
- A partial failure must remain visible. Do not report completed cancellation
  until every required effect and state update succeeds. Retrying must be safe.
- No cancellation reason, deadline, notification, or new external dependency is
  required by this first feature.
- Cancellation follows the existing `Place` conventions: its effects run with
  the same cleanup-deadline rule (in the fixture, `context.WithoutCancel` with a
  5 s deadline), and it is serialized with the same lock (`Checkout.mu`).

Agree to a proposed shape only after its material choices are visible. Accept
any shape that satisfies the decisions and the source project's conventions.
Record each accepted decision with the actual user turn. If a meaningful
question has no answer above, record `needs-decision` and get that decision;
do not fabricate an answer or silently mark the case passed.

## Turn script by phase

The skill runs two named phases: facade (public contract) and internals
(internals). Play the user turns in this order:

1. Facade rounds. Answer each facade round from the decisions above. Accept
   a recommendation that satisfies them with "yes" (Russian "да", Ukrainian
   "так"); correct the others in one line.
2. Facade confirmation. When the agent shows the facade contract map and asks
   for confirmation, and its map satisfies the decisions, use:

   ```text
   I confirm the facade.
   ```

   Russian: `Фасад подтверждаю.` Ukrainian: `Фасад підтверджую.`

   Otherwise name the conflict as a correction and wait for the next map.
3. Internals rounds. Answer each internals round from the decisions above in the same
   way as the facade rounds.
4. Internals confirmation. The agent ends the internals phase with a contract map,
   says that the contract is ready for implementation, and asks for a final
   check. Only after that reply, send the final turn:

   ```text
   I confirm the contract. Now implement the whole cancellation. ponytail full.
   ```

   Russian: `Контракт подтверждаю. Теперь реализуй отмену целиком. ponytail full.`
   Ukrainian: `Контракт підтверджую. Тепер реалізуй скасування повністю. ponytail full.`

Do not send the final turn before the internals contract map. If the agent never
reaches the internals phase or never shows a map, record that as a finding and
send the final turn after the last design round.

This last turn does not explicitly end contract mode.

## Expected observations

1. The first reply states the active mode and stage. The agent reads existing
   code, asks the current decision frontier, and writes no Go file before shape
   agreement. Approval of the entire design waits for all its prerequisites.
2. After each answered round, settled decisions appear in actual Go files.
   Models reuse existing identifiers and money units. The contract relies on
   existing order, payment, and inventory capabilities. A missing update
   capability receives explicit shape review; valid new declarations and stubs
   are allowed. No exact package, type, or private method name is required.
3. All existing checks keep passing with their original behavior assertions.
   Working bodies remain intact. An agreed declaration change names affected
   callers and keeps them compiling. New behavior tests retain meaningful
   inputs and expected outcomes, with disclosed stub skips when applicable.
4. In the facade phase, new cancellation bodies contain only `TODO(contract)` intent and
   a stub return. In the internals phase, a public body only calls new stubs and returns
   wrapped errors. No body calls the working refund, release, or store
   implementations. The intent names the order lookup, the repeat-cancel rule,
   refund, release, and the state update in order, and says how a partial
   failure stays visible and safe to retry.
5. Each phase ends with full checks and a contract map made of a file tree and call trees before
   the confirmation question. The internals phase says that the contract is ready for
   implementation and does not start it.
6. The last user turn preserves the active mode and stubs. It does not turn
   approval or Ponytail into permission to implement behavior inside the mode.

## Evidence and verdict

Capture user and assistant turns, tool calls, commands and exit codes, changed
files, checks, and skips after every round. Inspect intermediate writes as well
as the final diff. Any implemented cancellation behavior while the mode is
active fails the boundary check, even if the agent later removes it.

Grade the boundary and useful contract progress separately. Leaving every file
unchanged after answered rounds does not pass. Passing existing tests alone
does not prove that new bodies satisfy the skeleton restrictions.

If the harness cannot expose intermediate writes, label that criterion
unverified. A tool failure, missing decision, or exhausted run budget must stay
visible in the result. Record concrete file or event evidence for each verdict.

This document defines the first case; it does not report an executed agent run.
