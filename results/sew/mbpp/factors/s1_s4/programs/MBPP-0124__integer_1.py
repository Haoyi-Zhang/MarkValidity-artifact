import cmath
def  angle_complex(a,b):
  cn, angle=complex(a,b), cmath.phase(a+b)
  return  angle