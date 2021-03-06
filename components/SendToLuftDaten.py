import requests
import msgflo

endpoint = 'https://api.luftdaten.info/v1/push-sensor-data/'
endpoint2 = 'https://api-rrd.madavi.de/data.php'

class SendToLuftDaten(msgflo.Participant):
  def __init__(self, role):
    d = {
      'component': 'c-flo/SendToLuftDaten',
      'label': 'Send environmental data to luftdaten.info',
      'icon': 'cloud-upload',
      'inports': [
        { 'id': 'pm10', 'type': 'number', 'queue': 'staub/arboretum/pm10' },
        { 'id': 'pm25', 'type': 'number', 'queue': 'staub/arboretum/pm25' },
        { 'id': 'temperature', 'type': 'number', 'queue': 'staub/arboretum/temperature' },
        { 'id': 'humidity', 'type': 'number', 'queue': 'staub/arboretum/humidity' },
        { 'id': 'sensor', 'type': 'string'  },
      ],
      'outports': [
        { 'id': 'sent', 'type': 'bang' },
        { 'id': 'skipped', 'type': 'bang' },
      ],
    }
    self.values = {
      'pm10': None,
      'pm25': None,
      'temperature': None,
      'humidity': None
    }
    self.sensorId = 'msgflo-00000042'
    msgflo.Participant.__init__(self, d, role)

  def process(self, inport, msg):
    if inport == 'sensor':
      self.sensorId = msg.data
      self.ack(msg)
      return
    self.values[inport] = msg.data
    if inport == 'pm10' or inport == 'pm25':
      if self.values['pm10'] != None and self.values['pm25'] != None:
        self.sendToLuftDaten(endpoint, 1, {
          'P1': self.values['pm10'],
          'P2': self.values['pm25'],
        })
        self.sendToLuftDaten(endpoint2, 1, {
          'SDS_P1': self.values['pm10'],
          'SDS_P2': self.values['pm25'],
        })
        self.values['pm10'] = None
        self.values['pm25'] = None
        self.send('sent', True)
      else:
        self.send('skipped', True)
    if inport == 'temperature' or inport == 'humidity':
      if self.values['temperature'] != None and self.values['humidity'] != None:
        self.sendToLuftDaten(endpoint, 11, {
          'temperature': self.values['temperature'],
          'humidity': self.values['humidity'],
        })
        self.values['temperature'] = None
        self.values['humidity'] = None
        self.send('sent', True)
      else:
        self.send('skipped', True)
    self.ack(msg)

  def sendToLuftDaten(self, url, pin, values):
    headers = {
      'X-Pin': str(pin),
      'X-Sensor': self.sensorId
    }
    json = {
      'software_version': 'microflo-luftdaten 1.0.0',
      "sensordatavalues": [{'value_type': key, 'value': val} for key, val in values.items()],
    }
    requests.post(url, headers=headers, json=json)

if __name__ == '__main__':
  msgflo.main(SendToLuftDaten)
