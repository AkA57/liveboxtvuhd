#!/usr/bin/env python
import urllib.parse as urlparse
from const_france import CHANNELS
from http.server import BaseHTTPRequestHandler, HTTPServer

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
  # Define a global index channel
  index = 1
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

    elif self.path.startswith('/remoteControl/cmd?operation=09'):
      query_components = dict(urlparse.parse_qsl(urlparse.urlsplit(self.path).query))
      epg_id = query_components.get('epg_id', None)

      if epg_id:
        # Strip padding characters (e.g. "******1234" -> "1234")
        epg_id_clean = epg_id.lstrip('*')
        found = False
        for i, ch in enumerate(CHANNELS):
          if ch['epg_id'] == epg_id_clean:
            testHTTPServer_RequestHandler.index = i
            print(f"Channel change to: {ch['name']} - index: {i} - epg_id: {epg_id_clean}")
            found = True
            break
        if not found:
          print(f"Channel with epg_id {epg_id_clean} not found.")
      else:
        print("No epg_id found in the request.")

      message = bytes('{ "result": { "responseCode": "0", "message": "ok" } }', 'utf8')
      self.send_header('Content-type','text/json; charset=utf-8')
      self.send_header('Content-length', str(len(message)))
      self.end_headers()
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

      message = bytes('{ "result": { "responseCode": "0", "message": "ok" } }', 'utf8')
      self.send_header('Content-type','text/json; charset=utf-8')
      self.send_header('Content-length', str(len(message)))
      self.end_headers()
      self.wfile.write(message)
    return
  
def run():
  print('starting server...')
  # Server settings
  server_address = ('0.0.0.0', 8080)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running livebox-simulator on port 8080...')
  httpd.serve_forever()
run()