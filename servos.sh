#inicializa o PORTA D do EV3 para funcionar com um servo motor comum (aquele de aeromodelismo)
#utilizamos os pinos: 5V, GND e o pino 1 (pwm)
#o pino de sinal do servo, o pino 1 deve ser ligado no servo com um dividor de tensão entre o gnd e o pino de sinal, pois o pino de sinal sai a tensão da bateria, o que queimará o servo. Coloque um dividor, uns 10k cada resistencia deve servir.

# porta D
sh -c 'echo ev3-ports:outD > /sys/class/lego-port/port7/device/driver/unbind'
sh -c 'echo 0 > /sys/class/pwm/pwmchip1/export'
sh -c 'echo 83 > /sys/class/gpio/export'
sh -c 'echo 90 > /sys/class/gpio/export'
sh -c 'echo 1 > /sys/class/gpio/gpio83/value'
sh -c 'echo in > /sys/class/gpio/gpio90/direction'
sh -c 'echo 20000000 > /sys/class/pwm/pwmchip1/pwm0/period'
sh -c 'echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable'

#porta C
sh -c 'echo ev3-ports:outC > /sys/class/lego-port/port6/device/driver/unbind'
sh -c 'echo 0 > /sys/class/pwm/pwmchip0/export'
sh -c 'echo 104 > /sys/class/gpio/export' #GPIO_6_9
sh -c 'echo 89 > /sys/class/gpio/export' #GPIO_5_9
sh -c 'echo 1 > /sys/class/gpio/gpio104/value'
sh -c 'echo in > /sys/class/gpio/gpio89/direction'
sh -c 'echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/period'
sh -c 'echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable'

# porta A (só funciona se exportar a porta B tbm, mesmo pwm)
sh -c 'echo ev3-ports:outA > /sys/class/lego-port/port4/device/driver/unbind'
sh -c 'echo 0 > /sys/class/pwm/pwmchip5/export'
sh -c 'echo 63 > /sys/class/gpio/export' #GPIO_3_15
sh -c 'echo 54 > /sys/class/gpio/export' #GPIO_3_6
sh -c 'echo 1 > /sys/class/gpio/gpio63/value'
sh -c 'echo in > /sys/class/gpio/gpio54/direction'
sh -c 'echo 20000000 > /sys/class/pwm/pwmchip5/pwm1/period'
sh -c 'echo 1 > /sys/class/pwm/pwmchip5/pwm1/enable'

# porta B (só funciona se exportar a porta A tbm, mesmo pwm)
sh -c 'echo ev3-ports:outA > /sys/class/lego-port/port5/device/driver/unbind'
sh -c 'echo 0 > /sys/class/pwm/pwmchip5/export'
sh -c 'echo 33 > /sys/class/gpio/export' #GPIO_2_1
sh -c 'echo 3 > /sys/class/gpio/export' #GPIO_0_3
sh -c 'echo 1 > /sys/class/gpio/gpio33/value'
sh -c 'echo in > /sys/class/gpio/gpio3/direction'
sh -c 'echo 20000000 > /sys/class/pwm/pwmchip5/pwm0/period'
sh -c 'echo 1 > /sys/class/pwm/pwmchip5/pwm0/enable'


#para controlar o servo o arquio abaixo deve ser editado enviando um valor do duty_cycle que eh a posicao.
#sh -c 'echo 610000 > /sys/class/pwm/pwmchip1/pwm0/duty_cycle' (minimo)
#sh -c 'echo 2400000 > /sys/class/pwm/pwmchip1/pwm0/duty_cycle' (maximo)
#os valores acima podem podem variar de modelo pra modelo de servo

