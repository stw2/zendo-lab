"""Offline interruption test: local sockets and a fake provider, no inference."""
import json, socket, threading, sys, uuid
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import claude_backend as cb
ready=threading.Event()
class Response:
 status=200
 def __init__(self,sock):self.file=sock.makefile('rb')
 def getheader(self,name):return 'text/event-stream' if name=='content-type' else None
 def getheaders(self):return [('content-type','text/event-stream')]
 def readline(self):
  line=self.file.readline()
  if line:ready.set()
  return line
class Connection:
 debuglevel=0
 def __init__(self,*args,**kwargs):self.sock,self.writer=socket.socketpair();self.response=Response(self.sock)
 def request(self,*args,**kwargs):self.writer.sendall(b'data: {"type":"partial_fixture"}\n\n')
 def getresponse(self):return self.response
 def close(self):
  self.sock.close();self.writer.close();self.response.file.close()
experiment=Path(__file__).resolve().parents[1]
trace_id=uuid.uuid4().hex
trace_path=experiment/'results/runs/preflight'/f'interrupted-proxy-fixture-{trace_id}.jsonl'
trace=cb.Trace(trace_path,trace_id)
body={'model':cb.MODELS[0],'system':[{'type':'text','text':cb.SDK_IDENTITY},{'type':'text','text':'system'}],'messages':[{'role':'user','content':'user'}],'tools':[],'max_tokens':128000,'thinking':{'type':'adaptive'},'output_config':{'effort':'high'},'stream':True}
errors=[]
with patch.object(cb.http.client,'HTTPSConnection',Connection):
 guard=cb.Guard(cb.MODELS[0],'system','user',trace)
 with guard as endpoint:
  def client():
   try:
    data=json.dumps(body).encode()
    with socket.create_connection(('127.0.0.1',guard.server.server_port),timeout=10) as client_socket:
     head=(f'POST {guard.prefix}/v1/messages HTTP/1.0\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\n\r\n').encode()
     client_socket.sendall(head+data)
     while client_socket.recv(4096):pass
   except BaseException as error:errors.append(type(error).__name__+': '+str(error))
  thread=threading.Thread(target=client);thread.start()
  assert ready.wait(5), 'fixture did not stream: '+str(errors)
 thread.join(5)
 assert not thread.is_alive(),'client stuck after guard close'
 assert guard.active_handlers==0,'handler outlived guard'
trace.write('end',{'explicit_interruption':True})
rows=[json.loads(line) for line in trace_path.read_text().splitlines()]
assert any(r['kind']=='provider_stream' and 'partial_fixture' in r['value'] for r in rows)
assert rows[-1]['kind']=='end'
report={'offline_only':True,'partial_stream_retained':True,'handlers_joined_before_trace_end':True,'client_stopped':True,'backend_source_sha256':cb.SOURCE_SHA256}
(experiment/'results/interruption-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
