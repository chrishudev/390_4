/*
Test with error type check inputs.
*/

void main(string[] args) {
    true || false;
    1 || 2;
    "true" && "false";
    1 < 2;
    "cat" > "dog";
    true < false;
    "cat" <= 2;
    dog => 3;
    2 == 3.1;
    "cat" != "dog;
}