# High Difficulty Findings (Deferred)

Derived from the `HANDOFF_5.md` audit. Everything here was categorised as **high**
difficulty: it requires behavioural code changes, cross-service design decisions, or a
correctness fix with real regression risk. None of it was implemented in the low/medium
remediation pass. Struck-through findings in `HANDOFF_5.md` were already resolved before
this pass and are not repeated here.

Findings are grouped by theme rather than by service, because the largest items span
several services and must be resolved once, consistently.

---

## H1. Lifecycle callbacks re-raise arbitrary user-component exceptions

**Services affected:** `plugins_service.py`, `listeners_service.py`,
`agent_generators_service.py`, `event_hooks_service.py`

**Source:** `consortium/framework/_core/components/component_life_cycle.py:115,136,161,183,222,228`

User-authored components implement `on_started`, `on_stopped` and `on_cancelled`. When
those callbacks raise, `component_life_cycle` re-raises the original exception unchanged.
The public service methods below therefore have **no closed exception contract**: any
exception type a component author writes can escape to the caller, and from there to the
REST API layer, where `log_and_propagate_error_on_service_method` classifies it as
`Unhandled exception` and logs it as CRITICAL with a full traceback (see
`server/utils.py`), paging operators for what is really third-party component code
misbehaving.

Affected public callables:

- `plugins_service.load_plugin_from_directory`, `unload_plugin_by_plugin_id`,
  `reload_plugin_by_plugin_id`, `start_plugin_by_plugin_id`, `stop_plugin_by_plugin_id`,
  `restart_plugin_by_plugin_id`, `cancel_plugin_by_plugin_id`
- `listeners_service.start_listener_by_listener_id` (re-raised at
  `component_life_cycle.py:136`), `stop_listener_by_listener_id` (:183),
  `cancel_listener_by_listener_id` (:228)
- `agent_generators_service.start_agent_generator_by_agent_generator_id` (:136),
  `stop_agent_generator_by_agent_generator_id` (:183),
  `cancel_agent_generator_by_agent_generator_id` (:228)
- `event_hooks_service.load_event_hook` and friends, via component setup/teardown

**Why deferred:** the fix is a design decision at the framework layer, not a docstring
change. The options are mutually exclusive and all of them change observable behaviour:

1. Wrap every callback exception in the existing `*StartError` / `*StopError` /
   `*SetupError` / `*TeardownError` families, chaining the cause. Gives a closed
   contract and correct log severity, but changes what every caller catches, including
   existing `except` clauses in the API layer and tests.
2. Introduce a single `ComponentCallbackError` at
   `_core/framework_exceptions/` and wrap there. Smaller surface, but a new exception
   type to map at the API boundary.
3. Leave the behaviour alone and document `Exception` in every `Raises:` section. Cheap,
   honest, but leaves the CRITICAL log misclassification in place.

Recommendation: option 1, since the typed exceptions already exist and are already
documented as the failure mode in several places. It should be done in one pass across
`component_life_cycle.py` plus the four services, with the API exception mappings
checked in the same change.

---

## H2. Template extension points re-raise arbitrary user code exceptions

**Services affected:** `payloads_service.py`, `agent_templates_payloads_service.py`,
`agent_generators_service.py`, `listeners_service.py`

**Source:** `consortium/framework/agents/base_agent_template.py:274,284-285`,
`consortium/framework/listeners/base_listener_template.py:310`

The same problem as H1, one layer up. Template option validating functions, option name
resolvers and generator constructors are user-supplied callables. Arbitrary exceptions
raised inside them escape:

- `payloads_service.create_payload_file`, `add_payload_file`,
  `create_payload_directory`, `add_payload_directory`,
  `update_payload_by_resource_id`
- `agent_templates_payloads_service.create_payload_file`, `create_payload_directory`,
  `add_payload_file`, `add_payload_directory`
- `agent_generators_service.create_agent_generator_from_agent_template_by_agent_template_id`,
  `update_agent_generator_by_agent_generator_id`
- `listeners_service.update_listener_by_listener_id`

Note that `AgentTemplateValidatingFunctionError` and
`ListenerTemplateValidatingFunctionError` already exist and already wrap *some* of these
paths. The gap is that they are not applied uniformly, so a caller cannot tell which
failures are typed and which are raw. Fixing it means auditing every extension point in
both template base classes.

**Why deferred:** same reason as H1, and the two should be resolved together so the
framework ends up with one rule rather than two.

---

## H3. `are_c2_types_compatible` cannot return `True` for the documented case

**Service:** `c2_types_service.py:243` (comparison at `:266`)

The return description promises `True` when a listener is compatible, but the
implementation compares a `BaseListenerType` **instance** against a collection that is
treated as listener **name strings** everywhere else in the codebase. The documented true
case is therefore unreachable under the normal representation.

This is a live correctness bug, not a documentation defect. It gates agent profile
loading (`agent_profiles_service.load_agent_profile` resolves agent types through this
service), so a wrong fix silently changes which profiles the server will accept at
startup.

**Why deferred:** requires deciding the canonical representation of a listener type in
the compatibility set (instance, name string, or class) and then making every producer
and consumer agree. Needs test coverage before and after; there is currently none
exercising the true branch, which is presumably why the bug survived.

---

## H4. `UserAccountsFileContainsDuplicateUsernamesError` is unreachable

**Service:** `user_accounts_service.py`,
`load_user_accounts_from_user_accounts_file` and
`read_user_accounts_from_user_accounts_file` (check at lines ~418-433)

`new_usernames` is never populated before the duplicate check runs, so the documented
duplicate-username protection never fires. A user accounts file containing the same
username twice loads silently, with last-write-wins semantics decided by dict insertion
order.

**Why deferred:** the fix is small but the semantics are not. It has to be decided
whether a duplicate means duplicate *within the file*, duplicate *against already loaded
accounts*, or both, and whether the failure is fatal to server start (the current
`load_framework_user_accounts` catches `UserAccountsServiceError` and continues) or
merely logged. Changing it can prevent a server that boots today from booting, which
warrants a deliberate decision and a test.

---

## H5. Generator content is silently discarded

**Service:** `agent_templates_payloads_service.py`
(`create_payload_file`, `create_payload_directory`, `add_payload_file`,
`add_payload_directory`)

**Source:** `consortium/server/objects/repository_objects.py:145-147` and `:444`

The public signatures accept a generator as `content`, and the parameter descriptions
describe it as payload content. The repository objects treat a generator as **empty
content**. A caller following the documented contract gets an empty file or an empty
directory, with no error.

**Why deferred:** two incompatible fixes. Either the repository objects learn to consume
generators (a real streaming-write change in `repository_objects.py`, affecting the
artifact and asset paths as well), or the signatures stop accepting generators and the
API models are narrowed to match, which is a breaking change to the payload creation
endpoints. Either way it reaches beyond the service being audited.

---

## H6. `trigger_event` cannot collect `BaseException`

**Service:** `events_service.py:141` (await at `:176`, `ExceptionGroup` raised at `:191`)

The prose states that all exceptions from event handlers are collected into an
`ExceptionGroup`. `asyncio.CancelledError` and every other `BaseException` subclass
bypass both `except` blocks, so a cancelled handler aborts the whole trigger and the
already-collected failures are lost.

The docstring half of this finding (the wrong module path for the signal exception, and
the undocumented `EventHookTriggerError` inside the group) was fixed in the medium pass.
What remains is the behavioural question.

**Why deferred:** deciding whether `trigger_event` should shield handlers from
cancellation is a concurrency design decision that touches
`run_async_background_task` and the 43 call sites it serves. Catching `BaseException`
naively would swallow shutdown cancellation and hang server teardown.

---

## H7. The agent type reference resolver calls a profile as a constructor

**Service:** `c2_types_service.py`, `_resolve_agent_type_references`

**Not from the original audit.** Found while documenting
`agent_profiles_service.load_agent_profile`, whose audit entry only mentioned a
"possible raw TypeError from the resolver". It is not merely possible, it is certain.

`agent_type_name_to_agent_profile_map` is built mapping agent type names to
**`AgentProfile` instances**. The resolution loop then does:

```python
agent_profile.agent_type = agent_type_name_to_agent_profile_map[agent_type]()
```

`AgentProfile` defines no `__call__`, so this raises
`TypeError: 'AgentProfile' object is not callable` every single time a profile
declares its `agent_type` as a string reference to another profile's agent type. The
inline comment above the line ("Agent types need to be instances of the class") shows
the intent: it should almost certainly take the matched profile's `agent_type` and
instantiate its class, not call the profile.

The whole string-reference feature is therefore non-functional. It escapes
`load_agent_profile`, `load_agent_profile_from_directory`,
`reload_agent_profile_by_agent_profile_id` and `load_framework_agent_profiles`, and
because a raw `TypeError` is not a domain error, `log_and_propagate_error_on_service_method`
logs it as CRITICAL with a full traceback.

**Why deferred:** it is a one-line fix but it needs the same representation decision as
[H3](#h3-are_c2_types_compatible-cannot-return-true-for-the-documented-case), which
lives in the same service: whether an agent type is carried as an instance, a class, or
a name. Fixing this line without settling that question risks trading one representation
bug for another. It also has no test coverage today, which is why a permanently broken
code path went unnoticed. Fix H3 and H7 together, with tests.

The medium remediation pass documented this `TypeError` in the four affected
`agent_profiles_service` docstrings so the contract is at least honest until it is fixed.

---

## Cross-cutting notes

- H1 and H2 are the same problem at two layers and should be scoped as one piece of
  work. Together they are the reason several public services still lack a closed
  exception contract, which was the headline finding of the original audit.
- H3, H4 and H5 are each a genuine defect rather than a documentation gap, and each one
  wants a regression test written before the fix.
- Nothing in this file has been changed in the codebase. The low and medium remediation
  commits deliberately left the surrounding docstrings accurate about current behaviour,
  so no docstring here now claims a contract that the code does not honour.
