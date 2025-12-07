# Clear the dungeon

Based on this video by Riffle Shuffle & Roll -> https://youtu.be/GbEkAfCqfTM?si=yvGkOyPQFhplO2d_

python text based game.

## How to run the game

### create venv and install dependencies with uv

requires : `python3.13+`

`uv sync`

`source .venv/bin/activate`

### run the game

`python main.py`

## How to play

### commands

```
h - help, lists commands
q - quit
d - discard current hand
```

```
input is <# player hand card> <# dungeon hand card>
eg: 1 2
```

Notes:

- player hand card should be a valid number between 1-3, as existing on the player hand
- dungeon hand card should be a valid number between 1-4
