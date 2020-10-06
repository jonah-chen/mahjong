import numpy as np
from mahjong.tile import TilesConverter
from mahjong.meld import Meld
import mahjong.constants as const
from mahjong.hand_calculating.hand import HandCalculator, HandConfig
from mahjong.agari import Agari

calculator = HandCalculator()
agari = Agari()


class Wall:
    def __init__(self):  # creates a random wall, just like shuffling
        self.contents = list(range(136))
        np.random.shuffle(self.contents)
        self.length = 136

    def __str__(self):
        return 'length=' + str(self.length)

    def draw(self):  # draws a random tile.
        a = self.contents[0]
        self.contents = self.contents[1:]
        self.length -= 1
        return a


class Hand:
    def __init__(self, wall):
        self.hand = []
        for i in range(13):
            self.hand.append(int(wall.draw()))
        self.melds = []
        self.pond = []
        self.is_richii = False
        self.pot_win_tile = None

        self.tiles34 = TilesConverter.to_34_array(self.hand)
        self.melds34 = []

    def __str__(self):
        return TilesConverter.to_one_line_string(self.hand)

    # useful methods
    def draw(self, wall):
        self.pot_win_tile = wall.draw()
        self.hand.append(self.pot_win_tile)
        self.tiles34[self.pot_win_tile // 4] += 1

    def add(self, id):
        self.pot_win_tile = id
        self.hand.append(self.pot_win_tile)

    def discard(self, id):
        # returns whether a legal discard is made
        # id from 0-33 for normal tiles: 34-36 are for red fives
        if id == 34:
            target = 16
        elif id == 35:
            target = 88
        elif id == 36:
            target = 52
        else:
            target = id * 4
            for i in range(len(self.hand)):
                if 4 > self.hand[i] - target >= 0:
                    t = self.hand.pop(i)
                    self.pond.append(t)
                    self.tiles34[id] += 1
                    return t
            return -1
        for i in range(len(self.hand)):
            if self.hand[i] == target:
                t = self.hand.pop(i)
                self.pond.append(t)
                self.tiles34[target // 4] += 1
                return t
        return -1

    def kong(self, id, opened=True):
        id34 = id // 4
        if (self.tiles34[id34] == 3 and opened) or self.tiles34[id34] == 4:
            self.melds.append(
                Meld(meld_type=Meld.KAN, opened=opened, tiles=list(range(4 * id34, 4 * id34 + 4))))
            self.melds34.append([4 if j == id34 else 0 for j in range(34)])
            for i in range(len(self.hand)):
                if self.hand[i] // 4 == id // 4:
                    self.hand.pop(i)

            self.tiles34[id34] = 0
            return True
        return False

    def pong(self, id):
        tiles = [id]
        for t in self.hand:
            if t - t % 4 == id - id % 4:
                tiles.append(t)
        if len(tiles) != 3:
            return False
        self.melds.append(Meld(meld_type=Meld.PON, tiles=tiles))
        self.melds34.append([3 if j == id // 4 else 0 for j in range(34)])
        self.hand.remove(tiles[1])
        self.hand.remove(tiles[2])
        self.tiles34[id // 4] = 0
        return True

    def chi(self, id, z):
        # z=-1:lower tile
        # z=0 :middle tile
        # z=1 :higher tile

        if id >= 27 * 4:  # honor tiles
            return False
        a, b = (-1, -1)
        if z == -1:
            if 9 * 4 - 8 <= id < 9 * 4 or 9 * 8 - 8 <= id < 9 * 8 or 9 * 12 - 8 <= id:
                return False
            for t in self.hand:
                if t - t % 4 == 4 + id - id % 4:
                    a = t
                if t - t % 4 == 8 + id - id % 4:
                    b = t
        elif z == 0:
            if id < 4 or 9 * 4 - 4 <= id < 9 * 4 + 4 or 9 * 8 - 4 <= id < 9 * 8 + 4 or 9 * 12 - 4 <= id:
                return False
            for t in self.hand:
                if t - t % 4 == -4 + id - id % 4:
                    a = t
                if t - t % 4 == 4 + id - id % 4:
                    b = t
        elif z == 1:
            if id < 8 or 9 * 4 <= id < 9 * 4 + 8 or 9 * 8 <= id < 9 * 8 + 8:
                return False
            for t in self.hand:
                if t - t % 4 == -8 + id - id % 4:
                    a = t
                if t - t % 4 == -4 + id - id % 4:
                    b = t
        else:
            return False
        if a + b < 0:
            return False
        self.melds.append(Meld(meld_type=Meld.CHI, tiles=[a, b, id]))
        self.melds34.append(TilesConverter.to_34_array([a, b, id]))
        self.hand.remove(a)
        self.hand.remove(b)
        self.tiles34[a // 4] -= 1
        self.tiles34[b // 4] -= 1
        return True

    def richii(self):
        self.is_richii = True


class Stage:

    def __init__(self, prevailing_wind, round_number):
        self.prevailing_wind = prevailing_wind
        self.round_number = round_number
        self.wall = Wall()

        # deals hands to players
        self.hands = [Hand(self.wall), Hand(self.wall), Hand(self.wall), Hand(self.wall)]

        # dora indicator is in [0,136), but dora is in [0,34)
        self.dora_indicators = [self.wall.draw()]

        dora1 = self.dora_indicators[0] // 4
        if dora1 == const.NORTH:
            self.dora = [const.EAST]
        elif dora1 == const.HAKU:
            self.dora = [const.HATSU]
        elif dora1 % 9 == 8:
            self.dora = [dora1 - 8]
        else:
            self.dora = [dora1 + 1]
        self.end_state = None

    @staticmethod
    def player_wind(self, player):
        if player == 0:
            return const.EAST
        elif player == 1:
            return const.SOUTH
        elif player == 2:
            return const.WEST
        elif player == 3:
            return const.NORTH
        else:
            return None

    def win(self, player, win_tile, is_tsumo=False):
        if agari.is_agari():
            value = calculator.estimate_hand_value(self.hands[player].hand, win_tile, self.hands[player].melds,
                                                   dora_indicators=self.dora_indicators,
                                                   config=HandConfig(is_tsumo=is_tsumo,
                                                                     is_riichi=self.hands[player].is_richii,
                                                                     player_wind=self.player_wind(player),
                                                                     round_wind=self.prevailing_wind))
            return value.cost
        return None

    # actions[] is a bool array for the actions of
    #
    #
    def turn(self, player, actions):
        # every turn begins with draw
        self.hands[player].draw(self.wall)

        # checks for tsumo win
        hand_val = self.win(player, self.hands[player].pot_win_tile, is_tsumo=True)
        if hand_val is not None:
            if player == 0:
                self.end_state = [3 * hand_val['main'] / 1000, -hand_val['main'] / 1000, -hand_val['main'] / 1000, -hand_val['main'] / 1000]
            else:
                self.end_state = [-hand_val['main'] / 1000, -hand_val['additional'] / 1000, -hand_val['additional'] / 1000, -hand_val['additional'] / 1000]
                self.end_state[player] = hand_val['main'] / 1000 + hand_val['additional'] / 500
            return True # return value is whether the game ends

        # return the state to the player here. player will make decision to call kong if possible.





class Game:
    def __init__(self):
        self.points = [25, 25, 25, 25]
