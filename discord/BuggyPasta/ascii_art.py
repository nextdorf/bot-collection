ascii_logos = dict(
  arch='''
                    ▄
                   ▟█▙
                  ▟███▙
                 ▟█████▙
                ▟███████▙
               ▂▔▀▜██████▙
              ▟██▅▂▝▜█████▙
             ▟█████████████▙
            ▟███████████████▙
           ▟█████████████████▙
          ▟███████████████████▙
         ▟█████████▛▀▀▜████████▙
        ▟████████▛      ▜███████▙
       ▟█████████        ████████▙
      ▟██████████        █████▆▅▄▃▂
     ▟██████████▛        ▜█████████▙
    ▟██████▀▀▀              ▀▀██████▙
   ▟███▀▘                       ▝▀███▙
  ▟▛▀                               ▀▜▙
  '''
)

def cleanArt(ascii: str, rstrip:bool = True):
  asciiLs = ascii.splitlines()
  while not asciiLs[0].strip():
    asciiLs = asciiLs[1:]
  while not asciiLs[-1].strip():
    asciiLs = asciiLs[:-1]
  padL = float('inf')
  for l in asciiLs:
    i = 0
    maxLen = min(padL, len(l))
    while i<maxLen and l[i]==' ':
      i+=1
    padL = i
    if padL==0: break
  if padL==0: padL = None

  if rstrip:
    asciiLs = [l[padL:].rstrip() for l in asciiLs]
  else:
    padR = float('inf')
    for l in asciiLs:
      i = 0
      maxLen = min(padR, len(l))
      while i<maxLen and l[len(l)-i-1]==' ':
        i+=1
      padR = i
      if padR==0: break
    padR = -padR if padR>0 else None
    asciiLs = [l[padL : padR] for l in asciiLs]
  return '\n'.join(asciiLs)

ascii_logos = {k:cleanArt(v) for k,v in ascii_logos.items()}
