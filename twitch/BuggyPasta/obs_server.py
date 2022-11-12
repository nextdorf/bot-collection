from pathlib import Path
import http
import http.server
import urllib.parse
import os
import threading


imageAtlas = [
  None,
  'Tux.png',
  'logo.png',
]

class ObsHandle(http.server.BaseHTTPRequestHandler):
  KeepRunning = True
  Logging = True
  mimes = dict(html='text/html', jpg='image/jpg', gif='image/gif', js='application/javascript',
    css='text/css', png='image/png')
  atlasIdx = 0
  dTime = 1000 # refresh rate pro ms
  def do_GET(self):
    if self.path == '/':
      self.do_GET_Root()
    else:
      self.do_GET_Load()


  def do_GET_Root(self):
    img = imageAtlas[ObsHandle.atlasIdx % len(imageAtlas)]
    imgTag = f'<img src="/images/{img}">' if img is not None else ''
    html = f'''
      <!DOCTYPE html>
      <html>
      <head></head>
      <body>
        <script>
          setTimeout("location.reload(true);", {ObsHandle.dTime});
        </script>
        {imgTag}
      </body>
      </html>'''.encode('ascii')
    self.send_response(http.HTTPStatus.OK)
    self.send_header('Content-type', 'text/html')
    self.send_header('Content-Length', str(len(html)))
    self.end_headers()
    self.wfile.write(html)

  def do_GET_Load(self):
    ext = self.path.split('.')[-1]
    mimetype = ObsHandle.mimes.get(ext, None)
    if mimetype:
      path = str(Path('.') / self.path[1:])
      with open(path, 'rb') as f:
        self.send_response(http.HTTPStatus.OK)
        self.send_header('Content-type',mimetype)
        self.end_headers()
        self.wfile.write(f.read())

  def log_message(self, format: str, *args):
    if ObsHandle.Logging:
      super().log_message(format, *args)



def runAsync():
  httpd = http.server.HTTPServer(('localhost', 3001), ObsHandle)
  # httpd.timeout = 1
  ObsHandle.KeepRunning = True
  ObsHandle.Logging = False
  while ObsHandle.KeepRunning:
    httpd.handle_request()

t = threading.Thread(target=runAsync)

ObsHandle.KeepRunning = False
ObsHandle.atlasIdx = 0

t.start()
t.is_alive()
t.join()
