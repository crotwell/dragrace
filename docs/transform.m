function[correction] =  transform(v)
A = [0.94 0 0.34; ...
      0 1 0; ...
    -.342 0 0.94];
v = v';

correction = A * v;
correction = correction';