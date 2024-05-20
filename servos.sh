#inicializa o PORTA D do EV3 para funcionar com um servo motor comum (aquele de aeromodelismo)
#utilizamos os pinos: 5V, GND e o pino 1 (pwm)
#o pino de sinal do servo, o pino 1 deve ser ligado no servo com um dividor de tensão entre o gnd e o pino de sinal, pois o pino de sinal sai a tensão da bateria, o que queimará o servo. Coloque um dividor, uns 10k cada resistencia deve servir.

sh -c 'echo ev3-ports:outD > /sys/class/lego-port/port7/device/driver/unbind'
sh -c 'echo 0 > /sys/class/pwm/pwmchip1/export'
sh -c 'echo 83 > /sys/class/gpio/export'
sh -c 'echo 90 > /sys/class/gpio/export'
sh -c 'echo 1 > /sys/class/gpio/gpio83/value'
sh -c 'echo in > /sys/class/gpio/gpio90/direction'
sh -c 'echo 20000000 > /sys/class/pwm/pwmchip1/pwm0/period'
sh -c 'echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable'

#para controlar o servo o arquio abaixo deve ser editado enviando um valor do duty_cycle que eh a posicao.
#sh -c 'echo 610000 > /sys/class/pwm/pwmchip1/pwm0/duty_cycle' (minimo)
#sh -c 'echo 2400000 > /sys/class/pwm/pwmchip1/pwm0/duty_cycle' (maximo)
#os valores acima podem podem variar de modelo pra modelo de servo
