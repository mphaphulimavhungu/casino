"""Simple Streamlit UI for the Casino game.

Usage: streamlit run streamlit_app.py
"""
from __future__ import annotations

import random
from typing import Optional

import streamlit as st

from casino import Game


def init_session(player_count: int = 2, seed: Optional[int] = None) -> None:
    if "game" not in st.session_state:
        st.session_state.game = Game(player_count=player_count, rng=random.Random(seed))
        st.session_state.player_count = player_count
        st.session_state.seed = seed


def reset_game(player_count: int = 2, seed: Optional[int] = None) -> None:
    st.session_state.game = Game(player_count=player_count, rng=random.Random(seed))
    st.session_state.player_count = player_count
    st.session_state.seed = seed


def step_random_move() -> None:
    game: Game = st.session_state.game
    if game.is_over():
        return
    moves = game.legal_moves(game.active_player)
    if not moves:
        game.advance_turn()
        return
    action = game.rng.choice(moves)
    game.apply_action(game.active_player, action)
    game.advance_turn()


def auto_simulate() -> None:
    game: Game = st.session_state.game
    while not game.is_over():
        moves = game.legal_moves(game.active_player)
        if not moves:
            game.advance_turn()
            continue
        action = game.rng.choice(moves)
        game.apply_action(game.active_player, action)
        game.advance_turn()
    game.collect_remaining_table()


def main() -> None:
    st.title("Casino — 40-card numbers game")

    players = st.sidebar.selectbox("Players", [2, 3], index=0)
    seed = st.sidebar.number_input("RNG seed (0 for random)", min_value=0, value=0)
    human_player = st.sidebar.selectbox("Human player (or Auto)", ["Auto"] + [f"P{i+1}" for i in range(3)], index=0)

    if "game" not in st.session_state or st.session_state.player_count != players:
        init_session(player_count=players, seed=None if seed == 0 else seed)

    st.sidebar.button("Reset game", on_click=reset_game, args=(players, None if seed == 0 else int(seed)))
    if st.sidebar.button("Step (one random move)"):
        step_random_move()
    if st.sidebar.button("Auto-simulate to end"):
        auto_simulate()

    game: Game = st.session_state.game

    st.subheader("Table")
    st.write(game.table_state())

    st.subheader("Players")
    for idx, player in enumerate(game.players):
        st.markdown(f"**{player.name}** (active: {idx == game.active_player})")
        hand_display = " ".join(c.label for c in player.hand) or "(none)"
        st.text(f"Hand: {hand_display}")
        captured_display = " ".join(c.label for c in player.captured) or "(none)"
        st.text(f"Captured ({len(player.captured)}): {captured_display}")

    # Interactive move selection when it's the human player's turn.
    human_idx: Optional[int]
    if human_player == "Auto":
        human_idx = None
    else:
        # human_player values are like "P1", "P2", "P3" — map to index
        human_idx = int(human_player[1:]) - 1

    if not game.is_over():
        active = game.active_player
        st.info(f"Active player: {game.players[active].name}")
        moves = game.legal_moves(active)
        if human_idx is not None and human_idx == active:
            if not moves:
                st.write("No legal moves available. Passing.")
                if st.button("Pass / Advance turn"):
                    game.advance_turn()
            else:
                # build human-friendly descriptions
                def describe(a):
                    if a.kind == "throw":
                        return f"Throw card #{a.hand_index}"
                    if a.kind == "capture":
                        return f"Capture table #{a.table_index} with hand #{a.hand_index}"
                    if a.kind == "capture_build":
                        return f"Capture build #{a.build_index} with hand #{a.hand_index}"
                    if a.kind == "build":
                        return f"Build hand #{a.hand_index} + table #{a.table_index} to total {a.target_total}"
                    if a.kind == "steal_build":
                        return f"Steal top from player {a.steal_from + 1} + table #{a.table_index} to total {a.target_total}"
                    return a.kind

                descriptions = [describe(m) for m in moves]
                choice = st.selectbox("Choose move", options=list(range(len(moves))), format_func=lambda i: descriptions[i])
                if st.button("Apply move"):
                    action = moves[choice]
                    game.apply_action(active, action)
                    game.advance_turn()
        else:
            st.write("Not the human's turn (or Auto mode). Use 'Step' or 'Auto-simulate' to progress the game.")

    st.subheader("Builds")
    builds = game.builds
    if not builds:
        st.write("(none)")
    else:
        for b in builds:
            st.write(f"{b.total}: {'+'.join(c.label for c in b.cards)}")

    if game.is_over():
        game.collect_remaining_table()
        scores = game.score()
        st.success("Game over")
        for player, score in zip(game.players, scores):
            st.write(f"{player.name} score: {score} — captured {len(player.captured)} cards")


if __name__ == "__main__":
    main()
