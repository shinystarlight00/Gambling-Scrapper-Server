import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), './threads'))

# Scripts
from RustyPot import RustyPot
from BanditCamp import BanditCamp
from RustClash import RustClash

def f_run(func):
    func()

with ThreadPoolExecutor() as executor:
    executor.map(f_run, [
        RustyPot(),
        # BanditCamp(),
        # RustClash()
    ])