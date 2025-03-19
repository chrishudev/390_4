void foo(int x, int x) {}

void bar(int x) {
  int x = 0;
}

void baz() {
  int x = 0;
  int x = 1;
}

void qux() {
  int x = 0;
  if (x == 0) {
    int y = 1;
    {
      int x = 2;
      int y = 3;
    }
  }
}

void fie() {
  for (int i = 0; i < 10; ++i) {}
  for (int i = 0; i < 10; ++i) {} // no clash
  { int i = 0; } // no clash
  { int i = 0; } // no clash
}

void hie() {
  i = 3;
  int i = 4;
  if (true) {
    int j = 5;
  }
  j = 6;
}
