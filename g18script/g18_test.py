# encoding=utf8
import sys
sys.path.insert(0, "..")
from moa.moa import *
from moa import moa


if __name__ == "__main__":
    set_serialno()
    moa.OP_DELAY = 0.5
    touch("templates/login_game.png")
