# Vision

## The point

Most AI assistants forget you the moment the tab closes. Hermes is built the other way
round: it is a personal agent that accumulates. It writes skills from what it just did,
improves those skills while using them, curates its own memory, searches its past
conversations, and builds a model of the person it works for across sessions.

## Where it lives

An agent tied to one laptop is a tool. An agent reachable from Telegram while it works
on a cloud VM is a colleague. Hermes runs on a $5 VPS, a GPU cluster, or serverless
infrastructure that costs close to nothing while idle, and speaks to you over whichever
channel you already use — CLI, TUI, desktop app, or any of ~20 messaging platforms
through a single gateway process.

## What we refuse to do

- **Lock you to a model.** Any provider, any endpoint, switched with `hermes model`.
- **Grow the waist.** Every core model tool is paid for on every API call. Capability
  belongs in skills and plugins at the edges, where it costs nothing until used.
- **Break the cache.** Cheap long conversations are a product feature, not an
  optimisation. Design decisions that invalidate the cached prefix are rejected.

## Three-year horizon

Hermes should be the agent a person keeps for years — where the value is not the model
behind it but the accumulated skills, memory and habits layered on top, all of which
survive swapping that model out for whatever is best next month.

## How we measure it

Sessions per user over time rather than sessions per week; skills created and still in
use after a month; the share of capability shipped as plugins and skills instead of core
tools; and the cost of a long conversation staying flat as it lengthens.
