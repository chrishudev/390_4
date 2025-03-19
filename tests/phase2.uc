void main(string[] args) {
  new int[] {};
  new foo[] {};
}

foo foo() {
  return new foo();
}

struct foo {
  double f;
  foo g;
};
