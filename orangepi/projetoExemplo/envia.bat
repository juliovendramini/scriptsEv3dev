@echo off
@rem Altere o IP para o IP do Orange Pi
scp -r *.py orange@192.168.2.193:~\projeto1\
@rem ssh orange@192.168.2.193 "killall main.py"
