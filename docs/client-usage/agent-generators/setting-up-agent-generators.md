# Setting Up Agent Generators

An **agent generator** produces agents (and their payloads) from an agent template. The
**Generators** interpreter (prompt `Consortium (Generators)`) is where you view agent
templates, create generators from them, manage running generators, and work with the
payloads they produce.

Switch into it from any connected interpreter with the `generators` command.

## Agent templates, generators, and payloads

Three concepts are involved:

- An **agent template** is a reusable definition describing a kind of agent and the
  options needed to configure one. Templates are loaded on the server from agent
  profiles. See the
  framework [Agents Overview](../../framework-api/agents/agents-overview.md).
- An **agent generator** is created from a template with a specific set of option
  values. Starting a generator produces payloads.
- A **payload** is the concrete artifact a generator produces, which can be downloaded
  and delivered to a target. Payloads are covered
  in [Managing Payloads](../resource-management/managing-payloads.md).

As with listeners, you do not author templates from the client: you create generators
*from* templates. Configuring a template and creating a generator happens in the "use
agent template" context, covered in [Using Agent Templates](using-agent-templates.md).

## The generators interpreter

On entry, the Generators interpreter lists all current agent generators and all
available agent templates. It subscribes to `AGENT_GENERATOR_CREATED` and
`AGENT_GENERATOR_REMOVED`
events so its listings and completions stay current. Payload completions are kept
current for every connected interpreter (see
[Managing Payloads](../resource-management/managing-payloads.md)).

Commands available here:

| Command                                               | Description                                                      |
|-------------------------------------------------------|------------------------------------------------------------------|
| `list`                                                | List all agent generators                                        |
| `template list`                                       | List all agent templates                                         |
| `template info <template_id>`                         | Show details of an agent template                                |
| `use <template_id>`                                   | Enter the template's context to configure and create a generator |
| `info <generator_id>`                                 | Show details of a generator                                      |
| `start <generator_id>`                                | Start a generator to produce payloads                            |
| `stop <generator_id>`                                 | Stop a running generator                                         |
| `cancel <generator_id>`                               | Cancel a generator                                               |
| `update <generator_id> <param> <value> [<value> ...]` | Update a non-running generator's parameters                      |
| `rename <generator_id> <name>`                        | Rename an existing generator                                     |
| `redescribe <generator_id> <description>`             | Change an existing generator's description                       |
| `delete <generator_id>`                               | Delete a non-running generator                                   |

`rename` and `redescribe` act on a generator that already exists, which is why both are
named for changing something already set. To choose the name and description a generator
is *born* with, use the `name` and `describe` commands inside the template's context
before running `create`. See
[Using Agent Templates](using-agent-templates.md#naming-the-generator).

Generator IDs, template IDs, and (for `update`) parameter names all tab complete. The
`payload` command used to work with the payloads a generator produces is available here
as it is in every connected interpreter, covered in
[Managing Payloads](../resource-management/managing-payloads.md).

## The typical workflow

1. Enter the Generators interpreter with `generators`.
2. Browse the available templates with `template list`, and inspect one with
   `template info <template_id>`.
3. Enter its context with `use <template_id>` to configure options and create a
   generator. See [Using Agent Templates](using-agent-templates.md).
4. Back in the Generators interpreter, confirm the generator and its payloads with
   `list`
   and `payload list`.
5. Download the produced payload with `payload download <payload_id>` and deliver it to
   a target. See
   [Managing Payloads](../resource-management/managing-payloads.md).

When a delivered payload runs and connects back through its compatible listener, the
agent checks in and appears in the [Agents interpreter](../agents/tasking-agents.md).

## Managing generators

Once a generator exists you control its lifecycle directly:

```text
start <generator_id>                               # start a non-running generator
stop <generator_id>                                # stop a running generator
update <generator_id> <param> <value> [<value> ...]  # update a non-running generator
cancel <generator_id>                              # forcefully cancel a running generator
delete <generator_id>                              # delete a non-running generator
```

Stop a generator before updating or deleting it. Parameter values use the same typing
rules as template options: annotate an individual value (for example `30:int`) or use
`-t/--value-type` for every value. Run `update --help-full` for detailed examples.
