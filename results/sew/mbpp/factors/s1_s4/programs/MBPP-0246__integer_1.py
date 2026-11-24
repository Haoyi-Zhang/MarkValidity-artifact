def  babylonian_squareroot(number):
    if(number == 0):
        return 0;
    g = number / 2.0;
    g2 = g + 1;
    while(g2 != g):
        n=number/ g;
        g2=g;
        g=(n + g)/2;
    return g;