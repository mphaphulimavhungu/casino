# 40-Card Numbers Game (Draft Rules)

This document turns the provided rules into a complete, playable ruleset and adds online/multiplayer guidance.

## Deck

* 40-card deck, numbers only: Ace through 10 in each suit.
* Each card is unique (no repeats).
* Suits matter only for scoring (spades, 2♠, 10♦, and aces).

## Players

* 2 or 3 players.

## Objective

Score the most points by capturing cards, collecting scoring cards, and meeting suit/hand bonuses.

## Setup

### Two Players

1. Shuffle the 40-card deck.
2. Deal 10 cards to each player (private hand).
3. Set the remaining 20 cards as the **stock**.

**Second Round Deal:** When both players run out of cards, deal the remaining 10 cards to each player (so each player receives 20 total across the game). Continue play until all cards are played.

### Three Players

1. Shuffle the 40-card deck.
2. Deal 13 cards to each player (private hand). This uses 39 cards.
3. Reveal the final 1 card face-up on the table (the **starter card**).
4. If any player holds the **3 of hearts** ("3 of love"), they may immediately exchange it for the starter card, then place the 3 of hearts face-up as the new starter card. This exchange happens once.

## Turn Order

* Choose a starting player at random.
* Turns proceed clockwise.

## Table and Captures

### Table Layout

* The table contains loose cards and **builds** (see below).
* A build is a group of exactly two cards whose values sum to a target number.

### Values

* Ace = 1, number cards equal their number (2–10).

### Capturing ("Eating")

On your turn, play **one** card from your hand. You may:

1. **Capture a single card:** If your played card matches a single table card by value, you may capture that card.
2. **Capture a build:** If your played card matches the total value of a build (two cards that sum to the same value), you may capture the entire build.
3. **Create a build:** If there is a single table card that can be combined with a card from your hand to sum to a value in your hand, you may place those two cards together as a build.

**Build rule:** Builds are always exactly two cards. A player may build using a table card and a card from their hand. You may also build using a card from another player’s captured pile **only if** that top card is visible and the build uses exactly two cards total. (See “Stealing from Captured Piles” below.)

### Throw (No Capture)

If you cannot or do not wish to capture or build, you may place one card from your hand face-up on the table as a loose card.

## Stealing from Captured Piles (Important Rule)

If a player captures a card and places it on top of their captured pile (their **stack**), another player may take the **top card only** if it can be used immediately to create a valid two-card build on the table.

* The steal must be done **during the stealing player’s turn**.
* The stolen card must be used immediately to form a legal build.
* Only the **top card** of a captured pile is eligible.
* The original captured pile remains with the original owner (minus the top card).

## End of Round

The round ends when all players have played all cards and the stock (if any) is empty.

* Any loose cards or builds left on the table are awarded to the **last player to capture** a card.

## Scoring

Score at the end of the round:

* **Aces**: 1 point each (up to 4 points).
* **2 of spades (2♠)**: 1 point.
* **10 of diamonds (10♦)**: 1 point.
* **Spade majority**:
  * 5 spades = 1 point.
  * 6 or more spades = 2 points.
* **21 cards collected**: 1 point.

## Additional Rules to Make Play Clear

* **Single action per turn:** You may play only one card from your hand each turn.
* **Build priority:** A build can only be captured by a card matching its total value.
* **No rebuilding a build:** Builds are fixed once placed (two cards only).
* **Misplay correction:** If an illegal capture/build is made, rewind the turn if caught immediately; otherwise the state stands.

## Online / Multiplayer Play (Across Different Locations)

To make the game playable online (e.g., different Wi‑Fi/data networks), use a **server-authoritative** model:

1. **Authoritative server**
   * The server shuffles, deals, and validates every move.
   * Clients only send intended actions; the server accepts or rejects them.

2. **Turn-based actions**
   * Only the active player may submit an action.
   * Allowed actions: `capture`, `build`, `throw`, `steal-build`.

3. **State synchronization**
   * After every move, the server sends updated state:
     * current table cards and builds
     * each player’s hand size (not contents)
     * each player’s captured pile size
     * current scores (optional, or calculated at end)

4. **Anti‑cheat**
   * The server stores each player’s hand privately.
   * Random shuffle must use a server-generated seed.
   * Clients never see other players’ hands.

5. **Reconnection rules**
   * If a player disconnects, their hand is preserved on the server.
   * They have 2–3 minutes to reconnect before a forfeit or AI substitution.

6. **Timer (optional)**
   * 30–60 seconds per turn; timeouts automatically `throw` the lowest-value card.

### Example Action Messages (JSON)

```json
{
  "type": "build",
  "playerId": "p2",
  "handCard": "4H",
  "tableCard": "6C",
  "buildValue": 10
}
```

```json
{
  "type": "capture",
  "playerId": "p1",
  "handCard": "10S",
  "target": { "build": ["6D", "4C"] }
}
```

## Python Reference Implementation

A simple terminal-based Python implementation is included for local play or simulation.

```bash
python casino_game.py --players 2 --interactive
```

```bash
python casino_game.py --players 3 --simulate
```

## Glossary

* **Table:** The shared area with loose cards and builds.
* **Build:** Two cards placed together to create a target value.
* **Capture/Eat:** Taking cards from the table (or a build) into your captured pile.
* **Stack:** Your captured pile.
