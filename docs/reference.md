# Reference

Auto-generated from the source docstrings, grouped to mirror the
[R package's reference index](https://strategicprojects.github.io/evolution/reference/).

## Client

Create and configure the API client.

::: evolution_api.EvoClient
    options:
      members: false

::: evolution_api.AsyncEvoClient
    options:
      members: false

## Send messages

Functions to send different types of WhatsApp messages. All are methods on
`EvoClient` / `AsyncEvoClient`.

::: evolution_api.messages.MessagesMixin
    options:
      show_root_heading: false
      heading_level: 3
      members_order: source

## Chat utilities

Query and verify WhatsApp numbers, and build JIDs.

::: evolution_api.numbers.NumbersMixin
    options:
      show_root_heading: false
      heading_level: 3

::: evolution_api.instance.InstanceMixin
    options:
      show_root_heading: false
      heading_level: 3

::: evolution_api.jid

## Receiving (webhooks)

::: evolution_api.webhooks.parse_webhook

::: evolution_api.webhooks.fastapi.webhook_router

::: evolution_api.webhooks.dataframe.as_dataframe

### Event models

::: evolution_api.webhooks.models
    options:
      show_root_heading: false
      heading_level: 4
      members_order: source

## Errors

::: evolution_api.EvolutionError
::: evolution_api.EvolutionConfigError
::: evolution_api.EvolutionConnectionError
::: evolution_api.EvolutionAPIError
