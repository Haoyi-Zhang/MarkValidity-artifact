def babylonian_squareroot(number):
    if(number == 0):
        return  0;
    g=number/2.0;
    g2=1 + g;
    while(g != g2):
        n = number/ g;
        g2 = g;
        g = (g + n) / 2;
    return  g;
