from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional

SUITS = ["S", "H", "D", "C"]
VALUE_LABELS = {1: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10"}
LABEL_VALUES = {label: value for value, label in VALUE_LABELS.items()}


@dataclass(frozen=True)
class Card:
    value: int
    suit: str

    @property
    def label(self) -> str:
        return f"{VALUE_LABELS[self.value]}{self.suit}"


@dataclass
class Build:
    cards: List[Card]
    total: int


@dataclass
class Player:
    name: str
    hand: List[Card]
    captured: List[Card]


@dataclass
class Action:
    kind: str
    hand_index: Optional[int] = None
    table_index: Optional[int] = None
    build_index: Optional[int] = None
    target_total: Optional[int] = None
    steal_from: Optional[int] = None


class Game:
    def __init__(self, player_count: int, rng: Optional[random.Random] = None) -> None:
        if player_count not in (2, 3):
            raise ValueError("Only 2 or 3 players are supported.")
        self.player_count = player_count
        self.rng = rng or random.Random()
        self.players = [Player(name=f"P{i + 1}", hand=[], captured=[]) for i in range(player_count)]
        self.table: List[Card] = []
        self.builds: List[Build] = []
        self.stock: List[Card] = []
        self.last_capturer: Optional[int] = None
        self.active_player = 0
        self._setup()

    def _setup(self) -> None:
        deck = [Card(value=value, suit=suit) for suit in SUITS for value in range(1, 11)]
        self.rng.shuffle(deck)
        if self.player_count == 2:
            for player in self.players:
                player.hand.extend(deck[:10])
                del deck[:10]
            self.stock = deck
        else:
            for player in self.players:
                player.hand.extend(deck[:13])
                del deck[:13]
            starter = deck.pop()
            self.table.append(starter)
            self._resolve_three_of_hearts_exchange()
            self.stock = []

    def _resolve_three_of_hearts_exchange(self) -> None:
        if not self.table:
            return
        starter = self.table[0]
        for player in self.players:
            for card in player.hand:
                if card.value == 3 and card.suit == "H":
                    player.hand.remove(card)
                    player.hand.append(starter)
                    self.table[0] = card
                    return

    def _deal_second_round(self) -> None:
        if self.player_count != 2 or not self.stock:
            return
        if any(player.hand for player in self.players):
            return
        for player in self.players:
            player.hand.extend(self.stock[:10])
            del self.stock[:10]

    def current_player(self) -> Player:
        return self.players[self.active_player]

    def advance_turn(self) -> None:
        self.active_player = (self.active_player + 1) % self.player_count
        self._deal_second_round()

    def legal_moves(self, player_index: int) -> List[Action]:
        player = self.players[player_index]
        actions: List[Action] = []
        for idx, card in enumerate(player.hand):
            actions.append(Action(kind="throw", hand_index=idx))
            for table_idx, table_card in enumerate(self.table):
                if card.value == table_card.value:
                    actions.append(Action(kind="capture", hand_index=idx, table_index=table_idx))
            for build_idx, build in enumerate(self.builds):
                if card.value == build.total:
                    actions.append(Action(kind="capture_build", hand_index=idx, build_index=build_idx))
            for table_idx, table_card in enumerate(self.table):
                target_total = card.value + table_card.value
                if any(hand_card.value == target_total for hand_card in player.hand if hand_card != card):
                    actions.append(
                        Action(kind="build", hand_index=idx, table_index=table_idx, target_total=target_total)
                    )

        for opponent_index, opponent in enumerate(self.players):
            if opponent_index == player_index or not opponent.captured:
                continue
            top_card = opponent.captured[-1]
            for table_idx, table_card in enumerate(self.table):
                target_total = top_card.value + table_card.value
                if any(hand_card.value == target_total for hand_card in player.hand):
                    actions.append(
                        Action(
                            kind="steal_build",
                            table_index=table_idx,
                            target_total=target_total,
                            steal_from=opponent_index,
                        )
                    )
        return actions

    def apply_action(self, player_index: int, action: Action) -> None:
        player = self.players[player_index]
        if action.kind == "throw":
            card = player.hand.pop(action.hand_index)
            self.table.append(card)
            return
        if action.kind == "capture":
            card = player.hand.pop(action.hand_index)
            table_card = self.table.pop(action.table_index)
            player.captured.extend([card, table_card])
            self.last_capturer = player_index
            return
        if action.kind == "capture_build":
            card = player.hand.pop(action.hand_index)
            build = self.builds.pop(action.build_index)
            player.captured.append(card)
            player.captured.extend(build.cards)
            self.last_capturer = player_index
            return
        if action.kind == "build":
            card = player.hand.pop(action.hand_index)
            table_card = self.table.pop(action.table_index)
            build_cards = [card, table_card]
            self.builds.append(Build(cards=build_cards, total=action.target_total))
            return
        if action.kind == "steal_build":
            opponent = self.players[action.steal_from]
            stolen = opponent.captured.pop()
            table_card = self.table.pop(action.table_index)
            build_cards = [stolen, table_card]
            self.builds.append(Build(cards=build_cards, total=action.target_total))
            return
        raise ValueError(f"Unknown action: {action.kind}")

    def collect_remaining_table(self) -> None:
        if self.last_capturer is None:
            return
        player = self.players[self.last_capturer]
        player.captured.extend(self.table)
        self.table.clear()
        for build in self.builds:
            player.captured.extend(build.cards)
        self.builds.clear()

    def is_over(self) -> bool:
        return all(not player.hand for player in self.players) and not self.stock

    def score(self) -> List[int]:
        scores = []
        for player in self.players:
            pile = player.captured
            aces = sum(1 for card in pile if card.value == 1)
            two_spades = sum(1 for card in pile if card.value == 2 and card.suit == "S")
            ten_diamonds = sum(1 for card in pile if card.value == 10 and card.suit == "D")
            spades = sum(1 for card in pile if card.suit == "S")
            spade_points = 2 if spades >= 6 else 1 if spades == 5 else 0
            total_cards_bonus = 1 if len(pile) >= 21 else 0
            score = aces + two_spades + ten_diamonds + spade_points + total_cards_bonus
            scores.append(score)
        return scores

    def table_state(self) -> str:
        loose = " ".join(card.label for card in self.table) or "(none)"
        builds = ", ".join(
            f"{build.total}:" + "+".join(card.label for card in build.cards) for build in self.builds
        )
        builds = builds or "(none)"
        return f"Loose: {loose} | Builds: {builds}"


class ConsoleUI:
    def __init__(self, game: Game) -> None:
        self.game = game

    def run(self) -> None:
        while not self.game.is_over():
            player = self.game.current_player()
            print("\n" + "=" * 60)
            print(f"Table: {self.game.table_state()}")
            print(f"{player.name} hand: {self._hand_display(player.hand)}")
            moves = self.game.legal_moves(self.game.active_player)
            if not moves:
                print("No legal moves available. Passing.")
                self.game.advance_turn()
                continue
            action = self._prompt_for_action(moves)
            self.game.apply_action(self.game.active_player, action)
            self.game.advance_turn()

        self.game.collect_remaining_table()
        scores = self.game.score()
        print("\nGame over.")
        for player, score in zip(self.game.players, scores):
            print(f"{player.name} captured {len(player.captured)} cards, score: {score}")

    def _hand_display(self, hand: List[Card]) -> str:
        return " ".join(f"[{idx}] {card.label}" for idx, card in enumerate(hand))

    def _prompt_for_action(self, moves: List[Action]) -> Action:
        print("Available moves:")
        for idx, action in enumerate(moves):
            print(f"  {idx}: {self._describe_action(action)}")
        while True:
            raw = input("Choose move #: ").strip()
            if raw.isdigit() and 0 <= int(raw) < len(moves):
                return moves[int(raw)]
            print("Invalid selection.")

    def _describe_action(self, action: Action) -> str:
        if action.kind == "throw":
            return f"Throw card #{action.hand_index}"
        if action.kind == "capture":
            return f"Capture table card #{action.table_index} with hand #{action.hand_index}"
        if action.kind == "capture_build":
            return f"Capture build #{action.build_index} with hand #{action.hand_index}"
        if action.kind == "build":
            return (
                f"Build with hand #{action.hand_index} + table #{action.table_index}"
                f" to total {action.target_total}"
            )
        if action.kind == "steal_build":
            return (
                f"Steal top from player {action.steal_from + 1} + table #{action.table_index}"
                f" to total {action.target_total}"
            )
        return action.kind


def simulate_game(game: Game) -> None:
    while not game.is_over():
        moves = game.legal_moves(game.active_player)
        if not moves:
            game.advance_turn()
            continue
        action = game.rng.choice(moves)
        game.apply_action(game.active_player, action)
        game.advance_turn()
    game.collect_remaining_table()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play the 40-card numbers game.")
    parser.add_argument("--players", type=int, default=2, choices=[2, 3])
    parser.add_argument("--interactive", action="store_true", help="Play interactively in the terminal.")
    parser.add_argument("--simulate", action="store_true", help="Simulate a full game with random moves.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = Game(player_count=args.players)
    if args.interactive:
        ConsoleUI(game).run()
    else:
        simulate_game(game)
        scores = game.score()
        print("Simulation complete.")
        for player, score in zip(game.players, scores):
            print(f"{player.name} score: {score}")


if __name__ == "__main__":
    main()
