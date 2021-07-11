#define F_CPU 8000000UL
#include <avr/io.h>
#include <util/delay.h>

int main(void){
	DDRB |= (1 << PINB1); //PB1 is output
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
