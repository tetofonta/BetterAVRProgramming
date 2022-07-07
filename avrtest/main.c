#define F_CPU 8000000UL
#include <avr/io.h>
#include <util/delay.h>

volatile uint8_t data = 66;

volatile uint8_t debugger_flags __attribute__((section(".dbgdata"))) __attribute__((align(2)));
volatile uint8_t * buffer __attribute__((section(".dbgdata"))) __attribute__((align(2)));

volatile uint32_t bss;

int main(void){
	debugger_flags = 0;
	buffer = ((uint8_t *) 0x0070) - 10;
	bss = 63;

	data = data + 1;

	DDRB |= (1 << PINB1);	// PB1 is output
	PORTB &= ~(1 << PINB1); //off
	
	unsigned char i = 0;
	while(1){
		PORTB |= (1 << PINB1); //on
		if(i % 2)
			_delay_ms(250);
		else
			_delay_ms(1000);
		PORTB &= ~(1 << PINB1);
		_delay_ms(500);
		i++;
	}
	return 0;
}
