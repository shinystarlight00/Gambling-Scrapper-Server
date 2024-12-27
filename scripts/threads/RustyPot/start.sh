pm2 start coinflip.py -n pot_coinflip --interpreter='python3'
sleep 60
pm2 start jackpot.py -n pot_jackpot --interpreter='python3'