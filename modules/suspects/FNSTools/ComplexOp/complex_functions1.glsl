// Math below is taken from Ricky Reusser shader - https://www.shadertoy.com/view/tlcGzf

// Complex math! Beware that these functions are not all great for overflow,
// even though a GPU is precisely the sort of place where you ought to be 
// *very* concerned about overflow.
//
// This also includes a partial implementation of automatic differentiation
// for complex arithmetic using vec4 as a + bi --> vec4(a, b, da, db). This
// may be used to successfully avoid standard derivatives, though I just
// didn't find it worthwhile when standard derivatives are so easy and well
// supported.

#define PI 3.141592653589793238
#define TO_RADIANS 0.01745329251
#define HALF_PI 1.57079633
#define HALF_PI_INV 0.15915494309
#define PI_INV 0.31830988618
#define TWO_PI 6.28318530718
vec2 rotateUV(vec2 uv, float rotation)
{
    float mid = 0.5;
    return vec2(
        cos(rotation) * (uv.x - mid) + sin(rotation) * (uv.y - mid) + mid,
        cos(rotation) * (uv.y - mid) - sin(rotation) * (uv.x - mid) + mid
    );
}

vec2 rotateUV(vec2 uv, float rotation, vec2 mid)
{
    return vec2(
      cos(rotation) * (uv.x - mid.x) + sin(rotation) * (uv.y - mid.y) + mid.x,
      cos(rotation) * (uv.y - mid.y) - sin(rotation) * (uv.x - mid.x) + mid.y
    );
}

vec2 rotateUV(vec2 uv, float rotation, float mid)
{
    return vec2(
      cos(rotation) * (uv.x - mid) + sin(rotation) * (uv.y - mid) + mid,
      cos(rotation) * (uv.y - mid) - sin(rotation) * (uv.x - mid) + mid
    );
}

float hypot (vec2 z) {
  float x = abs(z.x);
  float y = abs(z.y);
  float t = min(x, y);
  x = max(x, y);
  t = t / x;
  return x * sqrt(1.0 + t * t);
}

float cmod (vec2 z) {
  return hypot(z);
} 

float cabs (vec2 z) {
  return cmod(z);
}


vec2 csqr (vec2 z) {
  return vec2(
    z.x * z.x - z.y * z.y,
    2.0 * z.x * z.y
  );
} 

vec2 cconst(vec2 z) {
	return z;
}

// not sure if include? could be fun for higher order that is not 2^N
vec2 cpow (vec2 z, float x) {
  float r = hypot(z);
  float theta = atan(z.y, z.x) * x;
  return vec2(cos(theta), sin(theta)) * pow(r, x);
}

vec2 csqrt (vec2 z) {
  float t = sqrt(2.0 * (cmod(z) + (z.x >= 0.0 ? z.x : -z.x)));
  vec2 f = vec2(0.5 * t, abs(z.y) / t);

  if (z.x < 0.0) f.xy = f.yx;
  if (z.y < 0.0) f.y = -f.y;

  return f;
}

vec2 cexp(vec2 z) {
  return vec2(cos(z.y), sin(z.y)) * exp(z.x);
} 

vec2 clog(vec2 z) {
  return vec2(
    log(hypot(z)),
    atan(z.y, z.x)
  );
}

vec2 clogn(vec2 z, float n) {
  return clog(z)/log(n);
}

vec2 cinv (vec2 b) {
  float e, f;
  vec2 g = vec2(1, -1);

  if( abs(b.x) >= abs(b.y) ) {
    e = b.y / b.x;
    f = b.x + b.y * e;
    g.y = -e;
  } else {
    e = b.x / b.y;
    f = b.x * e + b.y;
    g.x = e;
  }

  return g / f;
} 

vec2 cabs2 (vec2 z) {
  return vec2(cmod(z),0);
}

vec2 cconj (vec2 z) {
  return vec2(z.x, -z.y);
} 


//////////////////////

vec2 sinhcosh (float x) {
  vec2 ex = exp(vec2(x, -x));
  return 0.5 * (ex - vec2(ex.y, -ex.x));
}

vec2 catan (vec2 z) {
  float a = z.x * z.x + (1.0 - z.y) * (1.0 - z.y);
  vec2 b = clog(vec2(1.0 - z.y * z.y - z.x * z.x, -2.0 * z.x) / a);
  return 0.5 * vec2(-b.y, b.x);
} 

vec2 catanh (vec2 z) {
  float oneMinus = 1.0 - z.x;
  float onePlus = 1.0 + z.x;
  float d = oneMinus * oneMinus + z.y * z.y;

  vec2 x = vec2(onePlus * oneMinus - z.y * z.y, z.y * 2.0) / d;

  vec2 result = vec2(log(hypot(x)), atan(x.y, x.x)) * 0.5;

  return result;
} 

vec2 cacos (vec2 z) {
  vec2 a = csqrt(vec2(
    z.y * z.y - z.x * z.x + 1.0,
    -2.0 * z.x * z.y
  ));

  vec2 b = clog(vec2(a.x - z.y, a.y + z.x));
  return vec2(HALF_PI - b.y, b.x);
} 

vec2 cacosh (vec2 z) {
  vec2 a = cacos(z);

  if (a.y <= 0.0) {
    return vec2(-a.y, a.x);
  }

  return vec2(a.y, -a.x);
} 

vec2 cacot (vec2 z) {
  return catan(vec2(z.x, -z.y) / dot(z, z));
} 

vec2 cacoth(vec2 z) {
  return catanh(vec2(z.x, -z.y) / dot(z, z));
} 

vec2 casin (vec2 z) {
  vec2 a = csqrt(vec2(
    z.y * z.y - z.x * z.x + 1.0,
    -2.0 * z.x * z.y
  ));

  vec2 b = clog(vec2(
    a.x - z.y,
    a.y + z.x
  ));

  return vec2(b.y, -b.x);
} 

vec2 casinh (vec2 z) {
  vec2 res = casin(vec2(z.y, -z.x));
  return vec2(-res.y, res.x);
} 

vec2 cacsch(vec2 z) {
  return casinh(vec2(z.x, -z.y) / dot(z, z));
} 

vec2 casec (vec2 z) {
  float d = dot(z, z);
  return cacos(vec2(z.x, -z.y) / dot(z, z));
} 

vec2 casech(vec2 z) {
  return cacosh(vec2(z.x, -z.y) / dot(z, z));
} 

vec2 csin (vec2 z) {
  return sinhcosh(z.y).yx * vec2(sin(z.x), cos(z.x));
} 

vec2 ccos (vec2 z) {
  return sinhcosh(z.y).yx * vec2(cos(z.x), -sin(z.x));
} 

vec2 ccosh (vec2 z) {
  return sinhcosh(z.x).yx * vec2(cos(z.y), sin(z.y));
} 

vec2 ccot (vec2 z) {
  z *= 2.0;
  vec2 sch = sinhcosh(z.y);
  return vec2(-sin(z.x), sch.x) / (cos(z.x) - sch.y);
} 

vec2 ccoth(vec2 z) {
  z *= 2.0;
  vec2 sch = sinhcosh(z.x);
  return vec2(sch.x, -sin(z.y)) / (sch.y - cos(z.y));
} 

vec2 ccsc (vec2 z) {
  float d = 0.25 * (exp(2.0 * z.y) + exp(-2.0 * z.y)) - 0.5 * cos(2.0 * z.x);

  return sinhcosh(z.y).yx * vec2(sin(z.x), -cos(z.x)) / d;
} 

vec2 ccsch (vec2 z) {
  vec2 sch = sinhcosh(z.x);
  float d = cos(2.0 * z.y) - (exp(2.0 * z.x) + exp(-2.0 * z.x)) * 0.5;
  return vec2(-cos(z.y), sin(z.y)) * sch / (0.5 * d);
} 

vec2 cadd (vec2 a, vec2 b) {
  return a + b;
}

vec2 csub (vec2 a, vec2 b) {
  return a - b;
}

vec2 cdiv (vec2 a, vec2 b) {
  float e, f;
  float g = 1.0;
  float h = 1.0;

  if( abs(b.x) >= abs(b.y) ) {
    e = b.y / b.x;
    f = b.x + b.y * e;
    h = e;
  } else {
    e = b.x / b.y;
    f = b.x * e + b.y;
    g = e;
  }

  return (a * g + h * vec2(a.y, -a.x)) / f;
} 


vec2 cmul (vec2 a, vec2 b) {
  return vec2(
    a.x * b.x - a.y * b.y,
    a.y * b.x + a.x * b.y
  );
}

vec2 cmul (vec2 a, vec2 b, vec2 c) {
  return cmul(cmul(a, b), c);
}

vec2 cmul (vec2 a, vec2 b, vec2 c, vec2 d) {
  return cmul(cmul(a, b), cmul(c, d));
}

vec2 cmul (vec2 a, vec2 b, vec2 c, vec2 d, vec2 e) {
  return cmul(cmul(a, b, c), cmul(d, e));
}

vec2 cmul (vec2 a, vec2 b, vec2 c, vec2 d, vec2 e, vec2 f) {
  return cmul(cmul(a, b, c), cmul(d, e, f));
} 

vec2 cpolar (vec2 z) {
  return vec2(
    atan(z.y, z.x),
    hypot(z)
  );
} 

vec2 cpow (vec2 a, vec2 b) {
  float aarg = atan(a.y, a.x);
  float amod = hypot(a);

  float theta = log(amod) * b.y + aarg * b.x;

  return vec2(
    cos(theta),
    sin(theta)
  ) * pow(amod, b.x) * exp(-aarg * b.y);
} 




vec2 csec (vec2 z) {
  float d = 0.25 * (exp(2.0 * z.y) + exp(-2.0 * z.y)) + 0.5 * cos(2.0 * z.x);
  return sinhcosh(z.y).yx * vec2(cos(z.x), sin(z.x)) / d;
} 

vec2 csech(vec2 z) {
  float d = cos(2.0 * z.y) + 0.5 * (exp(2.0 * z.x) + exp(-2.0 * z.x));
  vec2 sch = sinhcosh(z.x);

  return vec2(cos(z.y), -sin(z.y)) * sch.yx / (0.5 * d);
} 


vec4 csincos (vec2 z) {
  float c = cos(z.x);
  float s = sin(z.x);
  return sinhcosh(z.y).yxyx * vec4(s, c, c, -s);
} 

vec2 csinh (vec2 z) {
  return sinhcosh(z.x) * vec2(cos(z.y), sin(z.y));
} 



vec2 ctan (vec2 z) {
  vec2 e2iz = cexp(2.0 * vec2(-z.y, z.x));

  return cdiv(
    e2iz - vec2(1, 0),
    vec2(-e2iz.y, 1.0 + e2iz.x)
  );
} 

vec2 ctanh (vec2 z) {
  z *= 2.0;
  vec2 sch = sinhcosh(z.x);
  return vec2(sch.x, sin(z.y)) / (sch.y + cos(z.y));
}

vec2 cpolar( float k , float t ){  return k*vec2(cos(t),sin(t));}


vec4 vec2_4(vec2 v2) {
  return vec4(v2, 0, 1);
}



struct functions_list {
    int none;
    int csqr;
    int csqrt;
    int cexp;
    int clog;
    int cinv;
    int cabs2;
    int cconj;
    int csin;
    int ccos;
    int ctan;
    int ccot;
    int csinh;
    int ccosh;
    int ctanh;
    int ccoth;
    int casin;
    int cacos;
    int catan;
    int cacot;
    int casinh;
    int cacosh;
    int catanh;
    int cacoth;
    int cpolar;
    int cpow;
    int cconst;
};

const functions_list functions = functions_list(
    0, 
    1, 2, 3, 4, 5, 6, 7, 
    8, 9, 10, 11, 
    12, 13, 14, 15, 
    16, 17, 18, 19,
    20, 21, 22, 23, 24, 
    25, 26
);

vec2 callback(int func, vec2 Z, float pow, vec2 c) {
  if (func == functions.none)
    return Z;
  else if (func == functions.csqr)
    return csqr(Z);
  else if (func == functions.csqrt)
    return csqrt(Z);
  else if (func == functions.cexp)
    return cexp(Z);
  else if (func == functions.clog)
    return clogn(Z,pow);
  else if (func == functions.cinv)
    return cinv(Z);
  else if (func == functions.cabs2)
    return cabs2(Z);
  else if (func == functions.cconj)
    return cconj(Z);
  else if (func == functions.csin)
    return csin(Z);
  else if (func == functions.ccos)
    return ccos(Z);
  else if (func == functions.ctan)
    return ctan(Z);
  else if (func == functions.ccot)
    return ccot(Z);
  else if (func == functions.csinh)
    return csinh(Z);
  else if (func == functions.ccosh)
    return ccosh(Z);
  else if (func == functions.ctanh)
    return ctanh(Z);
  else if (func == functions.ccoth)
    return ccoth(Z);
  else if (func == functions.casin)
    return casin(Z);
  else if (func == functions.cacos)
    return cacos(Z);
  else if (func == functions.catan)
    return catan(Z);
  else if (func == functions.cacot)
    return cacot(Z);
  else if (func == functions.casinh)
    return casinh(Z);
  else if (func == functions.cacosh)
    return cacosh(Z);
  else if (func == functions.catanh)
    return catanh(Z);
  else if (func == functions.cacoth)
    return cacoth(Z);
  else if (func == functions.cpolar)
    return cpolar(Z);
  else if (func == functions.cpow)
  	return cpow(Z, pow);
  else if (func == functions.cconst)
  	return cconst(c);
  else
    return Z;
}