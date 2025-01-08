# pm2 start coinflip.py -n pot_coinflip_1 --interpreter='python3'
# sleep 60
# pm2 start jackpot.py -n pot_jackpot --interpreter='python3'

pm2 start coinflip.py -n pot_coinflip --interpreter='../../venv/bin/python'
sleep 10
pm2 start jackpot.py -n pot_jackpot --interpreter='../../venv/bin/python'