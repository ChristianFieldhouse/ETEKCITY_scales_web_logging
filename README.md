# ETEKCITY_scales_web_logging
Code for microcontrollers added to ETEKCITY bathroom scales to intercept and decode the signals sent to the liquid crystal display, 
and send that code to Google sheets.

I used a needle to thread wires through the silicone pad connecting the PCB to the LCD screen. Those wires were attached to the pins on a Pi Pico.
pico_code/main.py has the logic for turning those signals into the number displayed.

![PXL_20230114_132846777](https://user-images.githubusercontent.com/48842799/221357058-f5244ead-60aa-4119-8a36-676a4b7301e9.jpg)

The pi pico turns on an NodeMCU esp8266 module and sends over that number. The esp8266 then writes that number to google sheets Apps script, which
takes that number and adds it to the sheet along with the date and time.
