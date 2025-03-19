void main(string[] args) {
  {
    string[] z = args;
    println("" + z.length);
  }
  {
    foo z = new foo(3, "hello");
    println(z.length);
    z.length = "world";
    println(z.length);
  }
}

void bar(foo f) {
}

struct foo {
  int x;
  string length;
};
