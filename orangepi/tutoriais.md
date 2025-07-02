Verificando a partição e corrigindo erros caso o brick não queira iniciar mais:

Vamos precisar para isso do cabo serial
Precisamos inicar o orange com o terminal serial de debug, para conectar lembre-se que a velocidade serial é 115200.
Assim que o log de boot começar aparecer, fique apertando a tecla ESPAÇO do teclado para entrar no u-boot.
Após entrar no u-boot, cole em ordem os seguintes comando. Cole e Dê enter duas vezes em cada comando (as vezes o terminal fica bugado)

 * ext4load mmc 0:1 0x42000000 /boot/Image
 * ext4load mmc 0:1 0x47000000 /boot/dtb/allwinner/sun50i-h618-orangepi-zero2w.dtb
 * ext4load mmc 0:1 0x60000000 /boot/uInitrd-6.6.28-current-sunxi64
 * booti 0x42000000 0x60000000 0x47000000
 * fsck.ext4 -f /dev/mmcblk0p1

Após executar corretamente todos os comando, desligue o orange e liguei novamente. Agora, se tudo der certo, ele deve iniciar novamente.
