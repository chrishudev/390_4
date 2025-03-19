void main(string[] args) {
  foo f = new foo();
  bar b = new bar();
  baz z = new baz();
  println(int_to_string(f.x));
  println(boolean_to_string(b.f == null));
  println(boolean_to_string(b.a == null));
}

struct foo {
  int x;
};

struct bar {
  foo f;
  int x;
  string[] a;
};

struct baz {};
