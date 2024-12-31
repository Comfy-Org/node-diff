# node-diff

A Github Action for diffing custom nodes.

## Description

This action checks out your PR branch and your main branch and compares the custom nodes defined in `NODE_CLASS_MAPPINGS` for backwards incompatible changes.

This helps you develop custom nodes that don't break existing workflows.

## Features

- [x] Checks `RETURN_TYPES`
- [ ] Checks `INPUT_TYPES`

## Usage

Just add this to your custom node repo: `.github/workflows/validate.yml`

```
name: Validate backwards compatibility

on:
  pull_request:
    branches:
      - master
      - main

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: comfy-org/node-diff@main
```

If you use a branch other than `main` as your base branch, add that here:

```
steps:
  - uses: comfy-org/node-diff@main
  with:
    base_ref: 'master'
```
