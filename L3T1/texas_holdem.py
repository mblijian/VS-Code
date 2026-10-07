"""
Texas Hold'em - Console Edition
================================
You play against three computer opponents. Everyone starts with 1000 chips.
The game ends when you run out of chips, when you are the last player left,
or when you type q between hands.

How a hand works:
  1. Each player gets 2 private cards ("hole cards").
  2. Two players post forced bets called blinds.
  3. Betting rounds happen after: the deal (pre-flop), 3 shared cards (flop),
     a 4th shared card (turn), and a 5th shared card (river).
  4. Remaining players compare their best 5-card hand from 7 cards.

Python concepts used in this file:
  classes and objects, lists, dictionaries, tuples, loops, functions,
  random.shuffle, itertools.combinations, collections.Counter,
  tuple comparison, input validation with try/except.

Run with:  python texas_holdem.py
"""

import random
from collections import Counter
from itertools import combinations

# ---------------------------------------------------------------
# Settings (easy for students to change)
# ---------------------------------------------------------------
STARTING_CHIPS = 1000
SMALL_BLIND = 10
BIG_BLIND = 20
BOT_NAMES = ["Ada", "Turing", "Grace"]

SUITS = ["♠", "♥", "♦", "♣"]          # If your console shows ?, use ["S","H","D","C"]
FACE_NAMES = {11: "J", 12: "Q", 13: "K", 14: "A"}
HAND_NAMES = [
    "High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight",
    "Flush", "Full House", "Four of a Kind", "Straight Flush",
]


# ---------------------------------------------------------------
# Cards and deck
# ---------------------------------------------------------------
class Card:
    def __init__(self, value, suit):
        self.value = value          # 2 .. 14 (14 = Ace)
        self.suit = suit

    def __str__(self):
        return FACE_NAMES.get(self.value, str(self.value)) + self.suit


class Deck:
    def __init__(self):
        self.cards = [Card(v, s) for s in SUITS for v in range(2, 15)]
        random.shuffle(self.cards)

    def deal(self, n=1):
        return [self.cards.pop() for _ in range(n)]


def show(cards):
    return " ".join(str(c) for c in cards) if cards else "(none)"


# ---------------------------------------------------------------
# Hand evaluation
# A hand's score is a tuple: (category, tie-breakers...)
# Python compares tuples left to right, so a bigger tuple = better hand.
# ---------------------------------------------------------------
def score_five(cards):
    values = sorted((c.value for c in cards), reverse=True)
    counts = Counter(values)
    # Sort groups by (how many, card value): e.g. full house K K K 9 9 -> [(13,3),(9,2)]
    groups = sorted(counts.items(), key=lambda g: (g[1], g[0]), reverse=True)
    ranked_values = [v for v, _ in groups]

    is_flush = len({c.suit for c in cards}) == 1
    unique = sorted(set(values), reverse=True)
    straight_high = None
    if len(unique) == 5:
        if unique[0] - unique[4] == 4:
            straight_high = unique[0]
        elif unique == [14, 5, 4, 3, 2]:      # A-2-3-4-5, the "wheel"
            straight_high = 5

    if straight_high and is_flush:
        return (8, straight_high)
    if groups[0][1] == 4:
        return (7, *ranked_values)
    if groups[0][1] == 3 and groups[1][1] == 2:
        return (6, *ranked_values)
    if is_flush:
        return (5, *values)
    if straight_high:
        return (4, straight_high)
    if groups[0][1] == 3:
        return (3, *ranked_values)
    if groups[0][1] == 2 and groups[1][1] == 2:
        return (2, *ranked_values)
    if groups[0][1] == 2:
        return (1, *ranked_values)
    return (0, *values)


def best_hand(cards):
    """Best score from any 5 of the given cards (7 cards -> 21 combinations)."""
    return max(score_five(combo) for combo in combinations(cards, 5))


# ---------------------------------------------------------------
# Players
# ---------------------------------------------------------------
class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.chips = STARTING_CHIPS
        self.reset_for_hand()

    def reset_for_hand(self):
        self.hand = []
        self.folded = False
        self.bet = 0          # chips put in during the current betting round
        self.total_in = 0     # chips put in during the whole hand (for side pots)

    def can_act(self):
        return not self.folded and self.chips > 0

    def put_in(self, amount):
        amount = min(amount, self.chips)
        self.chips -= amount
        self.bet += amount
        self.total_in += amount
        return amount


# ---------------------------------------------------------------
# Computer player "brain"
# ---------------------------------------------------------------
def hand_strength(hole, board):
    """Rough estimate from 0 (terrible) to 1 (unbeatable)."""
    if not board:  # pre-flop: judge the two hole cards
        high, low = sorted((c.value for c in hole), reverse=True)
        s = (high + low) / 28 * 0.5
        if high == low:
            s += 0.3 + high / 14 * 0.2
        if hole[0].suit == hole[1].suit:
            s += 0.05
        if high - low == 1:
            s += 0.03
        return min(s, 1.0)

    category = best_hand(hole + board)[0]
    base = [0.2, 0.45, 0.65, 0.75, 0.82, 0.86, 0.93, 0.97, 1.0][category]
    if category == 0:
        base += max(c.value for c in hole) / 14 * 0.1
    # If the shared board alone is just as good, our cards are not helping much
    if len(board) == 5 and best_hand(board)[0] >= category:
        base -= 0.2
    return base


def bot_decide(player, to_call, current_bet, min_raise, pot, board):
    s = hand_strength(player.hand, board) + random.uniform(-0.1, 0.1)
    raise_to = current_bet + max(min_raise, pot // 2)

    if to_call == 0:
        if s > 0.7 or random.random() < 0.08:   # sometimes bluff
            return "raise", raise_to
        return "call", 0                          # check

    pot_odds = to_call / (pot + to_call)
    if s > 0.8 and random.random() < 0.5:
        return "raise", raise_to
    if s > pot_odds + 0.05 or (to_call <= BIG_BLIND and s > 0.3):
        return "call", 0
    return "fold", 0


# ---------------------------------------------------------------
# Safe input
# ---------------------------------------------------------------
def ask(prompt):
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return "q"


# ---------------------------------------------------------------
# The game
# ---------------------------------------------------------------
class Game:
    def __init__(self):
        self.players = [Player("You", is_human=True)] + [Player(n) for n in BOT_NAMES]
        self.button = 0
        self.quit = False

    # ----- main loop -----
    def play(self):
        print("=" * 50)
        print("        TEXAS HOLD'EM  -  You vs the computer")
        print("=" * 50)
        hand_number = 0
        while not self.quit:
            human = self.players[0]
            alive = [p for p in self.players if p.chips > 0]
            if human.chips == 0:
                print("\nYou are out of chips. Game over!")
                break
            if len(alive) == 1:
                print("\nYou won every chip at the table. Champion!")
                break
            hand_number += 1
            self.play_hand(alive, hand_number)
            self.button += 1
            if not self.quit and ask("\nPress Enter for the next hand, or q to quit: ") == "q":
                break

        print("\nFinal chip counts:")
        for p in sorted(self.players, key=lambda p: p.chips, reverse=True):
            print(f"  {p.name:<8} {p.chips}")

    # ----- one hand -----
    def play_hand(self, seats, number):
        n = len(seats)
        dealer = self.button % n
        for p in seats:
            p.reset_for_hand()

        deck = Deck()
        for p in seats:
            p.hand = deck.deal(2)

        sb = dealer if n == 2 else (dealer + 1) % n   # heads-up: dealer posts small blind
        bb = (sb + 1) % n
        seats[sb].put_in(SMALL_BLIND)
        seats[bb].put_in(BIG_BLIND)

        print(f"\n{'-' * 50}\nHand #{number}   Dealer: {seats[dealer].name}")
        print(f"{seats[sb].name} posts small blind {SMALL_BLIND}, "
              f"{seats[bb].name} posts big blind {BIG_BLIND}")
        print(f"Your cards: {show(seats[0].hand) if seats[0].is_human else ''}")

        board = []
        stages = [("PRE-FLOP", 0), ("FLOP", 3), ("TURN", 1), ("RIVER", 1)]
        for stage, new_cards in stages:
            if sum(not p.folded for p in seats) == 1:
                break
            if new_cards:
                board += deck.deal(new_cards)
                for p in seats:
                    p.bet = 0
            first = (bb + 1) % n if stage == "PRE-FLOP" else (dealer + 1) % n
            print(f"\n--- {stage} ---   Board: {show(board)}   Pot: {self.pot(seats)}")
            self.betting_round(seats, first, board)
            if self.quit:
                return

        self.showdown(seats, board)

    def pot(self, seats):
        return sum(p.total_in for p in seats)

    # ----- betting -----
    def betting_round(self, seats, start, board):
        n = len(seats)
        order = [seats[(start + i) % n] for i in range(n)]
        current_bet = max(p.bet for p in seats)
        min_raise = BIG_BLIND
        waiting = [p for p in order if p.can_act()]

        while waiting:
            if sum(not p.folded for p in seats) == 1:
                return
            p = waiting.pop(0)
            if not p.can_act():
                continue
            to_call = current_bet - p.bet
            others = [q for q in seats if q is not p and q.can_act()]
            if to_call == 0 and not others:
                continue                     # nobody left to bet against

            pot = self.pot(seats)
            if p.is_human:
                action, amount = self.ask_human(p, to_call, current_bet, min_raise, pot, board)
                if self.quit:
                    return
            else:
                action, amount = bot_decide(p, to_call, current_bet, min_raise, pot, board)

            if action == "fold":
                p.folded = True
                print(f"  {p.name} folds")
            elif action == "call":
                paid = p.put_in(to_call)
                if to_call == 0:
                    print(f"  {p.name} checks")
                else:
                    print(f"  {p.name} calls {paid}" + (" (all-in)" if p.chips == 0 else ""))
            else:  # raise to `amount`
                amount = min(amount, p.bet + p.chips)
                p.put_in(amount - p.bet)
                if p.bet > current_bet:
                    min_raise = max(min_raise, p.bet - current_bet)
                    current_bet = p.bet
                    print(f"  {p.name} raises to {p.bet}" + (" (all-in)" if p.chips == 0 else ""))
                    i = order.index(p)
                    waiting = [order[(i + k) % n] for k in range(1, n)
                               if order[(i + k) % n].can_act()]
                else:
                    print(f"  {p.name} calls {p.bet} (all-in)")

    def ask_human(self, p, to_call, current_bet, min_raise, pot, board):
        print(f"\n  Your cards: {show(p.hand)}   Board: {show(board)}")
        print(f"  Pot: {pot}   Your chips: {p.chips}   To call: {to_call}")
        while True:
            choice = "[c]heck" if to_call == 0 else f"[c]all {min(to_call, p.chips)}"
            a = ask(f"  {choice}, [r]aise, [a]ll-in, [f]old, [q]uit > ")
            if a == "q":
                self.quit = True
                return "fold", 0
            if a == "f":
                return "fold", 0
            if a == "c":
                return "call", 0
            if a == "a":
                return "raise", p.bet + p.chips
            if a == "r":
                max_to = p.bet + p.chips
                min_to = min(current_bet + min_raise, max_to)
                if p.chips <= to_call:
                    print("  You don't have enough to raise. Use [c] to call all-in.")
                    continue
                try:
                    amount = int(ask(f"  Raise to how much? ({min_to}-{max_to}) > "))
                except ValueError:
                    print("  Please type a whole number.")
                    continue
                if min_to <= amount <= max_to:
                    return "raise", amount
                print(f"  The amount must be between {min_to} and {max_to}.")
            else:
                print("  Please type c, r, a, f or q.")

    # ----- showdown and side pots -----
    def showdown(self, seats, board):
        contenders = [p for p in seats if not p.folded]
        if len(contenders) == 1:
            winner = contenders[0]
            total = self.pot(seats)
            winner.chips += total
            print(f"\n{winner.name} wins {total} chips (everyone else folded)")
            self.print_chips(seats)
            return

        print(f"\n--- SHOWDOWN ---   Board: {show(board)}")
        scores = {}
        for p in contenders:
            scores[p] = best_hand(p.hand + board)
            print(f"  {p.name:<8} {show(p.hand):<8} {HAND_NAMES[scores[p][0]]}")

        # Split the money into pots by contribution level (handles all-ins)
        levels = sorted({p.total_in for p in seats if p.total_in > 0})
        previous = 0
        for level in levels:
            pot = sum(min(p.total_in, level) - min(p.total_in, previous) for p in seats)
            previous = level
            if pot == 0:
                continue
            eligible = [p for p in contenders if p.total_in >= level] or contenders
            top = max(scores[p] for p in eligible)
            winners = [p for p in eligible if scores[p] == top]
            share, leftover = divmod(pot, len(winners))
            for w in winners:
                w.chips += share
            winners[0].chips += leftover
            names = " and ".join(w.name for w in winners)
            print(f"  {names} win{'s' if len(winners) == 1 else ''} {pot} "
                  f"with {HAND_NAMES[top[0]]}")
        self.print_chips(seats)

    def print_chips(self, seats):
        print("  Chips: " + ", ".join(f"{p.name} {p.chips}" for p in seats))


if __name__ == "__main__":
    Game().play()
