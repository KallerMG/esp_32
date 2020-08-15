import network
import urequests
from machine import Pin, ADC
from time import sleep

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)  
pot_value = pot.read()
temp= ((pot_value *3.3 / 4095) *250)

import esp
esp.osdebug(None)

import gc
gc.collect()

ssid = '#erro404#'
password = 'NET10net@'

api_key = 'lHChfneH6EeVgHoO7v-7l8cte5IoLYovziUI-EzLKJb'

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Conectado')
print(station.ifconfig())

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)  

while True:
    
    try:
      pot_value = pot.read()
      temp= ((pot_value *3.3 / 4095) *250)
      print('Temperature: %2.2f C' %temp)


      sensor_readings = {'value1':round(temp, 2), 'value2':round(temp, 2)}
      print(sensor_readings)

      request_headers = {'Content-Type': 'application/json'}

      request = urequests.post('http://maker.ifttt.com/trigger/temp_sensor/with/key/' + api_key,
      json=sensor_readings,
      headers=request_headers)
      print(request.text)
      request.close()

    except OSError as e:
      print('Falha ao enviar os dados.')
    sleep(15)