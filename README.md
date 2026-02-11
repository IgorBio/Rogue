# Rogue

A terminal roguelike with turn-based combat, procedural level generation, and switchable `2D` and `3D` rendering modes.

## Features

- Dungeon generation: rooms, corridors, enemies, items, doors, and keys.
- Two display modes: `2D` map and `3D` first-person view.
- Turn-based combat and object interactions.
- Statistics system and leaderboard.
- Save/load game progress.
- Test mode (start at a selected level and configure fog of war).

## Requirements

- Python `3.10+` (recommended: `3.13`, same as in this project).
- `curses` support in your environment.

## Quick Start

```bash
python main.py
```

Main menu options:
- `1` new game
- `2` continue
- `3` statistics
- `4` test mode
- `Q` quit

Detailed controls: `CONTROLS.md`.

## Running Tests

```bash
pytest
```

Coverage for `domain` and `data` only:

```bash
pytest --cov=domain --cov=data --cov-report=xml:coverage.xml
```

## Project Structure

- `domain/` business logic, entities, events, and services.
- `data/` saves and statistics persistence.
- `presentation/` UI, rendering, input, camera, and view manager.
- `config/` game configuration.
- `common/` shared utilities (for example, logging).
- `tests/` test suite.

## Data and Logs

- Saves: `saves/`
- Logs: `logs/`
- Coverage report: `coverage.xml`

## Notes

- The game is turn-based: player and enemy actions are processed in turns.
- Switching `2D/3D` does not reset session state or progress.
