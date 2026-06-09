---
name: uipath-ixp-runtime
description: "UiPath IXP runtime — consume published IXP (Document Understanding) models to extract data from documents at runtime. For creating projects, improving prompts, and publishing models→uipath-ixp-designtime."
---

# UiPath IXP Runtime

Skill for **consuming published UiPath IXP models** — running a model that was published with the designtime workflow against new documents to extract structured data.

> This skill is **in development**. The runtime consumption workflow and CLI surface are not yet documented here. To create a project, review/confirm predictions, improve prompts, and publish a model, use the [uipath-ixp-designtime](../uipath-ixp-designtime/SKILL.md) skill.

## When to Use This Skill

- User wants to **run** a published IXP model against documents (extract fields from new files using an existing published model).
- User asks how to consume / invoke an IXP Document Understanding model that has already been published.
- User asks which published IXP models are available to extract with at runtime.

For creating projects, labelling, improving prompts, or **publishing** models, use **uipath-ixp-designtime** instead.

## Critical Rules

1. **This skill covers runtime consumption only** — not authoring. Creating projects, improving prompts, and publishing models is the designtime skill's job (→ uipath-ixp-designtime).
2. **A model must be published before it can be consumed.** If no published model exists, route the user to uipath-ixp-designtime to create and publish one first.
3. **ONLY use documented `uip` CLI commands** — do NOT call REST APIs directly, grep/read source, or explore the codebase.

## Status

Skeleton / in-development. The runtime extraction workflow (CLI commands, inputs/outputs, examples) is still to be authored.
