state='{ "result": { "responseCode": "0", "message": "ok", "data": { "timeShiftingState": "0", "playedMediaType": "LIVE", "playedMediaState": "PLAY", "playedMediaId": "192", "playedMediaContextId": "1", "playedMediaPosition": "NA", "osdContext": "LIVE", "macAddress": "00:1E:00:84:89:00", "wolSupport": "0", "friendlyName": "décodeur TV d\'Orange", "activeStandbyState": "0" } } }';
#state='{ "result": { "responseCode": "0", "message": "ok", "data": { "timeShiftingState": "0", "playedMediaType": "LIVE", "playedMediaState": "PLAY", "playedMediaId": "14135", "playedMediaContextId": "1", "playedMediaPosition": "NA", "osdContext": "LIVE", "macAddress": "00:1E:00:84:89:00", "wolSupport": "0", "friendlyName": "décodeur TV d\'Orange", "activeStandbyState": "0" } } }';

#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer

# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

  # GET
  def do_GET(self):
    # Send response status code
    self.send_response(200)
    print(self.path)

    # Send message back to client
    if (self.path == '/remoteControl/cmd?operation=10'):
      json=state

      message = bytes(
        json
        , 'utf8')

      # Send headers
      self.send_header('Content-type','text/json; charset=utf-8')
      self.send_header('Content-length', str(len(message)))
      self.end_headers()

      # Write content as utf-8 data
      self.wfile.write(message)
    return

def run():
  print('starting server...')

  # Server settings
  # Choose port 8080, for port 80, which is normally used for a http server, you need root access
  server_address = ('0.0.0.0', 8080)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...')
  httpd.serve_forever()


run()