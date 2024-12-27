pm2 start misc.py -n bandit_misc --interpreter='python3'
sleep 60
pm2 start wheel.py -n wheel_misc --interpreter='python3'
sleep 60
pm2 start crate.py -n bandit_crate --interpreter='python3'
sleep 60
pm2 start spinner.py -n bandit_spinner --interpreter='python3'