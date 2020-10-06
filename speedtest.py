import time
from game import Hand
from game import Wall
from mahjong.hand_calculating.hand import HandCalculator, HandConfig
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter
from mahjong.agari import Agari
from mahjong.meld import Meld
import numpy as np

c = HandCalculator()
st = Shanten()
ag = Agari()

ops = 1e7

# Control Code
k = 0
cstart = time.time_ns()
while k < ops:
    k += 1
    w = Wall()
    hand = Hand(w)
    hand.draw(w)

cend = time.time_ns()

# Test Code
k = 0
start = time.time_ns()
while k < ops:
    k += 1
    w = Wall()
    hand = Hand(w)
    hand.draw(w)
    win = ag.is_agari(hand.tiles34)

end = time.time_ns()

print('Operation Time: {:.4f}us/op'.format((end - start) / (1e3 * ops)))
print('Control Time: {:.4f}us/op'.format((cend - cstart) / (1e3 * ops)))
print()
op_rate = (1e9 * ops) / (end - start)
ctrl_rate = (1e9 * ops) / (cend - cstart)
count_rate = 1e9 * ops / ((end - start) - (cend - cstart))
print('Net Operation Time: {:.4f}us/op'.format((end - start) / (1e3 * ops) - (cend - cstart) / (1e3 * ops)))
print('Operation Rate: ' + str(int(count_rate)) + u' \u00B1 ' + '{:.1f}ops/s'.format(np.sqrt(1e9 * (op_rate / (end - start) + ctrl_rate / (cend - cstart)))))