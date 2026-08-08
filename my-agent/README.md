# my-agent

A Managed Deep Agent built with [`managed-deepagents`](https://github.com/langchain-ai/managed-deepagents-sdk).

## Project structure

```text
my-agent/
  agent.py         # define_deep_agent(...) — required `name` is the deploy id
  instructions.md  # always-loaded system prompt
  pyproject.toml   # project dependencies
  .env             # API keys (LangSmith + model providers); never commit
  identity.py      # managed authentication and private per-user state
  memory.py        # durable memory (`none` scope)
  tools/           # optional custom tools
  middleware/      # optional middleware
  skills/          # optional skills synced to Context Hub
  connectors/      # optional MCP server declaration
```

## Install

```bash
uv sync
```

## Evaluate

Managed Deep Agent evals are Harbor evals. Author full Harbor tasks directly under
`evals/tasks/<task>/`. To start from a minimal task, run:

```bash
mda evals init my-task
```

This creates the optional scaffold `evals/scaffold/my-task/` with an `instruction.md` and a language
verifier. Run the same command with another name to add more scaffolds. At compile
time MDA copies selected scaffolds to `evals/tasks/` and preserves
every other task. Compile the managed agent, then run Harbor yourself:

```bash
mda evals compile ./my-agent                  # all tasks
mda evals compile ./my-agent --task my-task   # only my-task
# follow the printed `harbor run` command
```

## Develop

Edit `agent.py` to configure your model, tools, and middleware, and edit
`instructions.md` to shape the system prompt.

Run the compiled app on the local LangGraph dev server:

```bash
mda dev .
```

For Python projects, `mda dev` requires `uv` on `PATH`, but it resolves the local LangGraph dev server automatically; you do not need to install a global `langgraph` command.

## Identity

`identity.py` enables managed authentication: threads and downstream
credentials are per-caller. Set `auth` to one or more `auth.*` entries if
browsers call the deployment directly. Durable memory is declared
separately.

## Memory

`memory.py` declares `none`, so this agent keeps no durable memory.
Change the scope to `"agent"` to mount `/memories/agent/`.

## Sandbox

This project has no sandbox: MDA only provisions one when a declaration
is present. Add `sandbox/__init__.py` to give the agent a managed execution
environment with a filesystem and a shell.

## Optional Runtime Pieces

Add `connectors/mcp.py` to attach MCP servers. The file must export a named
`connector` declaration.

## Deploy

Compile and deploy the project to LangSmith:

```bash
mda deploy .
```

This copies your files verbatim, generates a managed entry module, and writes a
deployable build (including `langgraph.json`) to `.mda/build`. The CLI uploads
that build to LangSmith to run your agent on the managed runtime.

Common options:

```bash
mda deploy . --name my-agent-dev --deployment-type dev
mda deploy . --workspace-id "$LANGSMITH_WORKSPACE_ID"
mda deploy . --no-wait
```

Deploy prints both the Agent Server URL to call and the LangSmith dashboard URL
to inspect.

## Logs

Read the deployed agent's server logs:

```bash
mda logs .
mda logs . --lines 200 --level error
```

In a terminal this streams new output until you press Ctrl-C. When the output is
piped or redirected it prints the most recent lines (1000 by default) and exits.

## Delete

Remove the deployment and the LangSmith resources it created:

```bash
mda delete .
```

This deletes the deployment, the tracing project created alongside it, the
Context Hub repo holding this agent's context and memory, and the managed
sandboxes this agent created. It asks first; pass `--yes` to skip the prompt.
Agent memory and thread history are not recoverable afterwards.

## Environment

`mda deploy` loads `.env`, uses `LANGSMITH_API_KEY` for LangSmith, and forwards
model provider keys such as `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` as deployment
secrets. Set `LANGSMITH_WORKSPACE_ID` or pass `--workspace-id` if your LangSmith
API key requires a workspace selection.
