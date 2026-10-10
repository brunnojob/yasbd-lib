import json
from yasbd import BoundaryDetector
text='Alpha. Beta. Gamma. Delta.'
sentences=list(BoundaryDetector('en').segment(text,preserve_whitespace=True))
assert len(sentences)==4
assert ''.join(sentences)==text
print(json.dumps({'input':text,'sentences':sentences,'lossless':True}))
