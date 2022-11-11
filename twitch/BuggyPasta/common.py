import sys
import pathlib
newPath = str((pathlib.Path(__file__) / '../../../common').resolve())
if newPath not in sys.path:
  print('Add', newPath, file=sys.stderr)
  sys.path.insert(0, newPath)
