#!/usr/bin/env python
import urllib.parse as urlparse
from const_caraibe import CHANNELS




from http.server import BaseHTTPRequestHandler, HTTPServer

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
  # Define a global index channel
  index = 2
  # GET
  def do_GET(self):
    # Send response status code
    self.send_response(200)
    print(self.path)

    # Send message back to client
    if (self.path == '/remoteControl/cmd?operation=10'):
      print(f"Current channel is: {CHANNELS[testHTTPServer_RequestHandler.index]['name']} - index: {testHTTPServer_RequestHandler.index} - epg_id: {CHANNELS[testHTTPServer_RequestHandler.index]['epg_id']}")
      json='{ "result": { "responseCode": "0", "message": "ok", "data": { "timeShiftingState": "0", "playedMediaType": "LIVE", "playedMediaState": "PLAY", "playedMediaId": "'+CHANNELS[testHTTPServer_RequestHandler.index]['epg_id']+'", "playedMediaContextId": "1", "playedMediaPosition": "NA", "osdContext": "LIVE", "macAddress": "00:1E:00:84:89:00", "wolSupport": "0", "friendlyName": "décodeur TV d\'Orange", "activeStandbyState": "0" } } }'
      message = bytes(json, 'utf8')

      # Send headers
      self.send_header('Content-type','text/json; charset=utf-8')
      self.send_header('Content-length', str(len(message)))
      self.end_headers()

      # Write content as utf-8 data
      self.wfile.write(message)

    elif self.path.startswith('/remoteControl/cmd?operation=01&key='):
      # Extract the key value from the path
      query_components = dict(urlparse.parse_qsl(urlparse.urlsplit(self.path).query))
      key = query_components.get('key', None)

      if key:
        print(f"Received key: {key}")
        if key == '402':
          testHTTPServer_RequestHandler.index += 1
          
          if testHTTPServer_RequestHandler.index >= len(CHANNELS):
            testHTTPServer_RequestHandler.index = 0
        elif key == '403':
          testHTTPServer_RequestHandler.index -= 1
          if testHTTPServer_RequestHandler.index < 0:
            testHTTPServer_RequestHandler.index = len(CHANNELS) - 1
        else:
          print(f"Key {key} received but no specific action defined.")
      else:
        print("No key found in the request.")
    return
  
def run():
  print('starting server...')

  # Server settings
  # Choose port 8080, for port 80, which is normally used for a http server, you need root access
  server_address = ('0.0.0.0', 8080)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running livebox-simulator ...')
  httpd.serve_forever()


run()