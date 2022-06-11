# Project aim

The first part of this project aims to build a debugWire debugger with common available hardware like a standard usb-to-serial converter (FT232).

This is implemented in software (python) and is composed of two parts: the debugWire Implementation through serial interface, and a small implementation of a gdb remote target server to be able to debug the target with gdb (avr-gdb).

The second part of this project may consist of developing an arduino-like board capable of isp programming, debug interface and serial converter.

## Why

Atmel debugWire is actually supported on the standard avr programmers (Dragon-obsolate, JTAGICE-obsolete, Xplained boards) which are usable only with Atmel Studio.

What if we already have an arduino?

# My setup
## Hardware
I use a Attiny85 dev board ([Digispark usb DevBoard](http://digistump.com/products/1) [[schematics](https://s3.amazonaws.com/digistump-resources/files/97a1bb28_DigisparkSchematic.pdf)])
connected to my computer with an FT232 Usb to serial converter and a diode on the tx pin.

_TODO Make some images_

```
+---------+        +------------+                        +-----------------+
| PC (USB)|--------| FT232 (RXD)|-------+---+------------|(!RST)           |
+---------+        |       (TXD)|---|<--+   |            |                 |
                   |            |          +++           |                 |
                   |            |          | | (R1 10K)  |    ATTINY85     |
                   |            |          +++           |                 |
                   |            |           |            |                 |
                   |       (VCC)|-----------+------------|(VCC)            |
                   |       (GND)|------------------------|(GND)            |
                   +------------+                        +-----------------+
```
As the schematic represents, the diode (1N4148) is connected from the rx line, pulled up to vcc with a 10K resistor
to the FT232 TX.
Note that this setup is good for slow speeds, an improvement can be made using a transistor on the tx line.

## First set up
The fisrst thing to do is enable DebugWire. This has to be made with an ISP/HV programmer
Using an arduino and the default ArduinoISP programmer, I overran the fuse bits
to enable DWEN fuse and changed the clock source to 8MHz Internal:

_arduino isp is connected as /dev/ttyACM0_

First we check for all the connections to be working. this should read the device fingerprint
```
$avrdude -v -cstk500v1 -P /dev/ttyACM0 -b 19200 -p attiny85
```

Next we want to read the fuse memory
```
$avrdude -v -cstk500v1 -P /dev/ttyACM0 -b 19200 -p attiny85 -U lfuse:r:-:h -U hfuse:r:-:h -U efuse:r:-:h -U lock:r:-:h
```

NB If lock bits are set we need to clear the device first. i don't know how to do it =(

For my setup i choose this fuse values
- LFUSE = 0xE2 -> internal RC 8MHz oscillator
- HFUSE = 0x9D -> Debug wire enable
- EFUSE = 0xFE -> self programming enable

_you can use [this site](https://eleccelerator.com/fusecalc/fusecalc.php?chip=attiny85) to ease up the configuration_
and here is the fuse programming command.
__Note: after setting those fuses the isp interface will be unaccessible without a debugWire setup (WIP)__
You should upload a sketch or a test program before setting the fuses.
```
avrdude -v -cstk500v1 -P /dev/ttyACM0 -b 19200 -p attiny85 -U lfuse:w:0xE2:m -U hfuse:w:0x9D:m -U efuse:w:0xFE:m
```

## Test code
The code used for testing is available in `./avrtest`.
after compilation you'll find an eeprom image, flash image and the elf you can use to debug the program.

## Sources and documentation
- http://www.ruemohr.org/docs/debugwire.html DebugWire reverse engeneering
- http://ww1.microchip.com/downloads/en/devicedoc/atmel-0856-avr-instruction-set-manual.pdf
### device specific
- https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-2586-AVR-8-bit-Microcontroller-ATtiny25-ATtiny45-ATtiny85_Datasheet.pdf
