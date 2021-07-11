
elf: main.c
	avr-gcc main.c -o main.elf -ggdb -Os -mmcu=attiny85
	avr-size -A main.elf

eeprom_image: main.elf
	avr-objcopy -O binary -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings --change-section-lma .eeprom=0 main.elf main.eep.bin

fw_image: main.elf
	avr-objcopy -O binary -R .eeprom main.elf main.flash.bin

all: elf eeprom_image fw_image
