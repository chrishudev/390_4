void main(string[] args) {
  main(3);
  main(args, args);
  new foo(3);
  new foo(null);
  new foo(true, false);
  new foo[] { 3 };
}

struct foo {
  boolean b;
};
